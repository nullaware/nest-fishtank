#!/usr/bin/env python3
"""Keep the fish tank showing on a Nest Hub.

Run every few minutes (see install-launchd.sh). Each run:
  - inside the active hours: if the Hub has been idle for --grace minutes, cast the
    tank with `catt cast_site`;
  - outside the active hours: if the tank (DashCast) is showing, stop it.
It never interrupts other casts (music, video, etc.). The grace period stops it
jumping in while someone is using the touchscreen, which also reports as idle.

Runs with catt's own Python so pychromecast is available:
  $(uv tool dir)/catt/bin/python keepalive.py
"""
import argparse
import datetime
import shutil
import subprocess
import sys
import time
import zoneinfo
from pathlib import Path

import pychromecast
from pychromecast.config import APP_BACKDROP, APP_DASHCAST

DEFAULT_URL = "https://nullaware.github.io/nest-fishtank/tank.html"
IDLE_FILE = Path.home() / ".cache" / "nest-fishtank" / "idle-since"


def idle_minutes():
    """Minutes since the Hub was first seen idle, recording now if it wasn't."""
    try:
        since = float(IDLE_FILE.read_text())
    except (OSError, ValueError):
        IDLE_FILE.parent.mkdir(parents=True, exist_ok=True)
        IDLE_FILE.write_text(str(time.time()))
        return 0.0
    return (time.time() - since) / 60


def clear_idle():
    IDLE_FILE.unlink(missing_ok=True)


def log(msg):
    print(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def in_hours(hour, start, end):
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end   # window wraps past midnight


def catt_bin():
    local = Path(sys.executable).parent / "catt"
    return str(local) if local.exists() else (shutil.which("catt") or "catt")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--device", default="My Nest Hub")
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--start", type=float, default=7, help="hour to start showing (default 7)")
    p.add_argument("--end", type=float, default=22, help="hour to stop showing (default 22)")
    p.add_argument("--tz", default="Australia/Sydney")
    p.add_argument("--grace", type=float, default=5,
                   help="minutes the hub must stay idle before re-casting (default 5)")
    a = p.parse_args()

    now = datetime.datetime.now(zoneinfo.ZoneInfo(a.tz))
    active = in_hours(now.hour + now.minute / 60, a.start, a.end)

    casts, browser = pychromecast.get_listed_chromecasts(friendly_names=[a.device], timeout=15)
    try:
        if not casts:
            log(f"'{a.device}' not found on the network")
            return 1
        cast = casts[0]
        cast.wait(timeout=10)
        app_id = cast.status.app_id if cast.status else None
        app_name = cast.status.display_name if cast.status else None
        showing = app_id == APP_DASHCAST
        idle = app_id in (None, APP_BACKDROP) or cast.is_idle

        if not (active and idle and not showing):
            clear_idle()

        if active and showing:
            log("tank is showing")
        elif active and idle:
            waited = idle_minutes()
            if waited < a.grace:
                log(f"hub idle ({app_name or 'no app'}) for {waited:.1f} of {a.grace:g} min, waiting")
                return 0
            clear_idle()
            log(f"hub idle ({app_name or 'no app'}) for {waited:.1f} min, casting tank")
            r = subprocess.run([catt_bin(), "-d", a.device, "cast_site", a.url],
                               capture_output=True, text=True, timeout=90)
            log(f"catt exit {r.returncode}: {(r.stdout + r.stderr).strip()}")
            return r.returncode
        elif active:
            log(f"hub busy with {app_name!r}, leaving it alone")
        elif showing:
            log("outside active hours, stopping tank")
            cast.quit_app()
        else:
            log("outside active hours, nothing to do")
        return 0
    finally:
        browser.stop_discovery()


if __name__ == "__main__":
    sys.exit(main())
