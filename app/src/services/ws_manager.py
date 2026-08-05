"""Manager mínimo de conexiones WebSocket para avisar cambios de pedidos.

El listener de Firestore corre en un hilo aparte; usa notify() (thread-safe)
para avisar a los clientes conectados que deben refrescar.
"""

import asyncio

from fastapi import WebSocket


class WsManager:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    def notify(self, message: str = "orders") -> None:
        # Se puede llamar desde cualquier hilo (ej. el callback de Firestore)
        if self._loop is None or not self._clients:
            return
        self._loop.call_soon_threadsafe(
            lambda: asyncio.create_task(self._broadcast(message))
        )

    async def _broadcast(self, message: str) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)


ws_manager = WsManager()
