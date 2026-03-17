"""
GENESIS ENGINE — ecs/components.py
Composants ECS purs. Dataclasses sérialisables.
Règle : on n'ajoute pas de logique ici, uniquement des données.
Pour ajouter un composant → créer components_v2.py
"""
from dataclasses import dataclass, field
from typing import Literal
import random


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Vitals:
    hunger: float = 0.3       # 0=rassasié 1=mourant de faim
    health: float = 1.0       # 0=mort 1=parfaite santé
    age: float    = 0.0       # en années simulées


@dataclass
class Reproduction:
    sex: Literal["M", "F"] = "M"
    fertile: bool = True
    cooldown: int = 0         # ticks avant prochaine reproduction possible


@dataclass
class Cognition:
    faith:    float = 0.1     # 0=athée 1=fanatique
    fear:     float = 0.0     # peur du surnaturel
    curiosity: float = 0.3    # ouverture au mystère


@dataclass
class SocialRole:
    role: Literal["chief", "hunter", "gatherer", "elder", "prophet"] = "gatherer"
    prestige: float = 0.0     # influence dans la tribu


@dataclass
class Member:
    """Un individu complet."""
    id: int
    position: Position
    vitals: Vitals
    reproduction: Reproduction
    cognition: Cognition
    social: SocialRole

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.position.x,
            "y": self.position.y,
            "age": round(self.vitals.age, 1),
            "health": round(self.vitals.health, 3),
            "hunger": round(self.vitals.hunger, 3),
            "faith": round(self.cognition.faith, 3),
            "sex": self.reproduction.sex,
            "role": self.social.role,
        }

    @classmethod
    def create(cls, tribe_id: int, idx: int, tx: int, ty: int) -> "Member":
        role = "chief" if idx == 0 else ("hunter" if random.random() < 0.5 else "gatherer")
        return cls(
            id=tribe_id * 1000 + idx,
            position=Position(tx + random.randint(-2, 2), ty + random.randint(-2, 2)),
            vitals=Vitals(
                hunger=random.uniform(0.1, 0.4),
                health=random.uniform(0.7, 1.0),
                age=random.uniform(10, 35),
            ),
            reproduction=Reproduction(
                sex=random.choice(["M", "F"]),
                fertile=True,
            ),
            cognition=Cognition(
                faith=random.uniform(0.0, 0.2),
                fear=random.uniform(0.0, 0.3),
            ),
            social=SocialRole(role=role),
        )


@dataclass
class TribeMemory:
    """Mémoire collective simple de la tribu."""
    disasters: int = 0
    miracles: int  = 0
    prophets: int  = 0
    winters_survived: int = 0
    total_dead: int = 0


@dataclass
class Tribe:
    """Entité tribu complète."""
    id: int
    name: str
    color: str
    x: int
    y: int
    members: list = field(default_factory=list)
    food: float   = 60.0
    faith: float  = 0.1
    alive: bool   = True
    prayer_cooldown: int = 0
    territory_radius: int = 8
    rituals: int  = 0
    memory: TribeMemory = field(default_factory=TribeMemory)
    founded_year: int = 12400

    def population(self) -> int:
        return len(self.members)

    def hunters(self) -> list:
        return [m for m in self.members if m.social.role in ("hunter", "chief")]

    def gatherers(self) -> list:
        return [m for m in self.members if m.social.role == "gatherer"]

    def avg_faith(self) -> float:
        if not self.members:
            return 0.0
        return sum(m.cognition.faith for m in self.members) / len(self.members)

    def food_status(self) -> str:
        ratio = self.food / max(1, self.population() * 10)
        if ratio > 1.5:  return "abundant"
        if ratio > 0.8:  return "stable"
        if ratio > 0.4:  return "scarce"
        return "famine"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "x": self.x,
            "y": self.y,
            "population": self.population(),
            "food": round(self.food, 1),
            "faith": round(self.faith, 3),
            "alive": self.alive,
            "rituals": self.rituals,
            "food_status": self.food_status(),
            "memory": {
                "disasters": self.memory.disasters,
                "miracles": self.memory.miracles,
                "prophets": self.memory.prophets,
                "winters_survived": self.memory.winters_survived,
                "total_dead": self.memory.total_dead,
            },
            "members_summary": {
                "hunters": len(self.hunters()),
                "gatherers": len(self.gatherers()),
                "avg_age": round(
                    sum(m.vitals.age for m in self.members) / max(1, self.population()), 1
                ),
            }
        }
