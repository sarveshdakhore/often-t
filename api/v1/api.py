from fastapi import APIRouter

# Import ALL endpoint routers
from .endpoints import recommendations, catalogue_routes, itineraries, template_routes

# This is the router imported in main.py via __init__.py
api_router = APIRouter()

# Include template router first to prioritize template-based operations
api_router.include_router(template_routes.router, tags=["Templates"])   # Prioritize templates first

# Include other routers
api_router.include_router(itineraries.router, prefix="/itineraries", tags=["Itineraries"])
api_router.include_router(recommendations.router, prefix="/recommended-itineraries", tags=["Recommendations"])
api_router.include_router(catalogue_routes.router, tags=["Catalogue"])  # Already has /catalogue prefix internally

