"""
GENESIS ENGINE — simulation/world.py
État global du monde + orchestration du tick principal.
C'est le cœur de la simulation.
Interface stable — on ajoute des systèmes sans modifier ce fichier.
"""
import random
import asyncio
from dataclasses import dataclass, field
from typing import Optional

from ..config import (
    MAP_SIZE, WORLD_SEED, NUM_TRIBES, TRIBE_NAMES, TRIBE_COLORS,
    DIVINE_ENERGY_START, DIVINE_ENERGY_MAX, DIVINE_COSTS,
    FOOD_PER_HUNT, FOOD_PER_GATHER, FOOD_CONSUME_PER_DAY,
    FAITH_DECAY_PER_TICK, PRAYER_FAITH_THRESHOLD, PRAYER_COOLDOWN_TICKS,
    PRAYER_TEMPLATES, MIN_TRIBE_POP, MAX_TRIBE_POP,
    DAYS_PER_TICK, EVENT_LOG_MAX,
)
from .map_generator import MapGenerator, Tile
from .time_system import WorldTime
from .ecs.components import Tribe, Member, Position, Vitals, Reproduction, Cognition, SocialRole, TribeMemory
from .ecs.systems import (
    system_food, system_aging_and_death,
    system_reproduction, system_health_recovery,
)
from .ecs.tribe_system import (
    system_migration, system_faith,
    system_divine_energy_regen, system_extinction_check,
)
from .ecs.systems_warfare import (
    system_tension, system_resolve_wars, get_wars_state,
)
from .ecs.tribe_system import (
    system_migration, system_faith,
    system_divine_energy_regen, system_extinction_check,
)
import server.config as cfg


# ── SINGLETON WORLD STATE ─────────────────────────────────────────────
class WorldState:
    """
    Singleton : état complet du monde en mémoire.
    Accès via world_state (module-level instance).
    """

    def __init__(self):
        self.initialized = False
        self.tiles: list[Tile] = []
        self.tribes: list[Tribe] = []
        self.time = WorldTime(days_per_tick=DAYS_PER_TICK)
        self.divine_energy: float = DIVINE_ENERGY_START
        self.event_log: list[dict] = []
        self.prayers: list[dict] = []
        self.prayer_id_counter: int = 0
        self._tick_lock = asyncio.Lock()
        self._broadcast_fn = None   # injecté par websocket.py

    # ── INITIALISATION ───────────────────────────────────────────────
    def initialize(self):
        if self.initialized:
            return
        gen = MapGenerator(MAP_SIZE, WORLD_SEED)
        self.tiles = gen.generate()
        self.tribes = self._spawn_tribes()
        self.initialized = True
        self._log("Le monde est né dans le silence du Créateur.", "divine")
        self._log("Les premières tribus allument leurs feux.", "birth")

    def _spawn_tribes(self) -> list[Tribe]:
        tribes = []
        used = []
        rng = random.Random(WORLD_SEED + 1)
        S = MAP_SIZE

        for t in range(NUM_TRIBES):
            tx, ty, attempts = 0, 0, 0
            while attempts < 300:
                tx = rng.randint(10, S - 10)
                ty = rng.randint(10, S - 10)
                tile = self.tiles[ty * S + tx]
                close = any(abs(px - tx) < 18 and abs(py - ty) < 18 for px, py in used)
                if tile.biome not in ("water", "mountain") and not close:
                    break
                attempts += 1

            used.append((tx, ty))
            pop = rng.randint(12, 20)
            members = [Member.create(t, i, tx, ty) for i in range(pop)]

            tribes.append(Tribe(
                id=t,
                name=TRIBE_NAMES[t % len(TRIBE_NAMES)],
                color=TRIBE_COLORS[t % len(TRIBE_COLORS)],
                x=tx, y=ty,
                members=members,
                food=rng.uniform(60, 100),
                faith=rng.uniform(0.05, 0.2),
                founded_year=self.time.year_bp,
            ))
        return tribes

    # ── TICK PRINCIPAL ───────────────────────────────────────────────
    async def tick(self):
        async with self._tick_lock:
            time_events = self.time.advance()
            all_events: list[dict] = list(time_events)

            alive = [t for t in self.tribes if t.alive]

            for tribe in alive:
                # Systèmes fondamentaux
                all_events += system_food(tribe, self.tiles, self.time, cfg)
                all_events += system_aging_and_death(tribe, cfg)
                all_events += system_reproduction(tribe, cfg)
                system_health_recovery(tribe)

                # Systèmes IA tribaux
                all_events += system_migration(tribe, self.tiles, self.tribes, cfg)
                all_events += system_faith(tribe, self.time, cfg)

                # Prières
                self._process_prayers(tribe)

                # Décrement cooldown
                if tribe.prayer_cooldown > 0:
                    tribe.prayer_cooldown -= 1

            # Guerres V2
            all_events += system_tension(self.tribes, self.time, cfg)
            all_events += system_resolve_wars(self.tribes, self.time, cfg)

            # Extinction check
            all_events += system_extinction_check(self.tribes, cfg)

            # Régénération énergie divine
            self.divine_energy = system_divine_energy_regen(
                self.tribes, self.divine_energy, cfg
            )

            # Log des événements
            for ev in all_events:
                if "text" in ev:
                    self._log(ev["text"], ev.get("color", ""))

            # Broadcast WebSocket
            if self._broadcast_fn:
                await self._broadcast_fn(self.to_snapshot())

    # ── PRIÈRES ─────────────────────────────────────────────────────
    def _process_prayers(self, tribe: Tribe):
        if tribe.faith < PRAYER_FAITH_THRESHOLD:
            return
        if tribe.prayer_cooldown > 0:
            return

        text, intensity = random.choice(PRAYER_TEMPLATES)
        self.prayer_id_counter += 1
        prayer = {
            "id":       self.prayer_id_counter,
            "tribe_id": tribe.id,
            "tribe_name": tribe.name,
            "text":     text,
            "intensity": round(intensity, 2),
            "tick":     self.time.tick,
            "year_bp":  self.time.year_bp,
            "answered": False,
        }
        self.prayers.insert(0, prayer)
        if len(self.prayers) > 50:
            self.prayers.pop()
        tribe.prayer_cooldown = PRAYER_COOLDOWN_TICKS + random.randint(0, 30)

    # ── ACTIONS DIVINES ──────────────────────────────────────────────
    def divine_action(self, action_type: str, tribe_id: Optional[int] = None) -> dict:
        cost = DIVINE_COSTS.get(action_type, 0)
        if self.divine_energy < cost:
            return {"ok": False, "reason": "Énergie divine insuffisante."}

        # Cible
        alive = [t for t in self.tribes if t.alive]
        if not alive:
            return {"ok": False, "reason": "Aucune tribu vivante."}
        if tribe_id is not None:
            target = next((t for t in alive if t.id == tribe_id), alive[0])
        else:
            target = random.choice(alive)

        self.divine_energy -= cost
        msg = ""

        if action_type == "sign":
            target.faith = min(1.0, target.faith + 0.15)
            target.food  = min(999, target.food  + 20)
            msg = f"✦ Un signe divin illumine {target.name}. Leur foi grandit."
            self._log(msg, "divine")

        elif action_type == "dream":
            target.faith = min(1.0, target.faith + 0.25)
            for m in target.members:
                m.vitals.health = min(1.0, m.vitals.health + 0.1)
            msg = f"☾ Dieu a visité les rêves de {target.name}."
            self._log(msg, "divine")

        elif action_type == "wrath":
            victims = max(1, int(target.population() * 0.2))
            for _ in range(victims):
                if len(target.members) > 2:
                    target.members.pop()
            target.faith = min(1.0, target.faith + 0.4)
            target.memory.disasters += 1
            for t in alive:
                t.faith = min(1.0, t.faith + 0.05)
            msg = f"⚡ La colère divine frappe {target.name}. {victims} morts. La terreur devient foi."
            self._log(msg, "death")

        elif action_type == "bless":
            target.food = min(999, target.food + 80)
            for m in target.members:
                m.vitals.health = min(1.0, m.vitals.health + 0.2)
            target.faith = min(1.0, target.faith + 0.1)
            msg = f"☀ Bénédiction sur {target.name}. Abondance et santé."
            self._log(msg, "divine")

        elif action_type == "miracle":
            target.faith = min(1.0, target.faith + 0.5)
            target.memory.miracles += 1
            target.rituals += 3
            for t in alive:
                if t != target:
                    t.faith = min(1.0, t.faith + 0.1)
            msg = f"✦ Un miracle inexpliqué frappe {target.name}. La foi se propage au monde."
            self._log(msg, "divine")

        elif action_type == "prophet":
            target.faith = min(1.0, target.faith + 0.35)
            target.memory.prophets += 1
            # Ajouter un prophète
            from .ecs.components import Member, Position, Vitals, Reproduction, Cognition, SocialRole
            prophet = Member(
                id=99000 + self.time.tick,
                position=Position(target.x, target.y),
                vitals=Vitals(age=28 + random.randint(0,10), health=1.0),
                reproduction=Reproduction(sex="M"),
                cognition=Cognition(faith=0.95, curiosity=0.9),
                social=SocialRole(role="prophet", prestige=0.9),
            )
            target.members.append(prophet)
            msg = f"☾ Un prophète s'éveille chez {target.name}. Il parle au nom de l'Invisible."
            self._log(msg, "faith")

        elif action_type == "disaster":
            victim = random.choice(alive)
            dead_n = max(1, int(victim.population() * 0.3))
            for _ in range(dead_n):
                if len(victim.members) > 2:
                    victim.members.pop()
            victim.food *= 0.3
            victim.memory.disasters += 1
            for t in alive:
                t.faith = min(1.0, t.faith + 0.15)
            msg = f"⚡ Un fléau dévaste {victim.name}. {dead_n} morts. La terreur du divin se répand."
            self._log(msg, "death")

        elif action_type == "ignore":
            target.faith = max(0.0, target.faith - 0.05)
            msg = f"— La prière de {target.name} reste sans réponse. Le doute s'installe."
            self._log(msg, "")

        return {"ok": True, "message": msg, "tribe": target.name, "energy_remaining": self.divine_energy}

    def answer_prayer(self, prayer_id: int, action_type: str) -> dict:
        prayer = next((p for p in self.prayers if p["id"] == prayer_id), None)
        if not prayer:
            return {"ok": False, "reason": "Prière introuvable."}
        if prayer["answered"]:
            return {"ok": False, "reason": "Déjà exaucée."}
        prayer["answered"] = True
        result = self.divine_action(action_type, prayer["tribe_id"])
        return result

    # ── LOG ─────────────────────────────────────────────────────────
    def _log(self, text: str, color: str = ""):
        entry = {
            "text":    text,
            "color":   color,
            "year_bp": self.time.year_bp,
            "tick":    self.time.tick,
        }
        self.event_log.insert(0, entry)
        if len(self.event_log) > EVENT_LOG_MAX:
            self.event_log.pop()

    # ── SÉRIALISATION ────────────────────────────────────────────────
    def to_snapshot(self) -> dict:
        return {
            "time":          self.time.to_dict(),
            "divine_energy": round(self.divine_energy, 2),
            "tribes":        [t.to_dict() for t in self.tribes],
            "event_log":     self.event_log[:30],
            "prayers":       [p for p in self.prayers[:10]],
            "wars": get_wars_state(),
            "stats": {
                "total_population": sum(t.population() for t in self.tribes if t.alive),
                "alive_tribes":     sum(1 for t in self.tribes if t.alive),
                "avg_faith":        round(
                    sum(t.faith for t in self.tribes if t.alive) / max(1, sum(1 for t in self.tribes if t.alive)), 3
                ),
                "pending_prayers":  sum(1 for p in self.prayers if not p["answered"]),
            }
        }
    def from_snapshot(self, data: dict):
    """Restaure l'état du monde depuis un snapshot PostgreSQL."""
    # Temps
    self.time.tick    = data["time"]["tick"]
    self.time.year_bp = data["time"]["year_bp"]
    self.time.day     = data["time"].get("day", 0)
    self.time.season  = data["time"].get("season", 0)

    # Énergie divine
    self.divine_energy = data.get("divine_energy", DIVINE_ENERGY_START)

    # Logs & prières
    self.event_log = data.get("event_log", [])
    self.prayers   = data.get("prayers", [])

    # Tribus
    for t_data in data.get("tribes", []):
        tribe = next((t for t in self.tribes if t.id == t_data["id"]), None)
        if tribe:
            tribe.food        = t_data.get("food", tribe.food)
            tribe.faith       = t_data.get("faith", tribe.faith)
            tribe.alive       = t_data.get("alive", True)
            tribe.x           = t_data.get("x", tribe.x)
            tribe.y           = t_data.get("y", tribe.y)
            tribe.rituals     = t_data.get("rituals", 0)

    self._log(f"[Restauration] Monde chargé — tick {self.time.tick}, an {self.time.year_bp} BP", "divine")

    def map_to_dict(self) -> dict:
        gen = MapGenerator(MAP_SIZE, WORLD_SEED)
        return {
            "size":  MAP_SIZE,
            "tiles": gen.tiles_to_dict(self.tiles),
        }


# ── MODULE-LEVEL SINGLETON ────────────────────────────────────────────
world_state = WorldState()
