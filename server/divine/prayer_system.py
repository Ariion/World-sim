"""
GENESIS ENGINE — divine/prayer_system.py
Helpers pour le système de prières. Logique complémentaire à world.py.
"""
from ..simulation.world import world_state


def get_inbox(limit: int = 20) -> list[dict]:
    """Retourne les prières non répondues en priorité."""
    unanswered = [p for p in world_state.prayers if not p["answered"]]
    answered   = [p for p in world_state.prayers if  p["answered"]]
    return (unanswered + answered)[:limit]


def get_unanswered_count() -> int:
    return sum(1 for p in world_state.prayers if not p["answered"])
