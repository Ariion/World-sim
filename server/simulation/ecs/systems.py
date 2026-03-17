"""
GENESIS ENGINE — ecs/systems.py
Systèmes ECS fondamentaux : nourriture, mort, reproduction, santé.
Chaque système est une fonction pure tribe × world → liste d'événements.
Interface stable — ne jamais modifier les signatures.
Pour ajouter un système → créer systems_v2.py et l'importer dans world.py
"""
import random
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..simulation.ecs.components import Tribe, Member
    from ..simulation.map_generator import Tile
    from ..simulation.time_system import WorldTime
    from ..server import config as cfg


def system_food(tribe, tiles, world_time, cfg) -> list[dict]:
    """
    Calcule production et consommation de nourriture.
    Retourne liste d'événements générés.
    """
    events = []
    S = cfg.MAP_SIZE
    idx = min(tribe.y, S-1) * S + min(tribe.x, S-1)
    tile = tiles[idx]

    hunters  = len(tribe.hunters())
    gatherers = len(tribe.gatherers())

    production = (
        hunters   * cfg.FOOD_PER_HUNT   * tile.huntable  * world_time.summer_bonus * world_time.winter_penalty
      + gatherers * cfg.FOOD_PER_GATHER * tile.fertility  * world_time.summer_bonus * world_time.winter_penalty
    )
    consumption = tribe.population() * cfg.FOOD_CONSUME_PER_DAY * cfg.DAYS_PER_TICK

    tribe.food = max(0.0, tribe.food + production - consumption)

    # Starvation
    if tribe.food < tribe.population() * 5:
        for m in tribe.members:
            m.vitals.health -= 0.015
            m.vitals.hunger  = min(1.0, m.vitals.hunger + 0.02)
        if random.random() < 0.05:
            events.append({
                "type":  "famine",
                "tribe": tribe.id,
                "text":  f"{tribe.name} souffre de la famine.",
                "color": "death",
            })

    return events


def system_aging_and_death(tribe, cfg) -> list[dict]:
    """
    Vieillit les membres et retire les morts.
    """
    events = []
    dead = []

    for m in tribe.members:
        m.vitals.age += cfg.DAYS_PER_TICK / 360.0

        # Mort naturelle (courbe de mortalité réaliste)
        death_prob = _mortality_rate(m.vitals.age, m.vitals.health)
        if random.random() < death_prob:
            dead.append(m)

    for m in dead:
        tribe.members.remove(m)
        tribe.memory.total_dead += 1
        tribe.faith = min(1.0, tribe.faith + 0.015)  # mort → foi

        if m.social.role == "chief":
            events.append({
                "type":  "death_chief",
                "tribe": tribe.id,
                "text":  f"Le chef de {tribe.name} est mort. La tribu cherche un successeur.",
                "color": "death",
            })
            _elect_chief(tribe)
        elif random.random() < 0.2:
            events.append({
                "type":  "death",
                "tribe": tribe.id,
                "text":  f"Un membre de {tribe.name} a péri ({m.social.role}, {int(m.vitals.age)} ans).",
                "color": "death",
            })

    return events


def system_reproduction(tribe, cfg) -> list[dict]:
    """
    Reproduction si conditions remplies.
    """
    events = []
    if tribe.population() >= cfg.MAX_TRIBE_POP:
        return events
    if tribe.food < tribe.population() * 12:
        return events

    females = [m for m in tribe.members
               if m.reproduction.sex == "F"
               and 14 <= m.vitals.age <= 40
               and m.reproduction.cooldown == 0]

    for f in females:
        if random.random() < 0.003:
            new_id  = tribe.id * 1000 + len(tribe.members) + random.randint(1000, 9999)
            from .components import Member, Position, Vitals, Reproduction, Cognition, SocialRole
            baby = Member(
                id=new_id,
                position=Position(tribe.x + random.randint(-1, 1), tribe.y + random.randint(-1, 1)),
                vitals=Vitals(hunger=0.0, health=1.0, age=0.0),
                reproduction=Reproduction(sex=random.choice(["M", "F"]), fertile=False),
                cognition=Cognition(faith=random.uniform(0.0, 0.1)),
                social=SocialRole(role="gatherer"),
            )
            tribe.members.append(baby)
            f.reproduction.cooldown = 120  # ticks de cooldown

            if random.random() < 0.15:
                events.append({
                    "type":  "birth",
                    "tribe": tribe.id,
                    "text":  f"Un enfant naît chez {tribe.name}.",
                    "color": "birth",
                })

    # Décrémenter cooldowns
    for m in tribe.members:
        if m.reproduction.cooldown > 0:
            m.reproduction.cooldown -= 1

    return events


def system_health_recovery(tribe) -> list[dict]:
    """Récupération lente de la santé si nourriture suffisante."""
    if tribe.food >= tribe.population() * 15:
        for m in tribe.members:
            m.vitals.health = min(1.0, m.vitals.health + 0.005)
            m.vitals.hunger = max(0.0, m.vitals.hunger - 0.01)
    return []


# ── UTILITAIRES INTERNES ─────────────────────────────────────────────
def _mortality_rate(age: float, health: float) -> float:
    """Courbe de Gompertz simplifiée."""
    base = 0.0001
    old_age = math.exp((age - 50) / 10) * 0.001
    sickness = (1.0 - health) * 0.02
    return base + old_age + sickness


def _elect_chief(tribe) -> None:
    """Élit le membre le plus âgé comme nouveau chef."""
    candidates = [m for m in tribe.members if m.social.role != "chief"]
    if not candidates:
        return
    new_chief = max(candidates, key=lambda m: m.vitals.age + m.social.prestige * 5)
    new_chief.social.role = "chief"
