# Liveness Detection API

Real-time face liveness detection using MediaPipe and head pose estimation.

## Features

- WebSocket-based real-time face verification
- Challenge-response system (LEFT, RIGHT, UP, DOWN)
- Anti-spoofing protection:
  - Session timeout (30s)
  - Challenge timeout (5s per challenge)
  - Wrong attempt detection
- No external API dependencies

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Start Server

```bash
# Development
uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# Production
uvicorn app:app --host 0.0.0.0 --port 8001 --workers 4
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/test` | GET | Test page (demo) |
| `/docs` | GET | Swagger documentation |
| `/ws` | WebSocket | Liveness verification |

## WebSocket API

### Connect
```
ws://your-server:8001/ws
```

### Flow

1. **Server sends start message:**
```json
{
  "type": "start",
  "state": "WAITING_CENTER",
  "instruction": "CENTER",
  "success": 0,
  "total": 3
}
```

2. **Client sends frame (base64 JPEG):**
```json
{
  "frame": "base64_encoded_jpeg_image"
}
```

3. **Server responses:**

| Type | Description |
|------|-------------|
| `waiting` | Waiting for user action |
| `challenge` | New direction challenge |
| `success` | Challenge completed |
| `complete` | All challenges passed - LIVE |
| `failed` | Verification failed |
| `no_face` | No face detected |

### Response Format
```json
{
  "type": "waiting|challenge|success|complete|failed",
  "state": "WAITING_CENTER|WAITING_ACTION|COMPLETE",
  "instruction": "CENTER|LEFT|RIGHT|UP|DOWN|VERIFIED",
  "yaw": -15.5,
  "pitch": 3.2,
  "success": 1,
  "total": 3,
  "live": false,
  "wrong_direction": "LEFT"
}
```

## Client Integration

### JavaScript (Web)

```javascript
// 1. WebSocket ulanish
const ws = new WebSocket("ws://your-server:8001/ws");

// 2. Kamerani ochish
const video = document.getElementById('video');
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');

navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
  .then(stream => {
    video.srcObject = stream;
    canvas.width = 640;
    canvas.height = 480;
  });

// 3. Server xabarlarini qabul qilish
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);

  switch(data.type) {
    case "start":
      // Frame yuborishni boshlash
      setInterval(() => sendFrame(), 150);
      break;

    case "challenge":
      // Yo'nalishni ko'rsatish: data.instruction = LEFT|RIGHT|UP|DOWN
      showDirection(data.instruction);
      break;

    case "success":
      // Challenge bajarildi, markazga qaytish kerak
      showMessage("Yaxshi! Markazga qarang");
      break;

    case "complete":
      // Muvaffaqiyat!
      if (data.live) {
        alert("Tasdiqlandi!");
      }
      break;

    case "failed":
      // Muvaffaqiyatsiz
      alert(data.message);
      break;

    case "no_face":
      // Yuz topilmadi
      showMessage("Yuz topilmadi");
      break;
  }
};

// 4. Frame yuborish funksiyasi
function sendFrame() {
  ctx.drawImage(video, 0, 0, 640, 480);
  const base64 = canvas.toDataURL("image/jpeg", 0.6).split(",")[1];
  ws.send(JSON.stringify({ frame: base64 }));
}
```

### React Native / Mobile

```javascript
import { Camera } from 'expo-camera';

const ws = new WebSocket("ws://your-server:8001/ws");

// Kameradan rasm olish va yuborish
const takePicture = async () => {
  const photo = await cameraRef.current.takePictureAsync({
    base64: true,
    quality: 0.6
  });
  ws.send(JSON.stringify({ frame: photo.base64 }));
};

ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  // ... handle messages
};
```

### Flutter / Dart

```dart
import 'package:web_socket_channel/web_socket_channel.dart';

final channel = WebSocketChannel.connect(
  Uri.parse('ws://your-server:8001/ws'),
);

// Frame yuborish
void sendFrame(String base64Image) {
  channel.sink.add(jsonEncode({'frame': base64Image}));
}

// Xabarlarni tinglash
channel.stream.listen((message) {
  final data = jsonDecode(message);
  switch (data['type']) {
    case 'challenge':
      // data['instruction'] = LEFT|RIGHT|UP|DOWN
      break;
    case 'complete':
      if (data['live']) print('Tasdiqlandi!');
      break;
    case 'failed':
      print(data['message']);
      break;
  }
});
```

### Python Client

```python
import asyncio
import websockets
import base64
import cv2
import json

async def liveness_check():
    async with websockets.connect("ws://your-server:8001/ws") as ws:
        cap = cv2.VideoCapture(0)

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if data['type'] == 'complete':
                print("Tasdiqlandi!" if data['live'] else "Rad etildi")
                break

            if data['type'] == 'failed':
                print(f"Xato: {data['message']}")
                break

            # Frame yuborish
            ret, frame = cap.read()
            _, buffer = cv2.imencode('.jpg', frame)
            base64_image = base64.b64encode(buffer).decode()
            await ws.send(json.dumps({'frame': base64_image}))

asyncio.run(liveness_check())
```

## Configuration

Edit `app.py` to change:

```python
required_successes = 3      # Number of challenges
challenge_timeout = 5.0     # Seconds per challenge
session_timeout = 30.0      # Total session time
max_wrong_attempts = 1      # Wrong attempts before fail
```

## Project Structure

```
liveness_server_face/
├── app.py                 # FastAPI application
├── test.html              # Demo test page
├── requirements.txt
├── README.md
└── liveness/
    ├── detector.py        # Face landmark detection
    ├── head_pose.py       # Head pose estimation
    ├── challenge.py       # Challenge logic
    └── session.py         # Session management
```

## License

MIT
