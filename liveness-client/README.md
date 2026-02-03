# Liveness Detection - Frontend Client

Face liveness detection client that connects to the Liveness Detection API via WebSocket.

## How it works

1. User clicks "Start Verification"
2. Camera opens and connects to WebSocket server
3. Server sends 3 random challenges (turn head LEFT, RIGHT, UP, DOWN)
4. User completes all 3 challenges → verified as a real person

## Files

```
liveness-client/
├── index.html          # Main page
├── css/
│   └── liveness.css    # Styles
├── js/
│   └── liveness.js     # Liveness module
└── README.md
```

## Quick Start

```bash
# Serve with any HTTP server
python3 -m http.server 8080

# Open in browser
# http://localhost:8080
```

> **Note:** HTTPS is required for camera access on mobile browsers.

## Integration

### Basic Usage

Add these files to your project and include them in your HTML:

```html
<link rel="stylesheet" href="css/liveness.css">
<script src="js/liveness.js"></script>
```

Add the container HTML:

```html
<div class="liveness-container" id="livenessContainer">
    <h2 class="liveness-title">Face Verification</h2>

    <div class="liveness-progress">
        <div class="liveness-dot" id="dot0"></div>
        <div class="liveness-dot" id="dot1"></div>
        <div class="liveness-dot" id="dot2"></div>
    </div>

    <div class="liveness-instruction" id="instruction">Click "Start" to begin</div>

    <div class="liveness-video-wrap" id="videoWrap">
        <video id="video" autoplay playsinline></video>
        <div class="liveness-oval"></div>
    </div>

    <div class="liveness-status" id="status"></div>

    <button class="liveness-btn" id="startBtn" onclick="LivenessCheck.start()">
        Start Verification
    </button>

    <canvas id="canvas" style="display:none"></canvas>
</div>
```

Initialize with your config:

```html
<script>
LivenessCheck.init({
    wsUrl: 'wss://face-check.das-uty.uz/ws',
    containerId: 'livenessContainer',
    onSuccess: function () {
        // User verified - call your backend
        fetch('/api/verify', { method: 'POST' });
    },
    onFail: function (reason, message) {
        // Verification failed
        console.log('Failed:', reason, message);
    }
});
</script>
```

### Custom Labels (e.g. Uzbek)

```js
LivenessCheck.init({
    wsUrl: 'wss://face-check.das-uty.uz/ws',
    labels: {
        CENTER: 'Kameraga qarang',
        LEFT:   'Chapga buriling',
        RIGHT:  "O'ngga buriling",
        UP:     'Yuqoriga qarang',
        DOWN:   'Pastga qarang'
    },
    onSuccess: function () { },
    onFail: function () { }
});
```

## API

| Method | Description |
|---|---|
| `LivenessCheck.init(config)` | Initialize with config |
| `LivenessCheck.start()` | Start verification |
| `LivenessCheck.stop()` | Cancel verification |
| `LivenessCheck.retry()` | Retry after fail/success |

### Config Options

| Option | Type | Description |
|---|---|---|
| `wsUrl` | string | WebSocket URL (required) |
| `containerId` | string | Container element ID |
| `labels` | object | Custom instruction labels |
| `onSuccess` | function | Called when verification passes |
| `onFail` | function(reason, message) | Called when verification fails |

### Failure Reasons

| Reason | Description |
|---|---|
| `timeout` | Session exceeded 30 seconds |
| `challenge_timeout` | Single challenge exceeded 5 seconds |
| `wrong_attempts` | User moved head in wrong direction |

## WebSocket Protocol

Client sends:
```json
{ "frame": "<base64 encoded JPEG>" }
```

Server responds with `type`:
- `start` — session started, begin sending frames
- `no_face` — no face detected
- `challenge` — new challenge (LEFT/RIGHT/UP/DOWN)
- `waiting` — face detected, waiting for correct pose
- `success` — one challenge passed
- `complete` — all 3 passed, `live: true`
- `failed` — verification failed
