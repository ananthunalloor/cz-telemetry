import time
import math
import logging
import struct
import serial
from typing import Optional
from PyQt6 import QtCore

PORT = "COM3"
BAUD = 115200
TIMEOUT = 1.0

START_MARKER = b"\x02"
END_MARKER = b"\x03"

# header, timestamp, temp, pressure, altitude, crc
TELEMETRY_PACKET_FORMAT = "<H I f f f B"
PACKET_SIZE = struct.calcsize(TELEMETRY_PACKET_FORMAT)

logger = logging.getLogger(__name__)


class Telemetry(QtCore.QObject):
    telemetry = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.0):
        super().__init__()
        logger.info("Initializing Telemetry")

        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._running = False
        self._ser: Optional[serial.Serial] = None

    def _compute_checksum(self, packet_bytes: bytes) -> int:
        return sum(packet_bytes[:-1]) & 0xFF

    def _read_exact(self, ser: serial.Serial, n: int) -> bytes:
        buf = bytearray()
        start = time.monotonic()
        timeout = ser.timeout if ser.timeout is not None else math.inf
        while len(buf) < n and self._running:
            chunk = ser.read(n - len(buf))
            if not chunk:
                if (time.monotonic() - start) >= timeout:
                    logger.error("Timeout while reading from serial")
                continue
            buf.extend(chunk)
        if len(buf) < n:
            logger.error("Timeout while reading exact bytes")
        return bytes(buf)

    def run(self):
        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            self._running = True
            logger.info("Opened serial port %s @ %d", self.port, self.baud)
        except Exception as e:
            self._ser = None
            logger.warning("Failed to open serial port %s: %s", self.port, e)

        ser = self._ser
        try:
            while self._running:
                if ser is None:
                    return

                b = ser.read(1)
                logger.info(b)
                if not b:
                    continue
                if b != START_MARKER:
                    continue

                try:
                    packet_bytes = self._read_exact(ser, PACKET_SIZE)
                except TimeoutError:
                    logger.warning("Timeout reading packet body, resyncing")
                    continue

                end = ser.read(1)
                if not end:
                    logger.warning("Timeout reading end marker, resyncing")
                    continue
                if end != END_MARKER:
                    logger.warning(
                        "Bad end marker (expected %s got %s), resyncing",
                        END_MARKER,
                        end,
                    )
                    continue

                received_crc = packet_bytes[-1]
                calc_crc = self._compute_checksum(packet_bytes)
                if received_crc != calc_crc:
                    logger.warning(
                        "CRC mismatch: received=%02X calc=%02X, discarding packet",
                        received_crc,
                        calc_crc,
                    )
                    continue

                try:
                    header, timestamp, temperature, pressure, altitude, crc = (
                        struct.unpack(TELEMETRY_PACKET_FORMAT, packet_bytes)
                    )
                    telemetry = {
                        "header": header,
                        "timestamp": timestamp,
                        "temperature": temperature,
                        "pressure": pressure,
                        "altitude": altitude,
                        "crc": crc,
                    }
                    self.telemetry.emit(telemetry)
                    # logger.info("Received Data: %s", altitude)
                except struct.error as e:
                    logger.error("Struct unpack error: %s", e)
                    continue

        except Exception as e:
            logger.error("Serial reading error: %s", e)

        finally:
            try:
                if ser and ser.is_open:
                    ser.close()
                    ser = None
                    self._ser = ser
                    self._running = False
                    logger.info("Closed open serial port")

            except Exception as e:
                logger.error("Failed to Closed serial port: %s", e)

            self.finished.emit()

    def stop(self):
        logger.info("Stopping Telemetry")
        self._running = False
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
                logger.info("Closed serial port")
        except Exception as e:
            logger.error("Failed to Closed serial port: %s", e)


()
