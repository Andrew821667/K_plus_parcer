"""
K_plus_parcer - 0@A5@  87 >=AC;LB0=B;NA

$>:CA =0 ML/RAG: Markdown 1070 7=0=89 8 40B0A5BK 4;O >1CG5=8O

A=>2=>5 8A?>;L7>20=85:
    from k_plus_parcer import NPAParser

    parser = NPAParser()
    document = parser.parse('path/to/npa.pdf')

    # -:A?>@B 2 Markdown (  ""!)
    document.export_markdown('output/npa.md')

    # -:A?>@B 2 JSON
    document.export_json('output/npa.json')
"""

from .parser import NPAParser
from .models.document import NPADocument
from .models.metadata import DocumentMetadata
from .models.article import Article, ArticlePart, Chapter

__version__ = "0.1.0"
__all__ = [
    "NPAParser",
    "NPADocument",
    "DocumentMetadata",
    "Article",
    "ArticlePart",
    "Chapter",
]
