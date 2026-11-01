"""
Collector package — every collector is one file, one class.
Re-exports the classes so callers can import from `collectors`.
"""

from collectors.remotive        import RemotiveCollector
from collectors.arbeitnow       import ArbeitnowCollector
from collectors.himalayas       import HimalayasCollector
from collectors.hackernews      import HackerNewsCollector
from collectors.jobgether       import JobgetherCollector
from collectors.workingnomads   import WorkingNomadsCollector
from collectors.serper          import SerperCollector
from collectors.brightdata_maps import BrightDataMapsCollector

# Optional — uncomment when these collectors are implemented and tested:
# from collectors.wwr            import WWRCollector
# from collectors.crossover      import CrossoverCollector
# from collectors.turing         import TuringCollector

__all__ = [
    "RemotiveCollector",
    "ArbeitnowCollector",
    "HimalayasCollector",
    "HackerNewsCollector",
    "JobgetherCollector",
    "WorkingNomadsCollector",
    "SerperCollector",
    "BrightDataMapsCollector",
]