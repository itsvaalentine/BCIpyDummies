import asyncio
import json
import threading
import time
import os
import pytest
import websockets

from cortex.websocket_client import WebSocketClient

# ====================================================================
#     SERVIDOR FAKE PARA TEST UNITARIO
# ====================================================================

async def fake_cortex_server(websocket, path):
    """
    Simula un servidor Cortex para pruebas unitarias.
    Responde a "authorize", "ping" y cualquier método "custom".
    """
    async for msg in websocket:
        data = json.loads(msg)
        method = data.get("method")
        mid = data.get("id", 1)

        if method == "authorize":
            await websocket.send(json.dumps({"id": mid, "result": {"cortexToken": "FAKE_TOKEN"}}))

        elif method == "ping":
            await websocket.send(json.dumps({"id": mid, "result": "pong"}))

        else:
            await websocket.send(json.dumps({
                "id": mid,
                "result": {"echo": method, "params": data.get("params")}
            }))

def start_fake_server():
    """Ejecuta el servidor fake en un hilo separado."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(fake_cortex_server, "127.0.0.1", 8765)
    loop.run_until_complete(server)
    loop.run_forever()

@pytest.fixture(scope="module")
def fake_server():
    """Levanta servidor fake antes del test y lo apaga al terminar."""
    t = threading.Thread(target=start_fake_server, daemon=True)
    t.start()
    time.sleep(0.3)  # Give server time to start
    return True

# ====================================================================
#     TESTS UNITARIOS (USAN SERVIDOR FAKE)
# ====================================================================

@pytest.mark.unit
def test_ws_connect_and_authorize_fake(fake_server):
    client = WebSocketClient("ws://127.0.0.1:8765")
    responses = []

    client.on_message = lambda d: responses.append(d)

    client.connect()
    client.send_request("authorize", {"clientId": "X"}, id=1)

    timeout = time.time() + 3
    while not responses and time.time() < timeout:
        time.sleep(0.1)

    assert responses, "No response from fake server"
    assert responses[0]["result"]["cortexToken"] == "FAKE_TOKEN"

    client.close()

@pytest.mark.unit
def test_ws_ping(fake_server):
    client = WebSocketClient("ws://127.0.0.1:8765")
    responses = []
    client.on_message = lambda d: responses.append(d)

    client.connect()
    client.send_request("ping", {}, id=9)

    timeout = time.time() + 3
    while not responses and time.time() < timeout:
        time.sleep(0.1)

    assert responses[0]["result"] == "pong"
    client.close()

@pytest.mark.unit
def test_ws_custom_method(fake_server):
    client = WebSocketClient("ws://127.0.0.1:8765")
    responses = []
    client.on_message = lambda d: responses.append(d)

    client.connect()
    client.send_request("moveLeft", {"power": 0.9}, id=33)

    timeout = time.time() + 3
    while not responses:
        time.sleep(0.1)

    assert responses[0]["result"]["echo"] == "moveLeft"
    assert responses[0]["result"]["params"]["power"] == 0.9

    client.close()

@pytest.mark.unit
def test_ws_close(fake_server):
    client = WebSocketClient("ws://127.0.0.1:8765")
    client.connect()
    client.close()
    assert client.connected is False

# ====================================================================
#     TESTS CON EMOTIV REAL (SE SALTAN SI NO HAY DAEMON)
# ====================================================================

CLIENT_ID = os.getenv("EMOTIV_CLIENT_ID")
CLIENT_SECRET = os.getenv("EMOTIV_CLIENT_SECRET")
EMOTIV_URL = "wss://127.0.0.1:6868"

def emotiv_is_running():
    """Quick check: intenta abrir socket; si falla, no hay daemon."""
    try:
        import websocket
        ws = websocket.create_connection(EMOTIV_URL, timeout=1, sslopt={"cert_reqs": 0})
        ws.close()
        return True
    except:
        return False

@pytest.mark.integration
def test_real_emotiv_authorize():
    if not emotiv_is_running():
        pytest.skip("⚠️ Emotiv Cortex no está corriendo")

    if not (CLIENT_ID and CLIENT_SECRET):
        pytest.skip("⚠️ Variables de entorno EMOTIV_CLIENT_ID y EMOTIV_CLIENT_SECRET no configuradas")

    client = WebSocketClient(EMOTIV_URL)
    messages = []
    client.on_message = lambda d: messages.append(d)

    client.connect()

    client.send_request("authorize", {
        "clientId": CLIENT_ID,
        "clientSecret": CLIENT_SECRET,
        "debit": 0
    }, id=1)

    timeout = time.time() + 5
    while not messages and time.time() < timeout:
        time.sleep(0.2)

    assert messages, "No hubo respuesta de Emotiv"
    assert "result" in messages[0]
    assert "cortexToken" in messages[0]["result"]

    client.close()
    print("🎉 Token recibido OK:", messages[0]["result"]["cortexToken"][:16], "...")

@pytest.mark.integration
def test_real_emotiv_query_headsets():
    if not emotiv_is_running():
        pytest.skip("⚠️ Emotiv Cortex no está corriendo")

    if not (CLIENT_ID and CLIENT_SECRET):
        pytest.skip("⚠️ Credenciales Emotiv no configuradas")

    client = WebSocketClient(EMOTIV_URL)
    messages = []
    client.on_message = lambda d: messages.append(d)

    client.connect()

    # Autorizar
    client.send_request("authorize", {
        "clientId": CLIENT_ID,
        "clientSecret": CLIENT_SECRET,
        "debit": 0
    }, id=1)

    time.sleep(1)

    # Query headsets
    client.send_request("queryHeadsets", {}, id=2)

    timeout = time.time() + 5
    while len(messages) < 2 and time.time() < timeout:
        time.sleep(0.2)

    assert len(messages) >= 2
    assert "result" in messages[1]

    client.close()

