"""
GENESIS ENGINE — divine/divine_energy.py
Helpers énergie divine.
"""
from ..simulation.world import world_state
from ..config import DIVINE_ENERGY_MAX


def get_energy() -> dict:
    return {
        "current": round(world_state.divine_energy, 2),
        "max":     DIVINE_ENERGY_MAX,
        "pct":     round(world_state.divine_energy / DIVINE_ENERGY_MAX * 100, 1),
    }
