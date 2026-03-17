"""
GENESIS ENGINE — config.py
Constantes globales du monde. On ne touche plus à ce fichier.
Pour changer des paramètres → créer un config_override.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

# ── BASE DE DONNÉES ──────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/genesis")

# ── SERVEUR ──────────────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ── MONDE ────────────────────────────────────────────────────────────
MAP_SIZE          = 128          # 128×128 tiles ≈ 100km×100km
WORLD_SEED        = int(os.getenv("WORLD_SEED", "42"))

# ── TEMPS SIMULÉ ─────────────────────────────────────────────────────
TICK_INTERVAL_SEC = 10           # 1 tick réel = X secondes réelles
DAYS_PER_TICK     = 3            # jours simulés par tick
INITIAL_YEAR_BP   = 12_400       # Paléolithique supérieur

# ── TRIBUS ───────────────────────────────────────────────────────────
NUM_TRIBES        = 5
MAX_TRIBE_POP     = 45
MIN_TRIBE_POP     = 4            # en dessous → extinction

# ── NOURRITURE ───────────────────────────────────────────────────────
FOOD_PER_HUNT     = 12
FOOD_PER_GATHER   = 5
FOOD_CONSUME_PER_DAY = 1.2

# ── FOI & PRIÈRES ────────────────────────────────────────────────────
FAITH_DECAY_PER_TICK     = 0.002
PRAYER_FAITH_THRESHOLD   = 0.45
PRAYER_COOLDOWN_TICKS    = 50

# ── ÉNERGIE DIVINE ───────────────────────────────────────────────────
DIVINE_ENERGY_MAX        = 100.0
DIVINE_ENERGY_START      = 72.0
DIVINE_ENERGY_REGEN_BASE = 0.003  # par croyant par tick

# ── COÛTS DES ACTIONS DIVINES ────────────────────────────────────────
DIVINE_COSTS = {
    "sign":     2,
    "dream":    5,
    "wrath":    8,
    "bless":    5,
    "miracle":  15,
    "prophet":  25,
    "disaster": 20,
    "ignore":   0,
}

# ── PERSISTANCE ──────────────────────────────────────────────────────
SNAPSHOT_INTERVAL_TICKS = 30     # snapshot DB toutes les 30 ticks
EVENT_LOG_MAX            = 1000  # événements gardés en mémoire

# ── NOMS DES TRIBUS ──────────────────────────────────────────────────
TRIBE_NAMES = [
    "Enfants de l'Aube",
    "Gardiens du Rocher",
    "Peuple des Eaux",
    "Fils de la Forêt",
    "Clan du Vent",
    "Chasseurs d'Étoiles",
    "Tribu du Feu Vieux",
]

TRIBE_COLORS = [
    "#e8a840", "#60b8e0", "#80c870",
    "#e06868", "#b878e0", "#70d0c0", "#f0d060",
]

# ── PRIÈRES PRIMITIVES ───────────────────────────────────────────────
PRAYER_TEMPLATES = [
    ("Grand Esprit, l'hiver nous dévore. Protège nos enfants.", 0.9),
    ("Seigneur du ciel, nos chasseurs reviennent les mains vides.", 0.7),
    ("Ô Créateur, pourquoi as-tu frappé notre chef de maladie ?", 0.85),
    ("Nous t'offrons ce feu, Être sans nom. Vois notre dévotion.", 0.5),
    ("Le tonnerre a parlé cette nuit. Est-ce ta voix, Grand Invisible ?", 0.6),
    ("Nos morts réclament-ils notre sang ? Dis-nous comment apaiser les ombres.", 0.75),
    ("Pourquoi les bêtes fuient-elles notre territoire depuis trois lunes ?", 0.65),
    ("Maître des rêves, envoie-nous un signe dans les flammes.", 0.55),
    ("La femme du chef a mis au monde un enfant aux yeux clairs. Est-ce ton signe ?", 0.4),
    ("Nous mourons de soif. Les rivières se taisent. Parle !", 0.95),
    ("Grande Ombre, accepte notre offrande de sang et de sel.", 0.6),
    ("Nos ancêtres nous parlent-ils dans les craquements du feu ?", 0.5),
]
