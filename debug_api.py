"""Script de diagnóstico — ejecutar con .venv/bin/python debug_api.py"""
import json
import sys
sys.path.insert(0, ".")

import browser_cookie3
import requests

# ── 1. Leer cookie ───────────────────────────────────────────────────────────
jar = browser_cookie3.firefox(domain_name="claude.ai")
session_key = next(
    (c.value for c in jar if c.name == "sessionKey" and "claude.ai" in (c.domain or "")),
    None,
)
if not session_key:
    print("ERROR: sessionKey no encontrada en Firefox")
    sys.exit(1)
print(f"sessionKey: {session_key[:12]}…")

# ── 2. Headers que imitan al navegador ───────────────────────────────────────
HEADERS = {
    "Cookie": f"sessionKey={session_key}",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://claude.ai/",
    "anthropic-client-version": "0",
    "x-requested-with": "XMLHttpRequest",
}

BASE = "https://claude.ai/api"

# ── 3. Organizaciones ────────────────────────────────────────────────────────
print("\n--- GET /api/organizations ---")
r = requests.get(f"{BASE}/organizations", headers=HEADERS, timeout=10)
print(f"Status: {r.status_code}")
try:
    data = r.json()
    print(json.dumps(data if isinstance(data, dict) else data[0] if data else data, indent=2)[:800])
    entry = data[0] if isinstance(data, list) else data
    org_id = entry.get("uuid") or entry.get("id")  # UUID primero
    print(f"\norg_id: {org_id}")
except Exception as e:
    print(f"body: {r.text[:400]}  ({e})")
    sys.exit(1)

# ── 4. Probar endpoints de uso ───────────────────────────────────────────────
endpoints = [
    f"/organizations/{org_id}/usage",
    f"/organizations/{org_id}/stats",
    f"/organizations/{org_id}/limits",
    f"/organizations/{org_id}/plan_limits",
    f"/usage",
    f"/account/usage",
]

for ep in endpoints:
    r = requests.get(f"{BASE}{ep}", headers=HEADERS, timeout=10)
    print(f"\n--- GET {ep} ---")
    print(f"Status: {r.status_code}")
    if r.ok:
        try:
            print(json.dumps(r.json(), indent=2)[:1000])
        except Exception:
            print(r.text[:400])
    else:
        print(r.text[:300])
