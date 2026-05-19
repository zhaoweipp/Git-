import asyncio
import base64
import logging
from apiflask import APIFlask
import socketio

from .config import (
    SERIAL_BAUDRATE,
    SERIAL_PORT,
    SERIAL_TIMEOUT,
    SOCKETIO_PING_INTERVAL,
    SOCKETIO_PING_TIMEOUT,
)
from .serial_bridge import SerialBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = APIFlask(__name__)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    ping_interval=SOCKETIO_PING_INTERVAL,
    ping_timeout=SOCKETIO_PING_TIMEOUT,
)
flask_app = app.wsgi_app
asgi_app = socketio.ASGIApp(sio, flask_app)

serial_bridge = SerialBridge(
    port=SERIAL_PORT,
    baudrate=SERIAL_BAUDRATE,
    timeout=SERIAL_TIMEOUT,
    delimiter=b"\n",  # configurable framing for sticky packet handling
)

pending_ack = {}


def encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode_bytes(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


@app.get("/health")
def health():
    return {"ok": True}


@sio.event
async def connect(sid, environ, auth):
    logger.info("client connected: %s", sid)


@sio.event
async def disconnect(sid):
    logger.info("client disconnected: %s", sid)


@sio.event
async def frontend_to_serial(sid, message):
    """
    message example:
    {
      "trace_id": "xxx",
      "client_id": "unique-client",
      "payload_b64": "..."
    }
    """
    trace_id = message.get("trace_id")
    payload = decode_bytes(message["payload_b64"])
    await serial_bridge.write(payload)

    if trace_id:
        pending_ack[trace_id] = asyncio.get_event_loop().time()

    await sio.emit("ack", {"trace_id": trace_id, "status": "sent"}, to=sid)


@sio.event
async def ack(sid, message):
    trace_id = message.get("trace_id")
    if trace_id in pending_ack:
        pending_ack.pop(trace_id, None)


async def serial_packet_callback(packet: bytes):
    await sio.emit(
        "serial_to_frontend",
        {
            "payload_b64": encode_bytes(packet),
        },
    )


async def startup_background():
    while True:
        try:
            await serial_bridge.start_read_loop(serial_packet_callback)
        except Exception as e:
            logger.exception("serial read loop crashed, reconnecting: %s", e)
            await asyncio.sleep(2)


@sio.event
async def heartbeat(sid, message):
    await sio.emit("heartbeat", {"ts": message.get("ts")}, to=sid)


loop = asyncio.get_event_loop()
loop.create_task(startup_background())
