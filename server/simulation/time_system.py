"""
GENESIS ENGINE — simulation/time_system.py
Gestion du temps simulé : ticks, jours, saisons, années.
Interface stable — ne pas modifier.
"""
from dataclasses import dataclass
from typing import Literal

Season = Literal["spring", "summer", "autumn", "winter"]

SEASON_LABELS = {
    "spring": ("🌱", "Printemps"),
    "summer": ("☀",  "Été"),
    "autumn": ("🍂", "Automne"),
    "winter": ("❄",  "Hiver"),
}


@dataclass
class WorldTime:
    tick: int        = 0
    day: float       = 1.0    # jour dans l'année (0–360)
    year_bp: int     = 12_400  # années avant présent
    days_per_tick: int = 3

    # ── PROPRIÉTÉS ───────────────────────────────────────────────────
    @property
    def season(self) -> Season:
        frac = (self.day % 360) / 360
        if frac < 0.25:  return "spring"
        if frac < 0.50:  return "summer"
        if frac < 0.75:  return "autumn"
        return "winter"

    @property
    def season_index(self) -> int:
        return ["spring", "summer", "autumn", "winter"].index(self.season)

    @property
    def is_winter(self) -> bool:
        return self.season == "winter"

    @property
    def is_summer(self) -> bool:
        return self.season == "summer"

    @property
    def winter_penalty(self) -> float:
        return 0.55 if self.is_winter else 1.0

    @property
    def summer_bonus(self) -> float:
        return 1.35 if self.is_summer else 1.0

    # ── AVANCE ───────────────────────────────────────────────────────
    def advance(self) -> dict:
        """Avance d'un tick. Retourne les événements temporels."""
        self.tick += 1
        self.day  += self.days_per_tick
        events = []

        if self.day >= 360:
            self.day -= 360
            self.year_bp -= 1
            events.append({"type": "new_year", "year": self.year_bp})

        # Changement de saison
        prev_season = self.season
        # (déjà recalculé depuis self.day)
        return events

    def to_dict(self) -> dict:
        emoji, label = SEASON_LABELS[self.season]
        return {
            "tick":    self.tick,
            "day":     round(self.day),
            "year_bp": self.year_bp,
            "season":  self.season,
            "season_label": label,
            "season_emoji": emoji,
            "winter_penalty": self.winter_penalty,
            "summer_bonus":   self.summer_bonus,
        }
