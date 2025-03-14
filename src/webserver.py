from flask import Flask, send_from_directory
import os
import asyncio
import websockets

PORT = int(os.getenv("PORT", 8098))  # Read from environment variable
WS_PORT = PORT + 1  # Use a different port for WebSocket

app = Flask(__name__)

@app.route('/')
def serve_index():
    return send_from_directory("static", "index.html")

async def log_handler(websocket, path):
    while True:
        await asyncio.sleep(1)  # Keep connection open

async def run_websocket():
    async with websockets.serve(log_handler, "0.0.0.0", WS_PORT):
        await asyncio.Future()  # Keep server running

if __name__ == "__main__":
    import threading

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT), daemon=True).start()
    asyncio.run(run_websocket())
