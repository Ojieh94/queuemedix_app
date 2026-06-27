from typing import Dict, List
import uuid
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # { channel: { room_id: [websockets...] } }
        self.active_connections: Dict[uuid.UUID, Dict[uuid.UUID, List[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, channel: uuid.UUID, room_id: uuid.UUID):
        """Accept connection and register it under channel + room"""
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = {}

        if room_id not in self.active_connections[channel]:
            self.active_connections[channel][room_id] = []

        self.active_connections[channel][room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, channel: uuid.UUID, room_id: uuid.UUID):
        """Remove connection from channel + room"""
        if channel in self.active_connections and room_id in self.active_connections[channel]:
            self.active_connections[channel][room_id].remove(websocket)

            if not self.active_connections[channel][room_id]:
                del self.active_connections[channel][room_id]

            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def broadcast(self, channel: uuid.UUID, room_id: uuid.UUID, message: dict):
        """Send a message to all clients in channel + room"""
        if channel in self.active_connections and room_id in self.active_connections[channel]:
            for connection in self.active_connections[channel][room_id]:
                await connection.send_json(message)


# Global manager instance
manager = ConnectionManager()
