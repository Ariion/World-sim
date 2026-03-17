"""
GENESIS ENGINE — simulation/map_generator.py
Génération procédurale de la carte via bruit de Perlin fBm.
Interface stable — ne pas modifier. Étendre via map_features.py
"""
import math
import random
from dataclasses import dataclass
from typing import Literal

import numpy as np

Biome = Literal["water", "shore", "river", "plains", "scrub", "forest", "highland", "mountain"]


@dataclass(frozen=True)
class Tile:
    biome: Biome
    height: float        # 0.0 → 1.0
    moisture: float      # 0.0 → 1.0
    fertility: float     # capacité agricole/cueillette
    huntable: float      # densité de faune chassable
    resource: float      # ressources générales


class MapGenerator:
    """
    Génère une carte 2D de taille SIZE×SIZE.
    Résultat : liste plate de Tile, indexée par y*SIZE + x.
    """

    def __init__(self, size: int, seed: int = 42):
        self.size = size
        self.seed = seed
        self._init_permutation(seed)

    # ── PERLIN NOISE ─────────────────────────────────────────────────
    def _init_permutation(self, seed: int):
        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        self._perm = p * 2

    def _fade(self, t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def _grad(self, h: int, x: float, y: float) -> float:
        v = h & 3
        if v == 0: return  x + y
        if v == 1: return -x + y
        if v == 2: return  x - y
        return -x - y

    def _noise2(self, x: float, y: float) -> float:
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        x -= math.floor(x)
        y -= math.floor(y)
        u, v = self._fade(x), self._fade(y)
        p = self._perm
        a  = p[X] + Y;   aa = p[a];   ab = p[a + 1]
        b  = p[X+1] + Y; ba = p[b];   bb = p[b + 1]
        return self._lerp(
            self._lerp(self._grad(p[aa], x,   y),   self._grad(p[ba], x-1, y),   u),
            self._lerp(self._grad(p[ab], x,   y-1), self._grad(p[bb], x-1, y-1), u),
            v
        )

    def _fbm(self, x: float, y: float, octaves: int = 6) -> float:
        val, amp, freq, mx = 0.0, 0.5, 1.0, 0.0
        for _ in range(octaves):
            val += self._noise2(x * freq, y * freq) * amp
            mx  += amp
            amp  *= 0.5
            freq *= 2.1
        return val / mx

    # ── GÉNÉRATION ───────────────────────────────────────────────────
    def generate(self) -> list[Tile]:
        S = self.size
        scale = 0.04

        # Heightmap
        heights = np.zeros((S, S), dtype=np.float32)
        for y in range(S):
            for x in range(S):
                h = self._fbm(x * scale + 3.1, y * scale + 1.7, 6)
                # Forme en cuvette (vallée centrale plus basse)
                cx = (x - S / 2) / (S / 2)
                cy = (y - S / 2) / (S / 2)
                h -= 0.15 * (cx * cx + cy * cy)
                heights[y, x] = h

        # Normalisation 0→1
        mn, mx = heights.min(), heights.max()
        heights = (heights - mn) / (mx - mn)

        # Moisture map (seed décalé)
        moisture = np.zeros((S, S), dtype=np.float32)
        self._init_permutation(self.seed + 99)
        for y in range(S):
            for x in range(S):
                moisture[y, x] = self._fbm(x * scale + 10, y * scale + 20, 4) * 0.5 + 0.5
        self._init_permutation(self.seed)

        # Assignation des biomes
        tiles = []
        for y in range(S):
            for x in range(S):
                h = float(heights[y, x])
                m = float(moisture[y, x])
                tiles.append(self._classify(h, m))

        # Rivières
        self._carve_rivers(tiles, heights, S)

        return tiles

    def _classify(self, h: float, m: float) -> Tile:
        if h < 0.30:
            return Tile("water",    h, m, 0.0, 0.1, 5.0)
        if h < 0.35:
            return Tile("shore",    h, m, 0.6, 0.4, 30.0)
        if h < 0.75:
            if m > 0.65:
                return Tile("forest",   h, m, 0.7, 0.8, 60.0)
            if m > 0.40:
                return Tile("plains",   h, m, 0.9, 0.6, 70.0)
            return     Tile("scrub",    h, m, 0.5, 0.4, 40.0)
        if h < 0.88:
            return Tile("highland", h, m, 0.2, 0.3, 20.0)
        return     Tile("mountain", h, m, 0.0, 0.1, 5.0)

    def _carve_rivers(self, tiles: list, heights: np.ndarray, S: int):
        """Trace des rivières depuis le centre vers les bords."""
        rng = random.Random(self.seed + 7)
        for _ in range(6):
            x = rng.randint(S // 2 - 15, S // 2 + 15)
            y = rng.randint(S // 2 - 15, S // 2 + 15)
            for _ in range(80):
                if not (1 <= x < S - 1 and 1 <= y < S - 1):
                    break
                idx = y * S + x
                if tiles[idx].biome == "water":
                    break
                # Remplacer par rivière
                t = tiles[idx]
                tiles[idx] = Tile("river", t.height, 1.0, 1.0, 0.7, 80.0)
                # Descendre la pente + bruit
                neighbors = [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]
                valid = [(nx,ny) for nx,ny in neighbors if 0<=nx<S and 0<=ny<S]
                valid.sort(key=lambda p: heights[p[1], p[0]])
                nx, ny = valid[0]
                if heights[ny, nx] >= heights[y, x] - 0.005:
                    nx, ny = rng.choice(valid)
                x, y = nx, ny

    # ── SÉRIALISATION ─────────────────────────────────────────────────
    def tiles_to_dict(self, tiles: list[Tile]) -> list[dict]:
        return [
            {
                "biome": t.biome,
                "height": round(t.height, 3),
                "moisture": round(t.moisture, 3),
                "fertility": round(t.fertility, 2),
                "huntable": round(t.huntable, 2),
            }
            for t in tiles
        ]
