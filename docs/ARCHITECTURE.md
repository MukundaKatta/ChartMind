# ChartMind Architecture

## Overview

ChartMind converts natural language queries into chart visualizations. It uses keyword matching and pattern rules (no ML dependencies) to interpret user intent and generates charts via matplotlib.

## Components

```
src/chartmind/
  __init__.py      -- Package exports
  core.py          -- Main engine (QueryParser, ChartGenerator, DataLoader, ChartRenderer)
  config.py        -- Chart styling defaults and supported chart types
  utils.py         -- Query tokenization, column extraction, filter parsing, data type detection
  __main__.py      -- CLI entry point (typer-based)
```

## Data Flow

```
User Query (text)
    |
    v
QueryParser
    |-- detect chart type (keyword matching)
    |-- detect aggregation (sum/mean/count/min/max)
    |-- extract x/y columns (fuzzy match against DataFrame columns)
    |-- parse filter clauses ("where region equals US")
    |
    v
ChartConfig (dataclass)
    |
    v
ChartRenderer
    |-- apply filters to DataFrame
    |-- aggregate data if needed
    |-- dispatch to chart-type-specific renderer
    |-- save to PNG/SVG via matplotlib
    |
    v
Output Image
```

## Supported Chart Types

| Type      | Trigger Keywords                        |
|-----------|-----------------------------------------|
| bar       | bar, compare, column chart              |
| line      | line, trend, over time, timeline        |
| scatter   | scatter, correlation, relationship, xy  |
| pie       | pie, proportion, share, breakdown       |
| histogram | histogram, distribution, frequency      |
| heatmap   | heatmap, heat map, matrix, density      |

## Design Decisions

1. **No ML dependency** -- Chart type detection uses keyword/pattern matching. This keeps the package lightweight and deterministic.
2. **matplotlib backend** -- Chosen for broad compatibility and high-quality static output (PNG, SVG, PDF).
3. **Pandas for data** -- DataFrames are the universal interchange format for tabular data in Python.
4. **Facade pattern** -- `ChartGenerator` wraps the parser, loader, and renderer for a simple one-call API.
