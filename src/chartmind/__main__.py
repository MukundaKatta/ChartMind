"""CLI entry point: python -m chartmind 'show revenue by month' --data sales.csv --output chart.png"""

from __future__ import annotations

import sys
from pathlib import Path

import typer

app = typer.Typer(help="ChartMind -- Natural language to chart generator.")


@app.command()
def main(
    query: str = typer.Argument(..., help="Natural language chart query"),
    data: str = typer.Option(..., "--data", "-d", help="Path to CSV or JSON data file"),
    output: str = typer.Option("chart.png", "--output", "-o", help="Output file path (PNG or SVG)"),
    width: int = typer.Option(10, "--width", "-w", help="Figure width in inches"),
    height: int = typer.Option(6, "--height", "-h", help="Figure height in inches"),
) -> None:
    """Parse a natural language query and generate a chart from your data."""
    from chartmind.core import ChartGenerator

    data_path = Path(data)
    if not data_path.exists():
        typer.echo(f"Error: data file not found: {data}", err=True)
        raise typer.Exit(code=1)

    generator = ChartGenerator()
    try:
        config = generator.generate(
            query=query,
            data=data_path,
            output=output,
        )
        typer.echo(f"Chart type : {config.chart_type}")
        typer.echo(f"Title      : {config.title}")
        typer.echo(f"X column   : {config.x_column}")
        typer.echo(f"Y column   : {config.y_column}")
        typer.echo(f"Aggregation: {config.aggregation or 'none'}")
        typer.echo(f"Saved to   : {output}")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
