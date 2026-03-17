"""
GENESIS ENGINE — ecs/tribe_system.py
Système IA tribal : migration, foi collective, événements métaphysiques.
Interface stable.
"""
import random
import math
from typing import TYPE_CHECKING

METAPHYSICAL_EVENTS = [
    ("Un rêve étrange visita le chef cette nuit.", 0.05),
    ("Une étoile filante traversa le ciel à l'aube.", 0.04),
    ("Un animal albinos fut aperçu à l'orée du camp.", 0.03),
    ("La fumée du feu dessina une silhouette humaine.", 0.04),
    ("Un tonnerre sans nuage résonna dans la vallée.", 0.05),
    ("Les enfants se mirent à parler en dormant, tous la même nuit.", 0.02),
    ("La rivière coula rouge pendant une journée.", 0.02),
    ("Un ancien mourut en souriant, les yeux ouverts vers le ciel.", 0.03),
    ("Les oiseaux gardèrent le silence pendant trois jours.", 0.03),
    ("Une lumière inexpliquée fut observée sur le rocher sacré.", 0.02),
]


def system_migration(tribe, tiles, tribes_all, cfg) -> list[dict]:
    """
    La tribu migre si nourriture trop basse ou aléatoirement.
    Évite les cases occupées par d'autres tribus et les obstacles.
    """
    events = []
    S = cfg.MAP_SIZE

    should_move = (
        tribe.food < tribe.population() * 8
        or random.random() < 0.003
    )
    if not should_move:
        return events

    directions = [
        (-3, 0), (3, 0), (0, -3), (0, 3),
        (-3, -3), (3, 3), (-3, 3), (3, -3),
        (-5, 0), (5, 0), (0, -5), (0, 5),
    ]

    best_pos   = None
    best_score = -math.inf

    for dx, dy in directions:
        nx, ny = tribe.x + dx, tribe.y + dy
        if not (2 <= nx < S - 2 and 2 <= ny < S - 2):
            continue
        t = tiles[ny * S + nx]
        if t.biome in ("water", "mountain"):
            continue
        # Pas trop proche d'une autre tribu
        too_close = any(
            ot.alive and ot.id != tribe.id and math.hypot(ot.x - nx, ot.y - ny) < 10
            for ot in tribes_all
        )
        if too_close:
            continue

        score = t.fertility + t.huntable - random.uniform(0, 0.2)
        if score > best_score:
            best_score = best_pos and score
            best_score = score
            best_pos   = (nx, ny)

    if best_pos:
        old_x, old_y = tribe.x, tribe.y
        tribe.x, tribe.y = best_pos
        if tribe.food < tribe.population() * 5:
            events.append({
                "type":  "migration",
                "tribe": tribe.id,
                "text":  f"{tribe.name} migre vers de nouveaux territoires, fuyant la disette.",
                "color": "warn",
            })

    return events


def system_faith(tribe, world_time, cfg) -> list[dict]:
    """
    Calcule l'évolution de la foi collective.
    La foi décroît naturellement, augmente avec catastrophes et mystère.
    """
    events = []

    # Décroissance naturelle
    tribe.faith = max(0.0, tribe.faith - cfg.FAITH_DECAY_PER_TICK)

    # Hiver → peur → foi
    if world_time.is_winter and random.random() < 0.008:
        tribe.faith = min(1.0, tribe.faith + 0.04)
        tribe.memory.winters_survived += 1

    # Famine → foi intense
    if tribe.food < tribe.population() * 3:
        tribe.faith = min(1.0, tribe.faith + 0.008)

    # Événement métaphysique aléatoire
    for desc, prob in METAPHYSICAL_EVENTS:
        if random.random() < prob * 0.1:
            tribe.faith  = min(1.0, tribe.faith + random.uniform(0.03, 0.08))
            tribe.rituals += 1
            events.append({
                "type":  "metaphysical",
                "tribe": tribe.id,
                "text":  f"{tribe.name} — {desc}",
                "color": "faith",
            })
            break  # un seul événement par tick

    # Propager la foi aux membres
    for m in tribe.members:
        delta = (tribe.faith - m.cognition.faith) * 0.05
        m.cognition.faith = max(0.0, min(1.0, m.cognition.faith + delta))

    return events


def system_divine_energy_regen(tribes, divine_energy, cfg) -> float:
    """
    Calcule la régénération de l'énergie divine à partir de la foi collective.
    Retourne la nouvelle valeur d'énergie.
    """
    total_regen = 0.0
    for tribe in tribes:
        if not tribe.alive:
            continue
        total_regen += tribe.faith * cfg.DIVINE_ENERGY_REGEN_BASE * tribe.population() / 20

    new_energy = min(cfg.DIVINE_ENERGY_MAX, divine_energy + total_regen)
    return new_energy


def system_extinction_check(tribes, cfg) -> list[dict]:
    """
    Vérifie si des tribus doivent s'éteindre.
    """
    events = []
    for tribe in tribes:
        if not tribe.alive:
            continue
        if tribe.population() < cfg.MIN_TRIBE_POP:
            tribe.alive = False
            events.append({
                "type":  "extinction",
                "tribe": tribe.id,
                "text":  f"{tribe.name} s'est éteinte. Leurs feux ne s'allumeront plus.",
                "color": "death",
            })
    return events
