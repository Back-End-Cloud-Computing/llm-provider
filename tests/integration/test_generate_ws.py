import json

from starlette.testclient import TestClient

from app.main import app


def test_generate_ws_streams_chunks_then_done():
    with TestClient(app).websocket_connect("/generate/ws") as websocket:
        websocket.send_text(json.dumps({"prompt": "descreva um produto"}))

        events = []
        while True:
            event = websocket.receive_json()
            events.append(event)
            if event["type"] in ("done", "error"):
                break

    assert events[-1]["type"] == "done"
    chunk_events = [e for e in events if e["type"] == "chunk"]
    assert len(chunk_events) >= 1
    assert events[-1]["text"] == "".join(e["text"] for e in chunk_events)
    assert events[-1]["provider"] == "mock"


def test_generate_ws_rejects_malformed_payload():
    with TestClient(app).websocket_connect("/generate/ws") as websocket:
        websocket.send_text("not json")
        event = websocket.receive_json()

    assert event["type"] == "error"
