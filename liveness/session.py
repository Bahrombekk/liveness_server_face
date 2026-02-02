import time
import uuid

# Simple in-memory session storage
_sessions = {}

def create_session():
    sid = str(uuid.uuid4())
    _sessions[sid] = {
        "challenge": None,
        "success": 0,
        "created": time.time(),
        "updated": time.time()
    }
    return sid

def get_session(sid):
    return _sessions.get(sid)

def update_session(sid, data):
    if sid in _sessions:
        _sessions[sid].update(data)
        _sessions[sid]["updated"] = time.time()
