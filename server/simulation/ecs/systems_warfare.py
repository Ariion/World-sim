"""
GENESIS ENGINE — ecs/systems_warfare.py
Guerres inter-tribales émergentes.
Nouveau fichier V2 — ne touche pas aux fichiers V1.

Logique :
- Tension monte entre tribus proches si ressources rares
- Raid : petite tribu vole nourriture d'une autre
- Guerre ouverte : bataille rangée, pertes des deux côtés
- Vainqueur pillage, perdant fuit ou s'éteint
- Les guerres génèrent des pics de foi et des prières
"""
import random
import math
from dataclasses import dataclass, field
from typing import Optional


# ── ÉTAT DE GUERRE ────────────────────────────────────────────────────
@dataclass
class WarState:
    """Conflit actif entre deux tribus."""
    attacker_id: int
    defender_id: int
    started_tick: int
    reason: str          # "resources" | "territory" | "ritual"
    intensity: float     # 0.0 → 1.0
    duration: int = 0    # ticks depuis début
    resolved: bool = False
    winner_id: Optional[int] = None
    log: list = field(default_factory=list)


# ── REGISTRE DES GUERRES ─────────────────────────────────────────────
active_wars: list[WarState] = []
war_history: list[dict]     = []


# ── SYSTÈME DE TENSION ────────────────────────────────────────────────
def system_tension(tribes, world_time, cfg) -> list[dict]:
    """
    Calcule la tension entre tribus voisines.
    Si tension > seuil → déclenche raid ou guerre.
    """
    events = []
    alive = [t for t in tribes if t.alive]

    for i, t1 in enumerate(alive):
        for t2 in alive[i+1:]:
            dist = math.hypot(t1.x - t2.x, t1.y - t2.y)
            if dist > 25:
                continue  # trop loin pour se battre

            # Déjà en guerre ?
            already = any(
                (w.attacker_id == t1.id and w.defender_id == t2.id) or
                (w.attacker_id == t2.id and w.defender_id == t1.id)
                for w in active_wars if not w.resolved
            )
            if already:
                continue

            # Calcul tension
            tension = _compute_tension(t1, t2, dist)

            # Raid (tension modérée)
            if tension > 0.55 and random.random() < 0.015:
                ev = _trigger_raid(t1, t2, world_time.tick)
                if ev:
                    events.append(ev)

            # Guerre ouverte (tension haute)
            elif tension > 0.78 and random.random() < 0.006:
                ev = _trigger_war(t1, t2, world_time.tick)
                if ev:
                    events.append(ev)

    return events


def _compute_tension(t1, t2, dist: float) -> float:
    """
    Tension = f(proximité, ressources, foi, mémoire de conflits passés).
    """
    proximity   = max(0, 1.0 - dist / 25.0)
    food_stress = max(0, 1.0 - (t1.food / max(1, t1.population() * 12)))
    faith_war   = (t1.faith + t2.faith) / 2 * 0.3  # foi haute → guerre sainte possible
    past_wars   = sum(1 for w in war_history if
                      (w["attacker"] == t1.id and w["defender"] == t2.id) or
                      (w["attacker"] == t2.id and w["defender"] == t1.id)) * 0.1

    return min(1.0, proximity * 0.5 + food_stress * 0.3 + faith_war * 0.1 + past_wars * 0.1)


# ── RAID ─────────────────────────────────────────────────────────────
def _trigger_raid(attacker, defender, tick: int) -> Optional[dict]:
    """
    Raid éclair : quelques chasseurs volent de la nourriture.
    Pas de guerre ouverte, mais crée de la rancœur.
    """
    hunters = len(attacker.hunters())
    if hunters == 0:
        return None

    # Calcul du butin
    stolen = min(defender.food * 0.2, hunters * 8)
    defender_losses = max(0, int(random.random() < 0.3))  # parfois 1 mort défenseur
    attacker_losses = max(0, int(random.random() < 0.2))  # parfois 1 mort attaquant

    defender.food -= stolen
    attacker.food += stolen

    if defender_losses and len(defender.members) > 3:
        defender.members.pop()
        defender.memory.total_dead += 1

    if attacker_losses and len(attacker.members) > 3:
        attacker.members.pop()
        attacker.memory.total_dead += 1

    # Montée de foi chez les deux (peur + colère)
    attacker.faith = min(1.0, attacker.faith + 0.05)
    defender.faith = min(1.0, defender.faith + 0.10)
    defender.memory.disasters += 1

    text = (f"Les {attacker.name} ont pillé le camp des {defender.name}. "
            f"{round(stolen)} unités de nourriture dérobées.")

    return {"type": "raid", "text": text, "color": "death",
            "attacker": attacker.id, "defender": defender.id}


# ── GUERRE OUVERTE ────────────────────────────────────────────────────
def _trigger_war(attacker, defender, tick: int) -> Optional[dict]:
    """Déclare une guerre ouverte entre deux tribus."""
    reasons = ["la disette pousse", "un ancien affront", "des terres fertiles convoitées",
               "la volonté des esprits", "un raid non vengé"]
    reason = random.choice(reasons)

    war = WarState(
        attacker_id=attacker.id,
        defender_id=defender.id,
        started_tick=tick,
        reason=reason,
        intensity=random.uniform(0.5, 0.9),
    )
    active_wars.append(war)

    text = (f"La guerre éclate entre {attacker.name} et {defender.name} — {reason}.")
    return {"type": "war_start", "text": text, "color": "death",
            "attacker": attacker.id, "defender": defender.id, "war": war}


# ── RÉSOLUTION DES GUERRES ACTIVES ────────────────────────────────────
def system_resolve_wars(tribes, world_time, cfg) -> list[dict]:
    """
    Fait progresser et résout les guerres actives.
    Appelé à chaque tick.
    """
    events = []
    tribe_map = {t.id: t for t in tribes}

    for war in active_wars:
        if war.resolved:
            continue

        att = tribe_map.get(war.attacker_id)
        dfd = tribe_map.get(war.defender_id)

        # Tribu disparue → fin de guerre
        if not att or not att.alive or not dfd or not dfd.alive:
            war.resolved = True
            continue

        war.duration += 1

        # Bataille par tick (pertes proportionnelles à la taille + intensité)
        att_strength = len(att.hunters()) * (0.5 + att.faith * 0.5)
        dfd_strength = len(dfd.hunters()) * (0.5 + dfd.faith * 0.5) * 1.1  # défenseur avantage

        att_losses = max(0, int(random.gauss(dfd_strength * 0.08 * war.intensity, 0.5)))
        dfd_losses = max(0, int(random.gauss(att_strength * 0.07 * war.intensity, 0.5)))

        for _ in range(att_losses):
            if len(att.members) > 2:
                att.members.pop()
                att.memory.total_dead += 1

        for _ in range(dfd_losses):
            if len(dfd.members) > 2:
                dfd.members.pop()
                dfd.memory.total_dead += 1

        # Foi monte des deux côtés pendant la guerre
        att.faith = min(1.0, att.faith + 0.008)
        dfd.faith = min(1.0, dfd.faith + 0.012)

        # Événement de bataille occasionnel
        if random.random() < 0.15:
            total_dead = att_losses + dfd_losses
            if total_dead > 0:
                war.log.append(f"An {world_time.year_bp}: {total_dead} morts")
                events.append({
                    "type": "battle",
                    "text": f"La guerre entre {att.name} et {dfd.name} fait {total_dead} morts ce jour.",
                    "color": "death",
                })

        # Conditions de fin
        att_pop = att.population()
        dfd_pop = dfd.population()
        war_over = False

        # Victoire par écrasement
        if att_pop < cfg.MIN_TRIBE_POP + 2:
            war.resolved = True
            war.winner_id = dfd.id
            war_over = True
            _resolve_victory(dfd, att, war, events)

        elif dfd_pop < cfg.MIN_TRIBE_POP + 2:
            war.resolved = True
            war.winner_id = att.id
            war_over = True
            _resolve_victory(att, dfd, war, events)

        # Épuisement mutuel (longue guerre)
        elif war.duration > 40 and random.random() < 0.08:
            war.resolved = True
            war_over = True
            events.append({
                "type": "war_end",
                "text": f"Épuisés, {att.name} et {dfd.name} cessent les combats. Paix fragile.",
                "color": "faith",
            })
            att.faith = min(1.0, att.faith + 0.1)
            dfd.faith = min(1.0, dfd.faith + 0.1)

        if war_over:
            war_history.append({
                "attacker": war.attacker_id,
                "defender": war.defender_id,
                "winner":   war.winner_id,
                "duration": war.duration,
                "reason":   war.reason,
            })

    # Nettoyer les guerres résolues
    active_wars[:] = [w for w in active_wars if not w.resolved]

    return events


def _resolve_victory(winner, loser, war: WarState, events: list):
    """Le vainqueur pille et la tribu perdante fuit ou s'éteint."""
    # Pillage
    loot = loser.food * 0.6
    winner.food += loot
    loser.food  *= 0.4
    winner.memory.miracles += 1  # victoire = miracle divin pour le vainqueur
    loser.memory.disasters += 1

    # Foi explosive chez le vainqueur
    winner.faith = min(1.0, winner.faith + 0.3)
    loser.faith  = min(1.0, loser.faith  + 0.4)  # trauma → foi

    events.append({
        "type":  "war_victory",
        "text":  (f"{winner.name} a vaincu {loser.name} après {war.duration} ticks de guerre. "
                  f"Butin : {round(loot)} unités. Les survivants fuient."),
        "color": "death",
        "winner": winner.id,
        "loser":  loser.id,
    })


# ── API : ÉTAT DES GUERRES ────────────────────────────────────────────
def get_wars_state() -> dict:
    return {
        "active_wars": [
            {
                "attacker_id": w.attacker_id,
                "defender_id": w.defender_id,
                "reason":      w.reason,
                "intensity":   round(w.intensity, 2),
                "duration":    w.duration,
            }
            for w in active_wars if not w.resolved
        ],
        "war_history": war_history[-20:],
        "total_wars":  len(war_history),
    }
