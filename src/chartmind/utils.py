"""Query parsing helpers, data type detection, and text utilities for ChartMind."""

from __future__ import annotations

import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset({
    "show", "me", "plot", "draw", "chart", "graph", "create", "make",
    "generate", "display", "visualize", "the", "a", "an", "of", "in",
    "for", "with", "and", "or", "to", "from", "as", "is", "are",
    "using", "use", "please", "can", "you", "i", "want", "would", "like",
})


def tokenize_query(query: str) -> list[str]:
    """Lowercase, remove punctuation, split into tokens."""
    cleaned = re.sub(r"[^\w\s]", " ", query.lower())
    return [t for t in cleaned.split() if t]


def remove_stop_words(tokens: list[str]) -> list[str]:
    """Filter out common stop words from a token list."""
    return [t for t in tokens if t not in STOP_WORDS]


# ---------------------------------------------------------------------------
# Chart type matching
# ---------------------------------------------------------------------------

def match_chart_type(query: str, patterns: dict[str, list[str]]) -> str:
    """Return the best-matching chart type from keyword patterns.

    Tries longer patterns first so "bar chart" beats "bar".
    Falls back to "bar" if nothing matches.
    """
    best_type = "bar"
    best_len = 0
    for chart_type, keywords in patterns.items():
        sorted_kw = sorted(keywords, key=len, reverse=True)
        for kw in sorted_kw:
            if kw in query and len(kw) > best_len:
                best_type = chart_type
                best_len = len(kw)
    return best_type


# ---------------------------------------------------------------------------
# Aggregation detection
# ---------------------------------------------------------------------------

def parse_aggregation(
    query: str, patterns: dict[str, list[str]]
) -> Optional[str]:
    """Detect aggregation function from the query text."""
    for agg_name, keywords in patterns.items():
        sorted_kw = sorted(keywords, key=len, reverse=True)
        for kw in sorted_kw:
            if kw in query:
                return agg_name
    return None


# ---------------------------------------------------------------------------
# Column extraction
# ---------------------------------------------------------------------------

def extract_columns_from_query(query: str, columns: list[str]) -> list[str]:
    """Find column names mentioned in the query, case-insensitive.

    Checks both the raw column name and underscore-to-space variants.
    Returns columns in the order they appear in the query.
    """
    found: list[tuple[int, str]] = []
    query_lower = query.lower()
    for col in columns:
        col_lower = col.lower()
        col_spaced = col_lower.replace("_", " ")
        pos = query_lower.find(col_lower)
        if pos == -1:
            pos = query_lower.find(col_spaced)
        if pos >= 0:
            found.append((pos, col))
    found.sort(key=lambda x: x[0])
    return [col for _, col in found]


# ---------------------------------------------------------------------------
# Filter clause parsing
# ---------------------------------------------------------------------------

_FILTER_OPS = {
    "greater than": ">",
    "more than": ">",
    "above": ">",
    "less than": "<",
    "below": "<",
    "under": "<",
    "equal to": "==",
    "equals": "==",
    "not equal to": "!=",
    "at least": ">=",
    "at most": "<=",
}


def parse_filter_clauses(
    query: str, columns: list[str]
) -> list[dict[str, Any]]:
    """Extract simple filter conditions like 'where region equals US'.

    Returns a list of dicts: [{"column": ..., "op": ..., "value": ...}].
    """
    filters: list[dict[str, Any]] = []
    where_match = re.search(r"\b(?:where|filter|when|if)\b\s+(.+)", query)
    if not where_match:
        return filters

    clause = where_match.group(1)

    for col in columns:
        col_lower = col.lower()
        col_spaced = col_lower.replace("_", " ")
        for variant in (col_lower, col_spaced):
            if variant not in clause:
                continue
            remainder = clause.split(variant, 1)[1].strip()
            for text_op, symbol in sorted(_FILTER_OPS.items(), key=lambda x: -len(x[0])):
                if remainder.startswith(text_op):
                    value_str = remainder[len(text_op):].strip().split()[0] if remainder[len(text_op):].strip() else ""
                    if value_str:
                        filters.append({"column": col, "op": symbol, "value": _coerce(value_str)})
                    break
            else:
                # Try pattern: column = value or column > value
                op_match = re.match(r"(==|!=|>=|<=|>|<|=)\s*(\S+)", remainder)
                if op_match:
                    op = "==" if op_match.group(1) == "=" else op_match.group(1)
                    filters.append({"column": col, "op": op, "value": _coerce(op_match.group(2))})
    return filters


def _coerce(value: str) -> Any:
    """Try to coerce a string to int or float, else return as-is."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value.strip("'\"")


# ---------------------------------------------------------------------------
# Data type detection
# ---------------------------------------------------------------------------

def detect_column_type(series: Any) -> str:
    """Detect whether a pandas Series is numeric, datetime, or categorical."""
    import pandas as pd

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "categorical"


def suggest_chart_type_from_data(
    x_type: str, y_type: str
) -> str:
    """Suggest a chart type based on column data types."""
    if x_type == "categorical" and y_type == "numeric":
        return "bar"
    if x_type == "datetime" and y_type == "numeric":
        return "line"
    if x_type == "numeric" and y_type == "numeric":
        return "scatter"
    if x_type == "categorical" and y_type == "categorical":
        return "heatmap"
    return "bar"
