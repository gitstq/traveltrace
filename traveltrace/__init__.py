"""
TravelTrace - 旅行足迹智能可视化引擎
TravelTrace - Intelligent Travel Footprint Visualization Engine

A lightweight, privacy-first tool to parse, analyze and visualize your
location history from Google Takeout, GPX tracks and photo EXIF data.
"""

__version__ = "1.0.0"
__author__ = "TravelTrace Contributors"
__license__ = "MIT"

from .parser import LocationParser, TrackPoint
from .analyzer import TrackAnalyzer, StayPoint, TripSegment
from .exporter import Exporter

__all__ = [
    "LocationParser",
    "TrackPoint",
    "TrackAnalyzer",
    "StayPoint",
    "TripSegment",
    "Exporter",
    "__version__",
]
