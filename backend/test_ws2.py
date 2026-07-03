import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/ws/agent/dynamic"
    headers = {"Origin": "http://localhost:5173"}
    async with websockets.connect(uri, additional_headers=headers) as ws:
        await ws.send(json.dumps({"goal": "Plan a weekend trip to Goa with flights, a hotel, and weather check"}))
        async for message in ws:
            data = json.loads(message)
            print(f"[{data['type']}]", json.dumps(data, indent=2)[:300])
            if data["type"] in ("done", "error"):
                break

asyncio.run(test())
