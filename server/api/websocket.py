"""
GENESIS ENGINE — api/websocket.py
WebSocket temps réel : le serveur pousse les mises à jour au client.
Le client n'a pas besoin de poller — il reçoit chaque tick automatiquement.
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

# Pool de connexions actives
_connections: set[WebSocket] = set()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _connections.add(ws)
    try:
        # Envoyer l'état initial immédiatement
        from ..simulation.world import world_state
        await ws.send_text(json.dumps({
            "type": "init",
            "data": world_state.to_snapshot(),
        }))
        # Garder la connexion ouverte
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                # Pour l'instant on ignore les messages client (actions via REST)
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(ws)


async def broadcast(data: dict):
    """Appelée à chaque tick pour pousser l'état à tous les clients connectés."""
    if not _connections:
        return
    msg = json.dumps({"type": "tick", "data": data})
    dead = set()
    for ws in _connections:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _connections -= dead
