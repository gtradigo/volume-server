#!/usr/bin/env python3
"""
Volume Remote — control your Ubuntu laptop's volume from your phone's browser.

Run this on your LAPTOP:
    pip install flask
    python3 server.py          # or: python3 server.py --tray

Then on your PHONE (same WiFi network), open the URL it prints,
e.g. http://192.168.1.42:5000
"""

import argparse
import os
import re
import signal
import socket
import subprocess
import threading
import time

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

SINK = "@DEFAULT_SINK@"
PORT = 5000


def run(cmd):
    # pactl's output is localized (e.g. "Mute: sì"), so force English for parsing.
    env = {**os.environ, "LC_ALL": "C"}
    return subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=env)


def get_status():
    """Return current volume (0-100) and mute state using pactl."""
    vol = 0
    muted = False
    try:
        out = run(["pactl", "get-sink-volume", SINK]).stdout
        m = re.search(r"(\d+)%", out)
        if m:
            vol = int(m.group(1))
    except Exception:
        pass
    try:
        out = run(["pactl", "get-sink-mute", SINK]).stdout
        muted = "yes" in out.lower()
    except Exception:
        pass
    return {"volume": vol, "muted": muted}


@app.route("/")
def index():
    return INDEX_HTML


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


@app.route("/manifest.json")
def manifest():
    return jsonify(
        {
            "name": "Volume Remote",
            "short_name": "Volume",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0f1115",
            "theme_color": "#0f1115",
            "icons": [
                {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
            ],
        }
    )


@app.route("/api/status")
def api_status():
    return jsonify(get_status())


@app.route("/api/set", methods=["POST"])
def api_set():
    level = int(request.json.get("level", 50))
    level = max(0, min(100, level))
    run(["pactl", "set-sink-volume", SINK, f"{level}%"])
    return jsonify(get_status())


@app.route("/api/step", methods=["POST"])
def api_step():
    delta = int(request.json.get("delta", 5))
    sign = "+" if delta >= 0 else "-"
    run(["pactl", "set-sink-volume", SINK, f"{sign}{abs(delta)}%"])
    return jsonify(get_status())


@app.route("/api/mute", methods=["POST"])
def api_mute():
    run(["pactl", "set-sink-mute", SINK, "toggle"])
    return jsonify(get_status())


INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<title>Volume Remote</title>
<link rel="icon" type="image/svg+xml" href="/assets/logo.svg">
<link rel="apple-touch-icon" href="/assets/icon-192.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0f1115">
<style>
  :root {
    --bg: #0f1115;
    --card: #1a1d24;
    --accent: #4f8cff;
    --text: #f2f3f5;
    --muted-color: #ff5b6a;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; user-select: none; }
  html, body {
    height: 100%;
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    overscroll-behavior: none;
    padding-top: env(safe-area-inset-top, 0px);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
  .card {
    width: 100%;
    max-width: 380px;
    padding: 32px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
  }
  .logo {
    width: 88px;
    height: 88px;
    border-radius: 20px;
  }
  h1 {
    font-size: 18px;
    font-weight: 600;
    color: #9aa1ac;
    margin: 0;
    letter-spacing: 0.02em;
  }
  .volume-display {
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    transition: color 0.2s ease;
  }
  .muted .volume-display { color: var(--muted-color); }

  .slider-wrap {
    width: 100%;
    padding: 8px 0;
  }
  input[type=range] {
    width: 100%;
    height: 48px;
    -webkit-appearance: none;
    appearance: none;
    background: transparent;
  }
  input[type=range]::-webkit-slider-runnable-track {
    height: 12px;
    border-radius: 6px;
    background: linear-gradient(to right, var(--accent) var(--fill, 50%), #2b2f38 0);
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #fff;
    margin-top: -10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
  }

  .row {
    display: flex;
    gap: 16px;
    width: 100%;
  }
  button {
    flex: 1;
    border: none;
    border-radius: 16px;
    background: var(--card);
    color: var(--text);
    font-size: 26px;
    padding: 20px 0;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s ease, transform 0.08s ease;
  }
  button:active { transform: scale(0.95); background: #262a33; }

  .mute-btn {
    width: 100%;
    background: var(--card);
    font-size: 17px;
    padding: 16px 0;
    border-radius: 16px;
    color: #c6cad2;
    letter-spacing: 0.03em;
  }
  .mute-btn.active {
    background: var(--muted-color);
    color: #fff;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3ddc84;
    display: inline-block;
    margin-right: 6px;
  }
  .status-dot.offline { background: #ff5b6a; }
  .status-line {
    font-size: 12px;
    color: #6b7280;
  }
</style>
</head>
<body>
  <div class="card" id="card">
    <img class="logo" src="/assets/logo.svg" alt="Volume Remote logo">
    <h1>VOLUME REMOTE</h1>
    <div class="volume-display" id="volDisplay">--</div>

    <div class="slider-wrap">
      <input type="range" id="slider" min="0" max="100" value="50">
    </div>

    <div class="row">
      <button id="downBtn">&#8722;</button>
      <button id="upBtn">&#43;</button>
    </div>

    <button class="mute-btn" id="muteBtn">MUTE</button>

    <div class="status-line"><span class="status-dot" id="statusDot"></span><span id="statusText">connecting…</span></div>
  </div>

<script>
const slider = document.getElementById('slider');
const volDisplay = document.getElementById('volDisplay');
const upBtn = document.getElementById('upBtn');
const downBtn = document.getElementById('downBtn');
const muteBtn = document.getElementById('muteBtn');
const card = document.getElementById('card');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

let syncing = false;

function render(status) {
  slider.value = status.volume;
  slider.style.setProperty('--fill', status.volume + '%');
  volDisplay.textContent = status.muted ? 'MUTED' : status.volume;
  card.classList.toggle('muted', status.muted);
  muteBtn.classList.toggle('active', status.muted);
  muteBtn.textContent = status.muted ? 'UNMUTE' : 'MUTE';
}

function setOnline(ok) {
  statusDot.classList.toggle('offline', !ok);
  statusText.textContent = ok ? 'connected' : 'connection lost';
}

async function refresh() {
  try {
    const r = await fetch('/api/status');
    const data = await r.json();
    if (!syncing) render(data);
    setOnline(true);
  } catch (e) {
    setOnline(false);
  }
}

async function post(url, body) {
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body || {})
    });
    const data = await r.json();
    render(data);
    setOnline(true);
  } catch (e) {
    setOnline(false);
  }
}

let debounceTimer = null;
slider.addEventListener('input', () => {
  syncing = true;
  slider.style.setProperty('--fill', slider.value + '%');
  volDisplay.textContent = slider.value;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    post('/api/set', {level: parseInt(slider.value, 10)});
    syncing = false;
  }, 120);
});

upBtn.addEventListener('click', () => post('/api/step', {delta: 5}));
downBtn.addEventListener('click', () => post('/api/step', {delta: -5}));
muteBtn.addEventListener('click', () => post('/api/mute'));

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def serve():
    app.run(host="0.0.0.0", port=PORT)


def load_tray_libs():
    """Return (Gdk, GLib, Gtk, AppIndicator), or None if there's no usable tray."""
    try:
        import gi

        gi.require_version("Gdk", "3.0")
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, GLib, Gtk

        try:
            # Newer Ubuntu releases only ship the Ayatana fork.
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AppIndicator
        except ValueError:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3 as AppIndicator
    except (ImportError, ValueError) as e:
        print(f"  Tray disabled: {e}")
        return None
    if not Gtk.init_check()[0]:
        print("  Tray disabled: no graphical session.")
        return None
    return Gdk, GLib, Gtk, AppIndicator


def run_tray(url, libs):
    """Show the tray icon on the main thread and serve Flask in the background."""
    Gdk, GLib, Gtk, AppIndicator = libs

    indicator = AppIndicator.Indicator.new(
        "volume-remote",
        os.path.join(ASSETS_DIR, "icon-192.png"),
        AppIndicator.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_title("Volume Remote")
    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()
    url_item = Gtk.MenuItem(label=f"Copy phone URL: {url}")
    volume_item = Gtk.MenuItem(label="Volume: --")
    volume_item.set_sensitive(False)
    mute_item = Gtk.MenuItem(label="Mute")
    quit_item = Gtk.MenuItem(label="Quit")
    for item in (url_item, Gtk.SeparatorMenuItem(), volume_item, mute_item,
                 Gtk.SeparatorMenuItem(), quit_item):
        menu.append(item)
    menu.show_all()
    indicator.set_menu(menu)

    def show_status(status):
        volume_item.set_label(f"Volume: {'muted' if status['muted'] else status['volume']}")
        mute_item.set_label("Unmute" if status["muted"] else "Mute")

    def publish_status():
        GLib.idle_add(show_status, get_status())

    def poll_status():
        while True:
            publish_status()
            time.sleep(2)

    def toggle_mute():
        run(["pactl", "set-sink-mute", SINK, "toggle"])
        publish_status()

    def copy_url(_item):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(url, -1)
        clipboard.store()

    def serve_then_quit():
        # If Flask dies (e.g. port in use), don't leave a dead icon in the tray.
        try:
            serve()
        finally:
            GLib.idle_add(Gtk.main_quit)

    url_item.connect("activate", copy_url)
    # pactl can block for seconds, so keep it off the GTK thread.
    mute_item.connect(
        "activate", lambda _item: threading.Thread(target=toggle_mute, daemon=True).start()
    )
    quit_item.connect("activate", lambda _item: Gtk.main_quit())

    for sig in (signal.SIGINT, signal.SIGTERM):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, sig, Gtk.main_quit)

    threading.Thread(target=serve_then_quit, daemon=True).start()
    threading.Thread(target=poll_status, daemon=True).start()
    Gtk.main()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control this laptop's volume from your phone.")
    parser.add_argument("--tray", action="store_true", help="show a system tray icon")
    args = parser.parse_args()

    phone_url = f"http://{local_ip()}:{PORT}"
    print("\n  Volume Remote is running.")
    print(f"  On your phone (same WiFi), open:  {phone_url}\n")

    tray_libs = load_tray_libs() if args.tray else None
    if tray_libs:
        run_tray(phone_url, tray_libs)
    else:
        serve()
