"""
GENESIS ENGINE — api/routes_warfare.py
Endpoints pour consulter l'état des guerres.
Nouveau fichier V2.
"""
from fastapi import APIRouter
from ..simulation.ecs.systems_warfare import get_wars_state, war_history, active_wars

router = APIRouter(prefix="/warfare", tags=["warfare"])


@router.get("/state")
async def get_warfare_state():
    """État complet des guerres actives et historique."""
    return get_wars_state()


@router.get("/active")
async def get_active_wars():
    return {
        "active": [
            {
                "attacker_id": w.attacker_id,
                "defender_id": w.defender_id,
                "reason":      w.reason,
                "intensity":   round(w.intensity, 2),
                "duration":    w.duration,
            }
            for w in active_wars if not w.resolved
        ],
        "count": sum(1 for w in active_wars if not w.resolved)
    }


@router.get("/history")
async def get_war_history(limit: int = 50):
    return {"wars": war_history[-limit:], "total": len(war_history)}
