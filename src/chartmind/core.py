"""Core engine for ChartMind -- query parsing, chart generation, data loading, rendering."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from chartmind.config import CHART_STYLE_DEFAULTS, SUPPORTED_CHART_TYPES
from chartmind.utils import (
    detect_column_type,
    extract_columns_from_query,
    match_chart_type,
    parse_aggregation,
    parse_filter_clauses,
    tokenize_query,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ChartConfig:
    """Describes everything needed to render a chart."""

    chart_type: str = "bar"
    title: str = ""
    x_column: str = ""
    y_column: str = ""
    aggregation: Optional[str] = None  # sum, mean, count, min, max
    filters: list[dict[str, Any]] = field(default_factory=list)
    style: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "x_column": self.x_column,
            "y_column": self.y_column,
            "aggregation": self.aggregation,
            "filters": self.filters,
            "style": self.style,
        }


# ---------------------------------------------------------------------------
# QueryParser
# ---------------------------------------------------------------------------

class QueryParser:
    """Extract chart type, columns, aggregations, and filters from natural language."""

    CHART_TYPE_PATTERNS: dict[str, list[str]] = {
        "bar": ["bar", "bar chart", "bar graph", "column chart", "compare"],
        "line": ["line", "line chart", "trend", "over time", "timeline", "time series"],
        "scatter": ["scatter", "scatter plot", "correlation", "relationship", "xy"],
        "pie": ["pie", "pie chart", "proportion", "share", "breakdown", "composition"],
        "histogram": ["histogram", "distribution", "frequency"],
        "heatmap": ["heatmap", "heat map", "matrix", "density"],
    }

    AGGREGATION_PATTERNS: dict[str, list[str]] = {
        "sum": ["total", "sum", "sum of", "total of"],
        "mean": ["average", "mean", "avg"],
        "count": ["count", "number of", "how many"],
        "min": ["minimum", "min", "lowest", "smallest"],
        "max": ["maximum", "max", "highest", "largest", "top"],
    }

    def parse(self, query: str, columns: list[str] | None = None) -> ChartConfig:
        """Parse a natural language query into a ChartConfig."""
        query_lower = query.lower().strip()
        tokens = tokenize_query(query_lower)

        chart_type = self._detect_chart_type(query_lower)
        aggregation = self._detect_aggregation(query_lower)
        x_col, y_col = self._detect_columns(query_lower, tokens, columns)
        filters = parse_filter_clauses(query_lower, columns or [])
        title = self._build_title(chart_type, x_col, y_col, aggregation)

        return ChartConfig(
            chart_type=chart_type,
            title=title,
            x_column=x_col,
            y_column=y_col,
            aggregation=aggregation,
            filters=filters,
        )

    def _detect_chart_type(self, query: str) -> str:
        return match_chart_type(query, self.CHART_TYPE_PATTERNS)

    def _detect_aggregation(self, query: str) -> Optional[str]:
        return parse_aggregation(query, self.AGGREGATION_PATTERNS)

    def _detect_columns(
        self, query: str, tokens: list[str], columns: list[str] | None
    ) -> tuple[str, str]:
        if columns:
            found = extract_columns_from_query(query, columns)
            if len(found) >= 2:
                return found[0], found[1]
            if len(found) == 1:
                return found[0], ""
        # Fallback: use "by <word>" pattern
        by_match = re.search(r"\bby\s+(\w+)", query)
        x_col = by_match.group(1) if by_match else ""
        # Look for the first noun-like token before "by" as y
        y_col = ""
        if by_match:
            before_by = query[: by_match.start()].strip().split()
            for w in reversed(before_by):
                if w not in {"show", "me", "plot", "draw", "chart", "graph",
                             "the", "a", "an", "of", "as", "in", "total",
                             "average", "sum", "count", "min", "max"}:
                    y_col = w
                    break
        return x_col, y_col

    @staticmethod
    def _build_title(chart_type: str, x: str, y: str, agg: Optional[str]) -> str:
        parts: list[str] = []
        if agg:
            parts.append(agg.capitalize())
        if y:
            parts.append(y.replace("_", " ").title())
        if x:
            parts.append(f"by {x.replace('_', ' ').title()}")
        title = " ".join(parts) if parts else f"{chart_type.title()} Chart"
        return title


# ---------------------------------------------------------------------------
# DataLoader
# ---------------------------------------------------------------------------

class DataLoader:
    """Load CSV or JSON files into a pandas DataFrame."""

    @staticmethod
    def load(path: str | Path) -> pd.DataFrame:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")
        ext = path.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path)
        if ext == ".json":
            return pd.read_json(path)
        raise ValueError(f"Unsupported file format: {ext}. Use .csv or .json")

    @staticmethod
    def from_dict(data: dict[str, list[Any]]) -> pd.DataFrame:
        return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# ChartRenderer
# ---------------------------------------------------------------------------

class ChartRenderer:
    """Render a ChartConfig + DataFrame to an image file using matplotlib."""

    def render(
        self,
        config: ChartConfig,
        df: pd.DataFrame,
        output: str | Path = "chart.png",
        figsize: tuple[int, int] = (10, 6),
    ) -> Path:
        output = Path(output)
        fig, ax = plt.subplots(figsize=figsize)
        style = {**CHART_STYLE_DEFAULTS, **config.style}

        # Apply filters
        filtered = self._apply_filters(df, config.filters)

        # Aggregate if needed
        plot_df = self._aggregate(filtered, config)

        renderer_map = {
            "bar": self._render_bar,
            "line": self._render_line,
            "scatter": self._render_scatter,
            "pie": self._render_pie,
            "histogram": self._render_histogram,
            "heatmap": self._render_heatmap,
        }

        render_fn = renderer_map.get(config.chart_type, self._render_bar)
        render_fn(ax, plot_df, config, style)

        ax.set_title(config.title, fontsize=style.get("title_fontsize", 14), pad=12)
        fig.tight_layout()
        fig.savefig(str(output), dpi=style.get("dpi", 150), bbox_inches="tight")
        plt.close(fig)
        return output

    # -- individual renderers ------------------------------------------------

    @staticmethod
    def _render_bar(ax: plt.Axes, df: pd.DataFrame, cfg: ChartConfig, style: dict) -> None:
        x = df[cfg.x_column] if cfg.x_column and cfg.x_column in df.columns else df.index
        y = df[cfg.y_column] if cfg.y_column and cfg.y_column in df.columns else df.iloc[:, -1]
        ax.bar(x.astype(str), y, color=style.get("color", "#4C72B0"), edgecolor="white")
        ax.set_xlabel(cfg.x_column.replace("_", " ").title())
        ax.set_ylabel(cfg.y_column.replace("_", " ").title())

    @staticmethod
    def _render_line(ax: plt.Axes, df: pd.DataFrame, cfg: ChartConfig, style: dict) -> None:
        x = df[cfg.x_column] if cfg.x_column and cfg.x_column in df.columns else df.index
        y = df[cfg.y_column] if cfg.y_column and cfg.y_column in df.columns else df.iloc[:, -1]
        ax.plot(x, y, marker="o", color=style.get("color", "#4C72B0"), linewidth=2)
        ax.set_xlabel(cfg.x_column.replace("_", " ").title())
        ax.set_ylabel(cfg.y_column.replace("_", " ").title())
        ax.grid(True, alpha=0.3)

    @staticmethod
    def _render_scatter(ax: plt.Axes, df: pd.DataFrame, cfg: ChartConfig, style: dict) -> None:
        x = df[cfg.x_column] if cfg.x_column and cfg.x_column in df.columns else df.iloc[:, 0]
        y = df[cfg.y_column] if cfg.y_column and cfg.y_column in df.columns else df.iloc[:, 1]
        ax.scatter(x, y, color=style.get("color", "#4C72B0"), alpha=0.7, edgecolors="white")
        ax.set_xlabel(cfg.x_column.replace("_", " ").title())
        ax.set_ylabel(cfg.y_column.replace("_", " ").title())

    @staticmethod
    def _render_pie(ax: plt.Axes, df: pd.DataFrame, cfg: ChartConfig, style: dict) -> None:
        labels = df[cfg.x_column] if cfg.x_column and cfg.x_column in df.columns else df.index
        values = df[cfg.y_column] if cfg.y_column and cfg.y_column in df.columns else df.iloc[:, -1]
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")

    @staticmethod
    def _render_histogram(ax: plt.Axes, df: pd.DataFrame, cfg: ChartConfig, style: dict) -> None:
        col = cfg.y_column or cfg.x_column
        data = df[col] if col and col in df.columns else df.iloc[:, 0]
        ax.hist(data, bins=style.get("bins", 20), color=style.get("color", "#4C72B0"),
                edgecolor="white", alpha=0.8)
        ax.set_xlabel(col.replace("_", " ").title() if col else "Value")
        ax.set_ylabel("Frequency")

    @staticmethod
    def _render_heatmap(ax: plt.Axes, df: pd.DataFrame, cfg: ChartConfig, style: dict) -> None:
        numeric_df = df.select_dtypes(include="number")
        corr = numeric_df.corr()
        im = ax.imshow(corr.values, cmap=style.get("cmap", "coolwarm"), aspect="auto")
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr.columns)
        plt.colorbar(im, ax=ax)

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _apply_filters(df: pd.DataFrame, filters: list[dict[str, Any]]) -> pd.DataFrame:
        result = df.copy()
        for f in filters:
            col = f.get("column", "")
            op = f.get("op", "==")
            val = f.get("value")
            if col not in result.columns or val is None:
                continue
            if op == "==":
                result = result[result[col] == val]
            elif op == "!=":
                result = result[result[col] != val]
            elif op == ">":
                result = result[result[col] > float(val)]
            elif op == "<":
                result = result[result[col] < float(val)]
            elif op == ">=":
                result = result[result[col] >= float(val)]
            elif op == "<=":
                result = result[result[col] <= float(val)]
        return result

    @staticmethod
    def _aggregate(df: pd.DataFrame, cfg: ChartConfig) -> pd.DataFrame:
        if not cfg.aggregation or not cfg.x_column or cfg.x_column not in df.columns:
            return df
        y_col = cfg.y_column if cfg.y_column and cfg.y_column in df.columns else None
        if y_col is None:
            return df
        grouped = df.groupby(cfg.x_column)[y_col]
        agg_map = {"sum": "sum", "mean": "mean", "count": "count", "min": "min", "max": "max"}
        agg_fn = agg_map.get(cfg.aggregation, "sum")
        result = grouped.agg(agg_fn).reset_index()
        return result


# ---------------------------------------------------------------------------
# ChartGenerator  (high-level facade)
# ---------------------------------------------------------------------------

class ChartGenerator:
    """Facade: parse query -> load data -> render chart."""

    def __init__(self) -> None:
        self.parser = QueryParser()
        self.loader = DataLoader()
        self.renderer = ChartRenderer()

    def generate(
        self,
        query: str,
        data: str | Path | pd.DataFrame | None = None,
        output: str | Path = "chart.png",
        columns: list[str] | None = None,
    ) -> ChartConfig:
        """Parse the query and optionally render the chart."""
        if isinstance(data, pd.DataFrame):
            df = data
        elif data is not None:
            df = self.loader.load(data)
        else:
            df = None

        cols = columns or (list(df.columns) if df is not None else None)
        config = self.parser.parse(query, cols)

        if df is not None:
            self.renderer.render(config, df, output=output)

        return config

    def generate_config(self, query: str, columns: list[str] | None = None) -> dict[str, Any]:
        """Return only the chart config dict without rendering."""
        config = self.parser.parse(query, columns)
        return config.to_dict()
