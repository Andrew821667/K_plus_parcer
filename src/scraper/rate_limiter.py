"""
Rate Limiter для защиты от блокировок (Token Bucket алгоритм)

Адаптировано из kad_parcer проекта
"""

import time
import asyncio
from threading import Lock
from typing import Optional


class TokenBucketRateLimiter:
    """
    Token Bucket алгоритм для ограничения частоты запросов

    Принцип работы:
    - "Ведро" содержит токены
    - Каждый запрос забирает 1 токен
    - Токены пополняются с заданной частотой
    - Если токенов нет - запрос ждет

    Это защищает от блокировки сайтом за слишком частые запросы.
    """

    def __init__(
        self,
        rate: float = 1.0,
        burst_size: int = 5,
        rate_limit_seconds: float = 1.0
    ):
        """
        Инициализация rate limiter

        Args:
            rate: Скорость пополнения токенов (токенов в секунду)
            burst_size: Максимальное количество токенов (для всплесков активности)
            rate_limit_seconds: Минимальное время между запросами
        """
        self.rate = rate
        self.burst_size = burst_size
        self.rate_limit_seconds = rate_limit_seconds

        self.tokens = float(burst_size)
        self.last_update = time.time()

        # Для синхронизации
        self._lock = asyncio.Lock()
        self._sync_lock = Lock()

    def _refill_tokens(self):
        """Пополнение токенов на основе прошедшего времени"""
        now = time.time()
        elapsed = now - self.last_update

        # Добавляем токены пропорционально времени
        new_tokens = elapsed * self.rate
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_update = now

    async def acquire(self):
        """
        Асинхронный захват разрешения на запрос

        Использование:
            await rate_limiter.acquire()
            # Теперь можно делать запрос
        """
        async with self._lock:
            self._refill_tokens()

            # Если токенов мало - ждем
            while self.tokens < 1:
                # Вычисляем сколько нужно ждать
                sleep_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(sleep_time)
                self._refill_tokens()

            # Забираем токен
            self.tokens -= 1

            # Минимальная задержка между запросами
            if self.rate_limit_seconds > 0:
                await asyncio.sleep(self.rate_limit_seconds)

    def acquire_sync(self):
        """
        Синхронный захват разрешения на запрос

        Использование:
            rate_limiter.acquire_sync()
            # Теперь можно делать запрос
        """
        with self._sync_lock:
            self._refill_tokens()

            # Если токенов мало - ждем
            while self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                time.sleep(sleep_time)
                self._refill_tokens()

            # Забираем токен
            self.tokens -= 1

            # Минимальная задержка
            if self.rate_limit_seconds > 0:
                time.sleep(self.rate_limit_seconds)


# Глобальный экземпляр rate limiter
_global_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_rate_limiter(
    rate: float = 0.5,  # 0.5 запросов в секунду = 1 запрос каждые 2 секунды
    burst_size: int = 3,  # Максимум 3 быстрых запроса подряд
    rate_limit_seconds: float = 2.0  # Минимум 2 секунды между запросами
) -> TokenBucketRateLimiter:
    """
    Получение глобального rate limiter

    Гарантирует что весь код использует один и тот же limiter.
    Это важно для корректного подсчета запросов.

    Args:
        rate: Скорость пополнения (по умолчанию: 0.5 req/sec)
        burst_size: Размер всплеска (по умолчанию: 3)
        rate_limit_seconds: Минимальная задержка (по умолчанию: 2 сек)

    Returns:
        TokenBucketRateLimiter: Глобальный экземпляр
    """
    global _global_rate_limiter

    if _global_rate_limiter is None:
        _global_rate_limiter = TokenBucketRateLimiter(
            rate=rate,
            burst_size=burst_size,
            rate_limit_seconds=rate_limit_seconds
        )

    return _global_rate_limiter


def reset_rate_limiter():
    """Сброс глобального rate limiter (для тестов)"""
    global _global_rate_limiter
    _global_rate_limiter = None
