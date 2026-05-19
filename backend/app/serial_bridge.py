import asyncio
import logging
from typing import Optional
import serial

logger = logging.getLogger(__name__)


class SerialBridge:
    """Transparent serial bridge with sticky-packet (framing) support.

    If `delimiter` is provided, packets are split by delimiter and forwarded packet by packet.
    Otherwise, raw chunks are forwarded directly.
    """

    def __init__(self, port: str, baudrate: int, timeout: float = 0.1, delimiter: Optional[bytes] = b"\n"):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.delimiter = delimiter
        self._ser: Optional[serial.Serial] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def open(self):
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        logger.info("Serial opened: %s @ %s", self.port, self.baudrate)

    def close(self):
        self._running = False
        if self._task:
            self._task.cancel()
        if self._ser and self._ser.is_open:
            self._ser.close()
        logger.info("Serial closed")

    async def write(self, payload: bytes):
        if not self._ser or not self._ser.is_open:
            self.open()
        self._ser.write(payload)

    async def start_read_loop(self, on_packet):
        self.open()
        self._running = True
        buf = bytearray()
        while self._running:
            await asyncio.sleep(0)
            data = await asyncio.to_thread(self._ser.read, 1024)
            if not data:
                continue

            if self.delimiter is None:
                await on_packet(bytes(data))
                continue

            buf.extend(data)
            while True:
                idx = buf.find(self.delimiter)
                if idx < 0:
                    break
                packet = bytes(buf[: idx + len(self.delimiter)])
                del buf[: idx + len(self.delimiter)]
                await on_packet(packet)
