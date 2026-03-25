"""Tests for ChartMind core functionality."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import pytest

from chartmind.core import ChartConfig, ChartGenerator, ChartRenderer, DataLoader, QueryParser


# ---------------------------------------------------------------------------
# QueryParser tests
# ---------------------------------------------------------------------------

class TestQueryParser:
    def setup_method(self) -> None:
        self.parser = QueryParser()

    def test_bar_chart_detection(self) -> None:
        config = self.parser.parse("show me revenue by month as a bar chart")
        assert config.chart_type == "bar"

    def test_line_chart_detection(self) -> None:
        config = self.parser.parse("show sales trend over time")
        assert config.chart_type == "line"

    def test_scatter_chart_detection(self) -> None:
        config = self.parser.parse("scatter plot of height vs weight")
        assert config.chart_type == "scatter"

    def test_pie_chart_detection(self) -> None:
        config = self.parser.parse("pie chart of market share by company")
        assert config.chart_type == "pie"

    def test_histogram_detection(self) -> None:
        config = self.parser.parse("show distribution of ages as histogram")
        assert config.chart_type == "histogram"

    def test_heatmap_detection(self) -> None:
        config = self.parser.parse("heatmap of correlations")
        assert config.chart_type == "heatmap"

    def test_column_extraction(self) -> None:
        columns = ["revenue", "month", "region"]
        config = self.parser.parse("show revenue by month", columns=columns)
        assert config.x_column == "month"
        assert config.y_column == "revenue"

    def test_aggregation_detection_sum(self) -> None:
        config = self.parser.parse("total revenue by month")
        assert config.aggregation == "sum"

    def test_aggregation_detection_average(self) -> None:
        config = self.parser.parse("average salary by department")
        assert config.aggregation == "mean"

    def test_aggregation_detection_count(self) -> None:
        config = self.parser.parse("count of orders by region")
        assert config.aggregation == "count"

    def test_default_chart_type(self) -> None:
        config = self.parser.parse("show me the numbers")
        assert config.chart_type == "bar"

    def test_title_generation(self) -> None:
        columns = ["revenue", "month"]
        config = self.parser.parse("total revenue by month", columns=columns)
        assert "Revenue" in config.title
        assert "Month" in config.title


# ---------------------------------------------------------------------------
# DataLoader tests
# ---------------------------------------------------------------------------

class TestDataLoader:
    def test_load_csv(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,value\nA,10\nB,20\nC,30\n")
        df = DataLoader.load(csv_file)
        assert len(df) == 3
        assert list(df.columns) == ["name", "value"]

    def test_load_json(self, tmp_path: Path) -> None:
        json_file = tmp_path / "data.json"
        json_file.write_text('[{"name": "A", "value": 10}, {"name": "B", "value": 20}]')
        df = DataLoader.load(json_file)
        assert len(df) == 2

    def test_load_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            DataLoader.load("/nonexistent/file.csv")

    def test_unsupported_format(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "data.xml"
        bad_file.write_text("<data/>")
        with pytest.raises(ValueError, match="Unsupported"):
            DataLoader.load(bad_file)


# ---------------------------------------------------------------------------
# ChartRenderer tests
# ---------------------------------------------------------------------------

class TestChartRenderer:
    def _sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "month": ["Jan", "Feb", "Mar", "Apr", "May"],
            "revenue": [100, 150, 130, 170, 200],
            "cost": [80, 90, 85, 100, 110],
        })

    def test_render_bar(self, tmp_path: Path) -> None:
        renderer = ChartRenderer()
        cfg = ChartConfig(chart_type="bar", x_column="month", y_column="revenue", title="Test Bar")
        out = renderer.render(cfg, self._sample_df(), output=tmp_path / "bar.png")
        assert out.exists()

    def test_render_line(self, tmp_path: Path) -> None:
        renderer = ChartRenderer()
        cfg = ChartConfig(chart_type="line", x_column="month", y_column="revenue", title="Test Line")
        out = renderer.render(cfg, self._sample_df(), output=tmp_path / "line.png")
        assert out.exists()

    def test_render_pie(self, tmp_path: Path) -> None:
        renderer = ChartRenderer()
        cfg = ChartConfig(chart_type="pie", x_column="month", y_column="revenue", title="Test Pie")
        out = renderer.render(cfg, self._sample_df(), output=tmp_path / "pie.png")
        assert out.exists()

    def test_render_scatter(self, tmp_path: Path) -> None:
        renderer = ChartRenderer()
        df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})
        cfg = ChartConfig(chart_type="scatter", x_column="x", y_column="y", title="Test Scatter")
        out = renderer.render(cfg, df, output=tmp_path / "scatter.png")
        assert out.exists()

    def test_render_histogram(self, tmp_path: Path) -> None:
        renderer = ChartRenderer()
        df = pd.DataFrame({"age": [22, 25, 27, 30, 35, 40, 42, 28, 33, 38]})
        cfg = ChartConfig(chart_type="histogram", x_column="age", y_column="age", title="Age Dist")
        out = renderer.render(cfg, df, output=tmp_path / "hist.png")
        assert out.exists()


# ---------------------------------------------------------------------------
# ChartGenerator integration test
# ---------------------------------------------------------------------------

class TestChartGenerator:
    def test_end_to_end(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "sales.csv"
        csv_file.write_text("month,revenue\nJan,100\nFeb,150\nMar,200\n")
        gen = ChartGenerator()
        config = gen.generate(
            query="show revenue by month as a bar chart",
            data=csv_file,
            output=tmp_path / "out.png",
        )
        assert config.chart_type == "bar"
        assert (tmp_path / "out.png").exists()

    def test_generate_config_only(self) -> None:
        gen = ChartGenerator()
        result = gen.generate_config(
            "average score by department",
            columns=["score", "department"],
        )
        assert result["chart_type"] == "bar"
        assert result["aggregation"] == "mean"
