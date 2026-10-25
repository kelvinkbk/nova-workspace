"""Read-only localhost status API for NOVA's static dashboard."""
import hmac
import json
import os
import platform
import sqlite3
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / "finance" / "ledger.sqlite3"
ORIGIN = os.environ.get("NOVA_DASHBOARD_ORIGIN", "https://nova-workplace.netlify.app").rstrip("/")
TOKEN = os.environ.get("NOVA_DASHBOARD_TOKEN", "")
START = time.monotonic()


def read_ledger():
    empty = {"available": False, "reason": "Ledger database not found",
             "verified_income_paise": None, "verified_expense_paise": None,
             "verified_owner_funding_paise": None, "net_earned_paise": None,
             "pending_count": None, "verified_count": None}
    if not DB.is_file():
        return empty
    try:
        with sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True, timeout=1) as con:
            rows = con.execute(
                "SELECT kind,status,COALESCE(SUM(amount_paise),0),COUNT(*) "
                "FROM finance_transactions GROUP BY kind,status"
            ).fetchall()
        totals = {"available": True, "verified_income_paise": 0,
                  "verified_expense_paise": 0, "verified_owner_funding_paise": 0,
                  "pending_count": 0, "verified_count": 0}
        keys = {"income": "verified_income_paise", "expense": "verified_expense_paise",
                "owner_funding": "verified_owner_funding_paise"}
        for kind, status, amount, count in rows:
            if status == "pending":
                totals["pending_count"] += count
            elif status == "verified" and kind in keys:
                totals["verified_count"] += count
                totals[keys[kind]] += amount
        totals["net_earned_paise"] = totals["verified_income_paise"] - totals["verified_expense_paise"]
        return totals
    except (sqlite3.Error, OSError):
        return {**empty, "reason": "Ledger read failed"}


class Handler(BaseHTTPRequestHandler):
    server_version = "NOVA-Local-Bridge/1.0"

    def log_message(self, fmt, *args):
        print(f"[{datetime.now(timezone.utc).isoformat()}] {fmt % args}")

    def cors(self):
        if self.headers.get("Origin", "") == ORIGIN:
            self.send_header("Access-Control-Allow-Origin", ORIGIN)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Cache-Control", "no-store")

    def respond(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        if self.headers.get("Origin", "") != ORIGIN:
            self.respond(403, {"error": "Origin not allowed"})
            return
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        if urlparse(self.path).path != "/api/status":
            self.respond(404, {"error": "Not found"})
            return
        if self.headers.get("Origin", "") != ORIGIN:
            self.respond(403, {"error": "Origin not allowed"})
            return
        if not TOKEN or not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + TOKEN):
            self.respond(401, {"error": "Unauthorized"})
            return
        self.respond(200, {
            "ok": True, "bridge": "online", "runtime": "not_detected",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int(time.monotonic() - START),
            "host": platform.system(), "host_release": platform.release(),
            "python": platform.python_version(), "workspace": ROOT.name,
            "ledger": read_ledger(),
            "note": "Bridge is live; NOVA runtime process status is not inferred from bridge connectivity."
        })


def main():
    if len(TOKEN) < 32:
        raise SystemExit("Set NOVA_DASHBOARD_TOKEN to a random secret of at least 32 characters.")
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("NOVA read-only bridge: http://127.0.0.1:8765/api/status")
    print("Allowed origin:", ORIGIN)
    print("Keep this terminal open; press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
