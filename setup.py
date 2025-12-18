"""
K_plus_parcer - Парсер НПА из КонсультантПлюс
Фокус на ML/RAG: Markdown база знаний и датасеты для обучения
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#') and not line.startswith('-')
        ]

setup(
    name="k_plus_parcer",
    version="0.1.0",
    author="Andrew821667",
    description="Парсер НПА из КонсультантПлюс для ML/RAG систем",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Andrew821667/K_plus_parcer",
    packages=['k_plus_parcer', 'k_plus_parcer.models', 'k_plus_parcer.extractors',
              'k_plus_parcer.parsers', 'k_plus_parcer.exporters', 'k_plus_parcer.utils'],
    package_dir={"k_plus_parcer": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "k-plus-parcer=k_plus_parcer.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
