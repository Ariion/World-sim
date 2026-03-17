"""
GENESIS ENGINE — api/routes_world.py
Endpoints REST pour l'état du monde.
"""
from fastapi import APIRouter
from ..simulation.world import world_state

router = APIRouter(prefix="/world", tags=["world"])


@router.get("/state")
async def get_world_state():
    """Snapshot complet du monde (pour reconnexion client)."""
    return world_state.to_snapshot()


@router.get("/map")
async def get_map():
    """Carte complète (appelée une seule fois au chargement client)."""
    return world_state.map_to_dict()


@router.get("/tribes")
async def get_tribes():
    return {"tribes": [t.to_dict() for t in world_state.tribes]}


@router.get("/tribes/{tribe_id}")
async def get_tribe(tribe_id: int):
    tribe = next((t for t in world_state.tribes if t.id == tribe_id), None)
    if not tribe:
        return {"error": "Tribu introuvable"}
    return tribe.to_dict()


@router.get("/events")
async def get_events(limit: int = 50):
    return {"events": world_state.event_log[:limit]}


@router.get("/time")
async def get_time():
    return world_state.time.to_dict()
