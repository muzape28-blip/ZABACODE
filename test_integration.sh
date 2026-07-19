#!/bin/bash
# Zabacode Test Suite

echo "🧪 Zabacode Test Suite"
echo "======================"

# Test 1: Sandbox Security
echo ""
echo "[TEST 1] Sandbox Security — Run nakal script"
python main.py &
sleep 2
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"code":"import os; print(os.system(\"whoami\"))"}' 2>/dev/null | jq .
pkill -f "python main.py"

# Test 2: Process Timeout
echo ""
echo "[TEST 2] Process Timeout — Infinite loop (should kill after 30s)"
python main.py &
sleep 2
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"code":"while True: pass"}' 2>/dev/null | jq .
pkill -f "python main.py"

# Test 3: Library Install
echo ""
echo "[TEST 3] Library Install — Runtime package (requests)"
python main.py &
sleep 2
curl -X POST http://localhost:5000/api/libraries/install \
  -H "Content-Type: application/json" \
  -d '{"name":"requests"}' 2>/dev/null | jq .
pkill -f "python main.py"

# Test 4: AI Provider Status
echo ""
echo "[TEST 4] AI Provider Status"
python main.py &
sleep 2
curl http://localhost:5000/api/keys/status 2>/dev/null | jq .
pkill -f "python main.py"

# Test 5: Health Check
echo ""
echo "[TEST 5] Health Check"
python main.py &
sleep 2
curl http://localhost:5000/api/health 2>/dev/null | jq .
pkill -f "python main.py"

# Test 6: File Manager
echo ""
echo "[TEST 6] File Manager — Save & List"
python main.py &
sleep 2
curl -X POST http://localhost:5000/api/files/test \
  -H "Content-Type: application/json" \
  -d '{"content":"print(\"hello world\")"}' 2>/dev/null | jq .
curl http://localhost:5000/api/files 2>/dev/null | jq .
pkill -f "python main.py"

echo ""
echo "✅ All tests completed!"
