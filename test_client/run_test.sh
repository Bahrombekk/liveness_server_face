#!/bin/bash

# Test client - lokal test uchun
# Bu skript HTTPS server ishga tushiradi (kamera uchun kerak)

IP=$(hostname -I | awk '{print $1}')
PORT=8443

echo "========================================"
echo "  Face ID - Test Client"
echo "========================================"
echo ""
echo "1-TERMINAL: Backend server ishga tushiring:"
echo "   cd $(dirname $(realpath $0))/.. && ./run.sh"
echo ""
echo "2-TERMINAL (shu): Test client ishga tushadi"
echo ""
echo "Telefonda Chrome flag yoqing:"
echo "   chrome://flags/#unsafely-treat-insecure-origin-as-secure"
echo "   http://${IP}:${PORT} yozing va Enable qiling"
echo ""
echo "Keyin telefondan oching:"
echo "   http://${IP}:${PORT}"
echo ""
echo "========================================"
echo ""

cd "$(dirname "$0")"
python3 -m http.server $PORT --bind 0.0.0.0
