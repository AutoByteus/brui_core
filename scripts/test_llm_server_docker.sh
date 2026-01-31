#!/usr/bin/env bash
set -euo pipefail

LLM_HOST="localhost"
LLM_PORT=51739
CHROME_PORT=9222

echo "🚀 Testing LLM Server and Chromium in Docker..."

# Wait until ports are open
echo "⏳ Waiting for LLM server on port ${LLM_PORT}..."
until nc -z "${LLM_HOST}" "${LLM_PORT}" >/dev/null 2>&1; do
  sleep 1
done
echo "✅ LLM server is listening on ${LLM_PORT}"

echo "⏳ Waiting for Chromium on port ${CHROME_PORT}..."
until nc -z "${LLM_HOST}" "${CHROME_PORT}" >/dev/null 2>&1; do
  sleep 1
done
echo "✅ Chromium is listening on ${CHROME_PORT}"

# Test LLM server HTTP endpoint
echo "🌐 Checking LLM server API..."
curl -s "http://${LLM_HOST}:${LLM_PORT}/models/llm" | head -c 200 || echo "⚠️ No response"

# Test Chromium DevTools JSON version endpoint
echo -e "\n🌐 Checking Chromium DevTools..."
curl -s "http://${LLM_HOST}:${CHROME_PORT}/json/version" | jq . || curl -s "http://${LLM_HOST}:${CHROME_PORT}/json/version"

echo "🎉 All tests completed."
