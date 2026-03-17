# Genesis Engine V1

> Simulateur civilisationnel métaphysique persistant.
> Époque paléolithique · 5 tribus autonomes · Toi en Dieu silencieux.

---

## 🚀 Déploiement sur Railway (gratuit, 5 minutes)

### Étape 1 — Créer le repo GitHub

1. Va sur [github.com](https://github.com) → **New repository**
2. Nom : `genesis-engine`
3. Privé ou public (au choix)
4. **Ne pas** initialiser avec README (on a déjà tout)

### Étape 2 — Pousser le code

```bash
# Dans le dossier world-sim/
git init
git add .
git commit -m "Genesis Engine V1 — Initial commit"
git remote add origin https://github.com/TON_USERNAME/genesis-engine.git
git push -u origin main
```

### Étape 3 — Déployer sur Railway

1. Va sur [railway.app](https://railway.app)
2. **Login avec GitHub**
3. **New Project** → **Deploy from GitHub repo** → sélectionne `genesis-engine`
4. Railway détecte Python automatiquement ✓
5. Clique sur **Add Service** → **Database** → **PostgreSQL**
6. Va dans les **Variables** de ton service Python :
   - `DATABASE_URL` → copier depuis le service PostgreSQL (bouton "Connect")
   - `WORLD_SEED` → `42` (ou autre pour un monde différent)
7. **Deploy** → attendre 2 minutes

### Étape 4 — Récupérer l'URL

Railway génère une URL du type : `https://genesis-engine-production.up.railway.app`

### Étape 5 — Connecter le frontend

Dans `client/index.html`, remplacer :
```javascript
const API_URL = "http://localhost:8000";
const WS_URL  = "ws://localhost:8000/ws";
```
par :
```javascript
const API_URL = "https://genesis-engine-production.up.railway.app";
const WS_URL  = "wss://genesis-engine-production.up.railway.app/ws";
```

---

## 📡 API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Status serveur |
| GET | `/world/state` | Snapshot complet |
| GET | `/world/map` | Carte (appelée 1x) |
| GET | `/world/tribes` | Liste des tribus |
| GET | `/world/tribes/{id}` | Détail tribu |
| GET | `/world/events` | Journal d'événements |
| GET | `/divine/inbox` | Boîte divine + prières |
| GET | `/divine/energy` | Énergie divine |
| POST | `/divine/action` | Action divine globale |
| POST | `/divine/prayer/{id}/answer` | Répondre à une prière |
| WS | `/ws` | Stream temps réel |

### Exemple POST /divine/action
```json
{
  "action": "miracle",
  "tribe_id": 2
}
```
Actions disponibles : `sign` · `dream` · `wrath` · `bless` · `miracle` · `prophet` · `disaster` · `ignore`

---

## 🏗 Structure des fichiers

```
world-sim/
├── server/
│   ├── main.py              ← FastAPI + boucle tick
│   ├── config.py            ← toutes les constantes
│   ├── simulation/
│   │   ├── world.py         ← état global + orchestration
│   │   ├── map_generator.py ← Perlin noise → biomes
│   │   ├── time_system.py   ← jours / saisons / années
│   │   └── ecs/
│   │       ├── components.py   ← Tribe, Member (dataclasses)
│   │       ├── systems.py      ← nourriture, mort, reproduction
│   │       └── tribe_system.py ← migration, foi, extinction
│   ├── divine/
│   │   ├── prayer_system.py ← helpers prières
│   │   └── divine_energy.py ← helpers énergie
│   ├── api/
│   │   ├── routes_world.py  ← endpoints monde
│   │   ├── routes_divine.py ← endpoints divins
│   │   └── websocket.py     ← WebSocket temps réel
│   └── persistence/
│       └── save_manager.py  ← snapshots PostgreSQL
├── database/
│   └── schema.sql           ← structure DB
├── client/
│   └── genesis_engine_v1.html ← frontend Three.js
├── requirements.txt
├── Procfile                 ← pour Railway
├── runtime.txt              ← Python 3.11
└── .env.example
```

## ⚙️ Paramètres importants (config.py)

| Paramètre | Valeur | Effet |
|-----------|--------|-------|
| `TICK_INTERVAL_SEC` | 10 | 1 tick = 10 secondes réelles |
| `DAYS_PER_TICK` | 3 | = 3 jours simulés par tick |
| `NUM_TRIBES` | 5 | Tribus initiales |
| `WORLD_SEED` | 42 | Changer = nouveau monde |
| `PRAYER_FAITH_THRESHOLD` | 0.45 | Foi minimum pour prier |

## 🔮 Prochaines étapes (V2)

- [ ] Guerres inter-tribales
- [ ] Transmission culturelle entre tribus
- [ ] Mythologie persistante générée par IA
- [ ] Prophètes avec messages complexes
- [ ] Langues primitives émergentes
- [ ] Néolithique (agriculture)
