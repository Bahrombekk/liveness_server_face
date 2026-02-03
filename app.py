from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import numpy as np
import cv2
import base64
import time

from liveness.detector import detect_landmarks
from liveness.head_pose import estimate_pose
from liveness.challenge import new_challenge, check, is_centered
from liveness.session import create_session, get_session, update_session

app = FastAPI(title="Liveness Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    """API haqida ma'lumot"""
    return {
        "name": "Liveness Detection API",
        "version": "1.0",
        "websocket": "/ws",
        "docs": "/docs",
        "test": "/test"
    }

@app.get("/test")
def test_page():
    """Test sahifasi"""
    return FileResponse("test.html")

@app.post("/start")
def start():
    sid = create_session()
    challenge = new_challenge()
    update_session(sid, {"challenge": challenge})
    return {"session_id": sid, "challenge": challenge}

@app.post("/frame")
def frame(session_id: str, file: UploadFile = File(...)):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # Read image
    data = np.frombuffer(file.file.read(), np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Invalid image")

    # Detect landmarks
    lm = detect_landmarks(img)
    if lm is None:
        return {"status": "NO_FACE"}

    # Head pose
    yaw, pitch = estimate_pose(lm, img.shape[1], img.shape[0])

    # Check challenge
    ok = check(session["challenge"], yaw, pitch)
    if ok:
        session["success"] += 1
        session["challenge"] = new_challenge()
        update_session(session_id, session)

    return {
        "yaw": yaw,
        "pitch": pitch,
        "challenge": session["challenge"],
        "success": session["success"],
        "live": session["success"] >= 2
    }

@app.websocket("/ws")
async def websocket_liveness(websocket: WebSocket):
    await websocket.accept()

    # State machine
    state = "WAITING_CENTER"
    success = 0
    challenge = None
    required_successes = 3

    # Anti-spoof: timeout va attempt limitlar
    challenge_start_time = None
    challenge_timeout = 5.0  # 5 soniya har bir challenge uchun
    wrong_attempts = 0
    max_wrong_attempts = 1  # 1 ta noto'g'ri harakat - fail
    session_start = time.time()
    session_timeout = 30.0  # umumiy sessiya timeout

    # Boshlang'ich ma'lumot yuborish
    await websocket.send_json({
        "type": "start",
        "state": state,
        "instruction": "CENTER",
        "success": success,
        "total": required_successes
    })

    try:
        while True:
            data = await websocket.receive_json()

            if "frame" not in data:
                await websocket.send_json({"type": "error", "message": "frame field required"})
                continue

            # Frame ni decode qilish
            try:
                img_data = base64.b64decode(data["frame"])
                img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid image data"})
                continue

            if img is None:
                await websocket.send_json({"type": "error", "message": "Could not decode image"})
                continue

            # Yuzni aniqlash
            lm = detect_landmarks(img)
            if lm is None:
                await websocket.send_json({
                    "type": "no_face",
                    "state": state,
                    "instruction": "CENTER" if state == "WAITING_CENTER" else challenge,
                    "success": success,
                    "total": required_successes
                })
                continue

            # Bosh holatini aniqlash
            yaw, pitch = estimate_pose(lm, img.shape[1], img.shape[0])
            centered = is_centered(yaw, pitch)

            # Session timeout tekshirish
            if time.time() - session_start > session_timeout:
                await websocket.send_json({
                    "type": "failed",
                    "reason": "timeout",
                    "message": "Vaqt tugadi! Qaytadan urinib ko'ring."
                })
                break

            # State machine logic
            if state == "WAITING_CENTER":
                if centered:
                    # Yuz markazda - challenge berish
                    challenge = new_challenge()
                    challenge_start_time = time.time()
                    wrong_attempts = 0
                    state = "WAITING_ACTION"
                    await websocket.send_json({
                        "type": "challenge",
                        "state": state,
                        "instruction": challenge,
                        "yaw": round(yaw, 2),
                        "pitch": round(pitch, 2),
                        "success": success,
                        "total": required_successes
                    })
                else:
                    await websocket.send_json({
                        "type": "waiting",
                        "state": state,
                        "instruction": "CENTER",
                        "yaw": round(yaw, 2),
                        "pitch": round(pitch, 2),
                        "success": success,
                        "total": required_successes
                    })

            elif state == "WAITING_ACTION":
                # Challenge timeout tekshirish
                if time.time() - challenge_start_time > challenge_timeout:
                    await websocket.send_json({
                        "type": "failed",
                        "reason": "challenge_timeout",
                        "message": f"'{challenge}' uchun vaqt tugadi!"
                    })
                    break

                if check(challenge, yaw, pitch):
                    # Challenge bajarildi!
                    success += 1

                    if success >= required_successes:
                        await websocket.send_json({
                            "type": "complete",
                            "state": "COMPLETE",
                            "instruction": "VERIFIED",
                            "yaw": round(yaw, 2),
                            "pitch": round(pitch, 2),
                            "success": success,
                            "total": required_successes,
                            "live": True
                        })
                        break
                    else:
                        state = "WAITING_CENTER"
                        await websocket.send_json({
                            "type": "success",
                            "state": state,
                            "instruction": "CENTER",
                            "yaw": round(yaw, 2),
                            "pitch": round(pitch, 2),
                            "success": success,
                            "total": required_successes
                        })
                else:
                    # Noto'g'ri yo'nalish - wrong attempt
                    wrong_direction = None
                    if abs(yaw) > 20 or abs(pitch) > 12:
                        wrong_attempts += 1
                        if yaw < -20:
                            wrong_direction = "LEFT"
                        elif yaw > 20:
                            wrong_direction = "RIGHT"
                        elif pitch < -12:
                            wrong_direction = "UP"
                        elif pitch > 12:
                            wrong_direction = "DOWN"

                    if wrong_attempts >= max_wrong_attempts:
                        await websocket.send_json({
                            "type": "failed",
                            "reason": "wrong_attempts",
                            "message": "Juda ko'p noto'g'ri harakat!"
                        })
                        break

                    await websocket.send_json({
                        "type": "waiting",
                        "state": state,
                        "instruction": challenge,
                        "yaw": round(yaw, 2),
                        "pitch": round(pitch, 2),
                        "success": success,
                        "total": required_successes,
                        "wrong_direction": wrong_direction
                    })

    except WebSocketDisconnect:
        pass
    finally:
        # WebSocket ni yopish
        try:
            await websocket.close()
        except:
            pass
