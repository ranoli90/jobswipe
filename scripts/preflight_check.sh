#!/usr/bin/env bash
set -euo pipefail

echo "Running preflight checks..."

# Parse fly internal_port
if [ -f fly.toml ]; then
  internal_port=$(grep -E "^\s*internal_port\s*=" fly.toml | head -n1 | awk -F'=' '{print $2}' | tr -d ' "')
else
  echo "fly.toml not found"; exit 2
fi

# Parse Dockerfile EXPOSE
if grep -q '^EXPOSE ' Dockerfile; then
  docker_port=$(grep '^EXPOSE ' Dockerfile | awk '{print $2}' | tr -d ' ')
else
  docker_port=""
fi

# Parse app port from backend/api/main.py (uvicorn.run) or from module-level uvicorn.run
app_port_num=""
if [ -f backend/api/main.py ]; then
  # Try to find `uvicorn.run(... host="0.0.0.0", port=8080)` style
  app_port_num=$(grep -E "uvicorn.run\(.*port *= *[0-9]+" backend/api/main.py -n || true)
  if [ -n "$app_port_num" ]; then
    app_port_num=$(echo "$app_port_num" | sed -n 's/.*port *= *\([0-9]\+\).*/\1/p' | head -n1)
  fi
fi

# Fallback: check for --port in Dockerfile CMD or fly.toml processes
if [ -z "$app_port_num" ]; then
  cmd_port=$(grep -oP '--port\s+\K[0-9]+' Dockerfile || true)
  app_port_num="$cmd_port"
fi

# Fallback: internal_port if still empty
if [ -z "$app_port_num" ]; then
  app_port_num="$internal_port"
fi

echo "fly internal_port: $internal_port"
echo "Dockerfile EXPOSE: ${docker_port:-(none)}"
echo "app port: ${app_port_num:-(none)}"

if [ -n "$internal_port" ] && [ -n "$app_port_num" ] && [ "$internal_port" != "$app_port_num" ]; then
  echo "ERROR: port mismatch between fly.toml internal_port ($internal_port) and app port ($app_port_num)"
  exit 3
fi
if [ -n "$docker_port" ] && [ -n "$app_port_num" ] && [ "$docker_port" != "$app_port_num" ]; then
  echo "ERROR: port mismatch between Dockerfile EXPOSE ($docker_port) and app port ($app_port_num)"
  exit 4
fi

# Check required environment variables locally (useful for CI/local preflight)
required=(DATABASE_URL SECRET_KEY ENCRYPTION_PASSWORD ENCRYPTION_SALT OAUTH_STATE_SECRET)
missing=()
for v in "${required[@]}"; do
  if [ -z "${!v:-}" ]; then
    missing+=("$v")
  fi
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "WARNING: missing environment variables locally: ${missing[*]}"
  echo "If deploying to Fly, set them using:"
  echo "  fly secrets set ${missing[*]/#/}"
else
  echo "All critical env vars set locally"
fi

# Check for .dockerignore exclusions that may hide required files
if grep -q "^backend/workers/" .dockerignore 2>/dev/null; then
  echo "NOTE: .dockerignore excludes backend/workers/. We added exceptions, verify worker code is included in build context if needed."
fi

echo "Preflight checks completed"
