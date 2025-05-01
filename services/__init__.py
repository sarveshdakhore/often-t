# This file marks the 'services' directory as a Python package.

# Import functions directly for easier access
from . import itinerary_service
from . import recommender # Keep old one for reference or potential fallback

__all__ = [
    "itinerary_service",
    "recommender", # Old template recommender
]
