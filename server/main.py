"""
GENESIS ENGINE — server/main.py
Point d'entrée FastAPI.
Lance la simulation en arrière-plan via asyncio.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import HOST, PORT, TICK_INTERVAL_SEC, SNAPSHOT_INTERVAL_TICKS
from .simulation.world import world_state
from .api.routes_world  import router as world_router
from .api.routes_divine import router as divine_router
from .api.routes_warfare import router as warfare_router
from .api.websocket     import router as ws_router, broadcast
from .persistence.save_manager import save_manager


# ── BOUCLE TICK PERSISTANTE ──────────────────────────────────────────
async def simulation_loop():
    """
    Boucle infinie : 1 tick toutes les TICK_INTERVAL_SEC secondes.
    Tourne 24/7 indépendamment des connexions clients.
    """
    print(f"[Genesis] Simulation démarrée — 1 tick = {TICK_INTERVAL_SEC}s réels = {world_state.time.days_per_tick} jours simulés")
    while True:
        await asyncio.sleep(TICK_INTERVAL_SEC)
        try:
            await world_state.tick()

            # Snapshot périodique
            if world_state.time.tick % SNAPSHOT_INTERVAL_TICKS == 0:
                await save_manager.save_snapshot(world_state)
                print(f"[Genesis] Tick {world_state.time.tick} — An {world_state.time.year_bp} BP — "
                      f"Pop: {sum(t.population() for t in world_state.tribes if t.alive)} — "
                      f"E.div: {world_state.divine_energy:.1f}")

        except Exception as e:
            print(f"[Genesis] Erreur tick: {e}")
            import traceback
            traceback.print_exc()


# ── STARTUP / SHUTDOWN ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await save_manager.connect()
    world_state.initialize()
    world_state._broadcast_fn = broadcast

    # Tentative de restauration depuis DB
    saved = await save_manager.load_latest()
if saved:
    print(f"[Genesis] Restauration depuis snapshot (tick {saved.get('time',{}).get('tick','?')})")
    world_state.from_snapshot(saved)  # ← remplace le commentaire

    # Lance la boucle
    task = asyncio.create_task(simulation_loop())

    yield  # Application en route

    # Shutdown
    task.cancel()
    await save_manager.save_snapshot(world_state)
    print("[Genesis] Simulation sauvegardée. Au revoir.")


# ── APPLICATION ──────────────────────────────────────────────────────
app = FastAPI(
    title="Genesis Engine API",
    description="Simulateur civilisationnel métaphysique persistant.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # En prod : restreindre à ton domaine
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(world_router)
app.include_router(divine_router)
app.include_router(ws_router)
app.include_router(warfare_router)


@app.get("/")
async def root():
    return {
        "name":    "Genesis Engine",
        "status":  "running",
        "tick":    world_state.time.tick,
        "year_bp": world_state.time.year_bp,
        "tribes":  sum(1 for t in world_state.tribes if t.alive),
    }


@app.get("/health")
async def health():
    return {"ok": True}


# ── LANCEMENT DIRECT ─────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host=HOST, port=PORT, reload=False)
