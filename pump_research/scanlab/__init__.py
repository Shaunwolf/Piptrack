"""
Scan Lab: a drag-and-drop stock scanner built from configurable indicator blocks.

    from pump_research.scanlab import catalog, evaluate, run_scan, PRESETS, expand_universe
"""

from . import blocks_indicators, blocks_levels, blocks_patterns, blocks_squeeze  # noqa: F401  (registers every block)
from .engine import BLOCKS, FAMILIES, ScanContext, catalog, evaluate, normalize_spec
from .presets import PRESETS, preset
from .runner import load_prices, run_scan
from .universe import LISTS, SECTORS, expand_universe

__all__ = ["BLOCKS", "FAMILIES", "ScanContext", "catalog", "evaluate", "normalize_spec", "PRESETS", "preset",
           "load_prices", "run_scan", "LISTS", "SECTORS", "expand_universe"]
