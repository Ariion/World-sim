"""
GENESIS ENGINE — api/routes_divine.py
Endpoints REST pour les actions divines.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ..simulation.world import world_state
from ..divine.prayer_system import get_inbox, get_unanswered_count
from ..divine.divine_energy import get_energy

router = APIRouter(prefix="/divine", tags=["divine"])


class DivineActionRequest(BaseModel):
    action: str          # sign | dream | wrath | bless | miracle | prophet | disaster | ignore
    tribe_id: Optional[int] = None


class PrayerAnswerRequest(BaseModel):
    action: str


@router.get("/inbox")
async def get_divine_inbox(limit: int = 20):
    """Boîte divine : prières + stats."""
    return {
        "prayers":         get_inbox(limit),
        "unanswered":      get_unanswered_count(),
        "divine_energy":   get_energy(),
    }


@router.get("/energy")
async def get_divine_energy():
    return get_energy()


@router.post("/action")
async def divine_action(req: DivineActionRequest):
    """Effectue une action divine globale."""
    result = world_state.divine_action(req.action, req.tribe_id)
    return result


@router.post("/prayer/{prayer_id}/answer")
async def answer_prayer(prayer_id: int, req: PrayerAnswerRequest):
    """Répond à une prière spécifique."""
    result = world_state.answer_prayer(prayer_id, req.action)
    return result


@router.get("/prayers")
async def list_prayers(limit: int = 20, unanswered_only: bool = False):
    prayers = world_state.prayers
    if unanswered_only:
        prayers = [p for p in prayers if not p["answered"]]
    return {"prayers": prayers[:limit]}
