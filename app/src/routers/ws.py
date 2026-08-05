# fastapi
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# app
from app.core.security import decode_access_token
from app.src.services.ws_manager import ws_manager


router = APIRouter(prefix="/api", tags=["ws"])


@router.websocket("/ws/orders")
async def orders_ws(websocket: WebSocket, token: str = "") -> None:
    # El navegador no manda headers al abrir el WS: el token va por query param
    if not decode_access_token(token):
        await websocket.close(code=1008)  # policy violation
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantiene viva la conexión; el cliente no necesita enviar nada
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:  # noqa: BLE001
        ws_manager.disconnect(websocket)
