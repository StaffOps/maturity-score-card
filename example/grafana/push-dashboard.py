#!/usr/bin/env python3
"""Push the Dashboard Schema V2 JSON into Grafana.

Grafana's file provisioner rejects V2 dashboards outright:

    failed to save dashboard ... error="dashboard appears to be in v2 format.
    Please use the /apis/dashboard.grafana.app/v2 API"

No feature toggle changes that — V2 dashboards can only be created through the
resource API. This script does that push, so dashboards/maturity.json stays the
single source of truth. It is idempotent: creates on first run, updates after.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

GRAFANA = os.environ.get("GRAFANA_URL", "http://grafana:3000")
USER = os.environ.get("GRAFANA_USER", "admin")
PASSWORD = os.environ.get("GRAFANA_PASSWORD", "admin")
SPEC_FILE = os.environ.get("DASHBOARD_FILE", "/dashboards/maturity.json")
UID = os.environ.get("DASHBOARD_UID", "maturity-score-v1")

API = f"{GRAFANA}/apis/dashboard.grafana.app/v2/namespaces/default/dashboards"


def request(method: str, url: str, payload: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    import base64
    token = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return e.code, {"message": raw.decode(errors="replace")}


def wait_for_grafana(attempts: int = 60) -> None:
    for i in range(attempts):
        try:
            status, _ = request("GET", f"{GRAFANA}/api/health")
            if status == 200:
                print(f"grafana is up (after {i * 2}s)", flush=True)
                return
        except Exception:
            pass
        time.sleep(2)
    sys.exit("timed out waiting for grafana")


def main() -> None:
    wait_for_grafana()

    with open(SPEC_FILE) as fh:
        spec = json.load(fh)

    resource = {
        "apiVersion": "dashboard.grafana.app/v2",
        "kind": "Dashboard",
        "metadata": {"name": UID},
        "spec": spec,
    }

    status, existing = request("GET", f"{API}/{UID}")
    if status == 200:
        # PUT needs the current resourceVersion for optimistic concurrency.
        resource["metadata"]["resourceVersion"] = existing["metadata"]["resourceVersion"]
        status, body = request("PUT", f"{API}/{UID}", resource)
        action = "updated"
    else:
        status, body = request("POST", API, resource)
        action = "created"

    if status not in (200, 201):
        sys.exit(f"failed to push dashboard ({status}): {body.get('message', body)}")

    tabs = body["spec"]["layout"]["spec"]["tabs"]
    print(
        f"dashboard {action}: {body['spec']['title']!r} "
        f"(uid={body['metadata']['name']}, tabs={len(tabs)}) "
        f"-> {GRAFANA}/d/{body['metadata']['name']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
