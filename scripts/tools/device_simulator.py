#!/usr/bin/env python3
"""Simulate ESP32 devices against the backend WebSocket protocol."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time

import websockets

PROTOCOL_VERSION = "1"


async def run_device(base_url: str, device_id: str, event_rate: float) -> None:
    async with websockets.connect(f"{base_url}/ws/devices/{device_id}") as ws:
        await ws.send(
            json.dumps(
                {
                    "version": PROTOCOL_VERSION,
                    "type": "register",
                    "device_id": device_id,
                    "payload": {
                        "firmware_version": "simulator",
                        "board_target": "python",
                    },
                }
            )
        )
        heartbeat = asyncio.create_task(_heartbeat(ws, device_id))
        events = asyncio.create_task(_events(ws, device_id, event_rate))
        try:
            await asyncio.gather(heartbeat, events)
        finally:
            heartbeat.cancel()
            events.cancel()


async def _heartbeat(ws, device_id: str) -> None:
    while True:
        await asyncio.sleep(5)
        await ws.send(
            json.dumps(
                {
                    "version": PROTOCOL_VERSION,
                    "type": "heartbeat",
                    "device_id": device_id,
                    "payload": {"timestamp_ms": int(time.monotonic() * 1000)},
                }
            )
        )


async def _events(ws, device_id: str, event_rate: float) -> None:
    delay = 1 / event_rate if event_rate > 0 else 1
    sequence = 0
    while True:
        await asyncio.sleep(delay)
        sequence += 1
        await ws.send(
            json.dumps(
                {
                    "version": PROTOCOL_VERSION,
                    "type": "event",
                    "device_id": device_id,
                    "payload": {
                        "event_type": random.choice(["button", "tap", "answer", "input"]),
                        "dedupe_key": f"{device_id}-{sequence}",
                        "timestamp_ms": int(time.monotonic() * 1000),
                        "elapsed_ms": random.randint(250, 2500),
                        "correct": random.random() > 0.2,
                    },
                }
            )
        )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ws://127.0.0.1:8000")
    parser.add_argument("--devices", type=int, default=5)
    parser.add_argument("--events-per-second", type=float, default=1.0)
    args = parser.parse_args()
    await asyncio.gather(
        *[
            run_device(args.url, f"sim-{index + 1:02d}", args.events_per_second)
            for index in range(args.devices)
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
