/**
 * ============================================
 *  LivenessCheck - Face Liveness Detection
 * ============================================
 *
 *  Usage:
 *
 *    LivenessCheck.init({
 *        wsUrl: 'wss://face-check.das-uty.uz/ws',
 *        containerId: 'livenessContainer',
 *        onSuccess: function() { ... },
 *        onFail: function(reason, message) { ... }
 *    });
 *
 *    LivenessCheck.start();   // start verification
 *    LivenessCheck.stop();    // cancel verification
 *
 * ============================================
 */

var LivenessCheck = (function () {

    // ---- Config ----
    var config = {
        wsUrl: '',
        containerId: '',
        frameInterval: 150,
        jpegQuality: 0.6,
        onSuccess: function () {},
        onFail: function () {}
    };

    // ---- Labels (change for your language) ----
    var LABELS = {
        CENTER: 'Look at the camera',
        LEFT:   'Turn head LEFT',
        RIGHT:  'Turn head RIGHT',
        UP:     'Look UP',
        DOWN:   'Look DOWN'
    };

    // ---- Internal state ----
    var ws = null;
    var streaming = false;
    var cameraStream = null;
    var video, canvas, ctx;
    var instrEl, statusEl, videoWrap, startBtn;
    var dots = [];

    // ============================================
    //  Init - call once on page load
    // ============================================
    function init(opts) {
        config.wsUrl       = opts.wsUrl       || config.wsUrl;
        config.containerId = opts.containerId || config.containerId;
        config.onSuccess   = opts.onSuccess   || config.onSuccess;
        config.onFail      = opts.onFail      || config.onFail;

        if (opts.labels) {
            for (var k in opts.labels) LABELS[k] = opts.labels[k];
        }

        // Cache DOM elements
        video     = document.getElementById('video');
        canvas    = document.getElementById('canvas');
        ctx       = canvas.getContext('2d');
        instrEl   = document.getElementById('instruction');
        statusEl  = document.getElementById('status');
        videoWrap = document.getElementById('videoWrap');
        startBtn  = document.getElementById('startBtn');
        dots      = [
            document.getElementById('dot0'),
            document.getElementById('dot1'),
            document.getElementById('dot2')
        ];
    }

    // ============================================
    //  Start verification
    // ============================================
    function start() {
        startBtn.disabled = true;
        startBtn.style.display = 'none';
        removeOverlay();
        resetUI();
        startCamera();
    }

    // ============================================
    //  Stop / cancel
    // ============================================
    function stop() {
        streaming = false;
        if (ws) { ws.close(); ws = null; }
        stopCamera();
        startBtn.disabled = false;
        startBtn.style.display = '';
    }

    // ============================================
    //  Camera
    // ============================================
    function startCamera() {
        navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: 640, height: 480 }
        })
        .then(function (stream) {
            cameraStream = stream;
            video.srcObject = stream;
            video.onloadedmetadata = function () {
                canvas.width  = video.videoWidth;
                canvas.height = video.videoHeight;
                connectWS();
            };
        })
        .catch(function (err) {
            statusEl.textContent = 'Camera error: ' + err.message;
            statusEl.className = 'liveness-status error';
            startBtn.disabled = false;
            startBtn.style.display = '';
        });
    }

    function stopCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(function (t) { t.stop(); });
            cameraStream = null;
            video.srcObject = null;
        }
    }

    // ============================================
    //  WebSocket
    // ============================================
    function connectWS() {
        ws = new WebSocket(config.wsUrl);

        ws.onopen = function () {
            statusEl.textContent = 'Connected...';
            statusEl.className = 'liveness-status';
        };

        ws.onmessage = function (event) {
            var data = JSON.parse(event.data);
            handleMessage(data);
            if (streaming && data.type !== 'complete' && data.type !== 'failed') {
                setTimeout(sendFrame, config.frameInterval);
            }
        };

        ws.onerror = function () {
            statusEl.textContent = 'Connection error';
            statusEl.className = 'liveness-status error';
        };

        ws.onclose = function () {
            streaming = false;
        };
    }

    // ============================================
    //  Send frame
    // ============================================
    function sendFrame() {
        if (!streaming || !ws || ws.readyState !== WebSocket.OPEN) return;
        ctx.drawImage(video, 0, 0);
        var base64 = canvas.toDataURL('image/jpeg', config.jpegQuality).split(',')[1];
        ws.send(JSON.stringify({ frame: base64 }));
    }

    // ============================================
    //  Handle server message
    // ============================================
    function handleMessage(data) {
        var instr = data.instruction || 'CENTER';
        updateDots(data.success || 0);

        switch (data.type) {

            case 'start':
                streaming = true;
                instrEl.textContent = LABELS.CENTER;
                statusEl.textContent = 'Position your face in the oval';
                statusEl.className = 'liveness-status';
                videoWrap.className = 'liveness-video-wrap';
                sendFrame();
                break;

            case 'no_face':
                instrEl.textContent = LABELS.CENTER;
                statusEl.textContent = 'No face detected';
                statusEl.className = 'liveness-status error';
                videoWrap.className = 'liveness-video-wrap';
                break;

            case 'waiting':
                instrEl.textContent = LABELS[instr] || instr;
                if (data.wrong_direction) {
                    statusEl.textContent = 'Wrong direction! ' + (LABELS[instr] || instr);
                    statusEl.className = 'liveness-status error';
                } else {
                    statusEl.textContent = data.state === 'WAITING_CENTER'
                        ? 'Center your face' : 'Move your head as shown';
                    statusEl.className = 'liveness-status';
                }
                videoWrap.className = data.state === 'WAITING_ACTION'
                    ? 'liveness-video-wrap active' : 'liveness-video-wrap';
                break;

            case 'challenge':
                instrEl.textContent = LABELS[instr] || instr;
                statusEl.textContent = 'Move your head now!';
                statusEl.className = 'liveness-status';
                videoWrap.className = 'liveness-video-wrap active';
                break;

            case 'success':
                instrEl.textContent = LABELS.CENTER;
                statusEl.textContent = 'Good! Look back at the camera';
                statusEl.className = 'liveness-status';
                videoWrap.className = 'liveness-video-wrap ok';
                break;

            case 'complete':
                streaming = false;
                stopCamera();
                if (ws) ws.close();
                showResult(true, 'Liveness Verified!');
                config.onSuccess();
                break;

            case 'failed':
                streaming = false;
                stopCamera();
                if (ws) ws.close();
                showResult(false, data.message || 'Verification failed');
                config.onFail(data.reason, data.message);
                break;
        }
    }

    // ============================================
    //  UI Helpers
    // ============================================
    function updateDots(passed) {
        dots.forEach(function (dot, i) {
            dot.className = 'liveness-dot';
            if (i < passed) dot.classList.add('done');
            else if (i === passed) dot.classList.add('current');
        });
    }

    function resetUI() {
        instrEl.textContent = 'Initializing...';
        statusEl.textContent = '';
        statusEl.className = 'liveness-status';
        videoWrap.className = 'liveness-video-wrap';
        dots.forEach(function (d) { d.className = 'liveness-dot'; });
    }

    function showResult(ok, text) {
        var overlay = document.createElement('div');
        overlay.className = 'liveness-overlay ' + (ok ? 'success' : 'fail');
        overlay.id = 'livenessOverlay';
        overlay.innerHTML =
            '<div class="icon">' + (ok ? '&#10004;' : '&#10008;') + '</div>' +
            '<div>' + text + '</div>' +
            '<button onclick="LivenessCheck.retry()">Try again</button>';
        document.body.appendChild(overlay);
    }

    function removeOverlay() {
        var el = document.getElementById('livenessOverlay');
        if (el) el.remove();
    }

    function retry() {
        removeOverlay();
        start();
    }

    // ============================================
    //  Public API
    // ============================================
    return {
        init:  init,
        start: start,
        stop:  stop,
        retry: retry
    };

})();
