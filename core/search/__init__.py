"""Search package — FTS index, query parser, SearchService."""
from core.search.fts_index import ensure_fts_table, index_note, index_extract, search, rebuild_index
from core.search.query_parser import build_fts_query

__all__ = [
    "ensure_fts_table",
    "index_note",
    "index_extract",
    "search",
    "rebuild_index",
    "build_fts_query",
]
