"""Configuration and chart styling defaults for ChartMind."""

from __future__ import annotations

SUPPORTED_CHART_TYPES = ["bar", "line", "scatter", "pie", "histogram", "heatmap"]

CHART_STYLE_DEFAULTS: dict[str, object] = {
    "color": "#4C72B0",
    "title_fontsize": 14,
    "label_fontsize": 11,
    "dpi": 150,
    "bins": 20,
    "cmap": "coolwarm",
    "figsize": (10, 6),
}

COLOR_PALETTES: dict[str, list[str]] = {
    "vibrant": [
        "#4C72B0", "#DD8452", "#55A868", "#C44E52",
        "#8172B3", "#937860", "#DA8BC3", "#8C8C8C",
    ],
    "pastel": [
        "#AEC7E8", "#FFBB78", "#98DF8A", "#FF9896",
        "#C5B0D5", "#C49C94", "#F7B6D2", "#DBDB8D",
    ],
    "monochrome": [
        "#2C3E50", "#34495E", "#5D6D7E", "#85929E",
        "#ABB2B9", "#CCD1D1", "#E5E8E8", "#F2F3F4",
    ],
}
