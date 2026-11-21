#!/usr/bin/env python3
"""Phone Deck: live Android screen + stats + remote control over adb.

Run: python3 server.py   then open http://127.0.0.1:8765
"""
import json
import pathlib
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
HERE = pathlib.Path(__file__).parent

KEYS = {
    "home": "KEYCODE_HOME",
    "back": "KEYCODE_BACK",
    "recents": "KEYCODE_APP_SWITCH",
    "power": "KEYCODE_POWER",
    "wake": "KEYCODE_WAKEUP",
    "vol_up": "KEYCODE_VOLUME_UP",
    "vol_down": "KEYCODE_VOLUME_DOWN",
    "play": "KEYCODE_MEDIA_PLAY_PAUSE",
}


def adb(*args, binary=False, timeout=10):
    out = subprocess.run(["adb", *args], capture_output=True, timeout=timeout)
    return out.stdout if binary else out.stdout.decode(errors="replace")


def stats():
    sep = "@@SEP@@"
    cmds = [
        "dumpsys battery",
        "cat /proc/meminfo",
        "df /data",
        "cat /proc/uptime",
        "dumpsys activity activities | grep -m1 topResumedActivity",
        "getprop ro.product.model; getprop ro.build.version.release; getprop ro.product.manufacturer",
        "wm size",
        "dumpsys power | grep -m1 mWakefulness=",
    ]
    raw = adb("shell", f"; echo {sep}; ".join(cmds)).split(sep)
    if len(raw) < len(cmds):
        return {"connected": False}
    batt, mem, df, up, top, props, size, power = raw

    def num(pattern, text, default=0):
        m = re.search(pattern, text)
        return int(m.group(1)) if m else default

    mem_total = num(r"MemTotal:\s+(\d+)", mem)
    mem_avail = num(r"MemAvailable:\s+(\d+)", mem)
    df_line = df.strip().splitlines()[-1].split()
    model, release, maker = (props.strip().splitlines() + ["", "", ""])[:3]
    top_m = re.search(r"u0 ([\w.]+)/", top)
    size_m = re.search(r"(\d+)x(\d+)", size)
    charging = num(r"status: (\d)", batt) == 2

    return {
        "connected": True,
        "device": f"{maker.title()} {model}",
        "android": release,
        "battery": num(r"level: (\d+)", batt),
        "charging": charging,
        "temp_c": num(r"temperature: (\d+)", batt) / 10,
        "voltage_mv": num(r"voltage: (\d+)", batt),
        "ram_used_pct": round(100 * (mem_total - mem_avail) / mem_total) if mem_total else 0,
        "ram_total_gb": round(mem_total / 1024 / 1024, 1),
        "storage_used_pct": int(df_line[4].rstrip("%")) if len(df_line) > 4 else 0,
        "storage_total_gb": round(int(df_line[1]) / 1024 / 1024) if len(df_line) > 1 else 0,
        "uptime_h": round(float(up.split()[0]) / 3600, 1) if up.strip() else 0,
        "foreground": top_m.group(1) if top_m else "?",
        "screen_on": "Awake" in power,
        "width": int(size_m.group(1)) if size_m else 1080,
        "height": int(size_m.group(2)) if size_m else 1920,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/stats":
            self.send(200, json.dumps(stats()).encode(), "application/json")
        elif self.path.startswith("/api/screen"):
            png = adb("exec-out", "screencap", "-p", binary=True)
            self.send(200 if png else 503, png, "image/png")
        else:
            self.send(404, b"not found", "text/plain")

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        action = body.get("action")
        if action == "tap":
            adb("shell", "input", "tap", str(int(body["x"])), str(int(body["y"])))
        elif action == "swipe":
            adb("shell", "input", "swipe", *(str(int(body[k])) for k in ("x1", "y1", "x2", "y2")), "250")
        elif action == "text":
            # adb input text needs spaces as %s and shell metacharacters escaped
            text = re.sub(r"([\\\"'`$&|;<>()*?!#~])", r"\\\1", body.get("text", "")).replace(" ", "%s")
            adb("shell", "input", "text", text)
        elif action in KEYS:
            adb("shell", "input", "keyevent", KEYS[action])
        else:
            return self.send(400, b'{"ok":false}', "application/json")
        self.send(200, b'{"ok":true}', "application/json")


if __name__ == "__main__":
    print(f"Phone Deck on http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
