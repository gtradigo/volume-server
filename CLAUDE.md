# Volume Remote

A small Flask app that runs on an Ubuntu laptop and serves a mobile-friendly web page. An Android phone on the same WiFi opens the page and controls the laptop's system volume.

## Layout

- `server.py` — the whole app: Flask routes, the `pactl` wrappers, and the HTML/CSS/JS page (embedded as the `INDEX_HTML` string).
- `README.md` — setup and usage instructions for the user.

## Run

```bash
pip install flask --break-system-packages
python3 server.py
```

The server listens on `0.0.0.0:5000` and prints the LAN URL to open on the phone.

## How it works

- Volume control shells out to `pactl` (works with PulseAudio and PipeWire) against `@DEFAULT_SINK@`.
- API routes: `GET /api/status`, `POST /api/set` (`{level}`), `POST /api/step` (`{delta}`), `POST /api/mute` (toggle).
- The page polls `/api/status` every 2 seconds and debounces slider changes by 120 ms.

## Notes for changes

- There is no authentication: anyone on the local network can reach the server. Keep that in mind before adding features, or consider adding a PIN/token.
- The target is the Ubuntu laptop. `pactl` is not available in cloud sandboxes, so test volume changes on the laptop itself.
- Keep the UI mobile-first (large touch targets, no scrolling).

## Ideas

- Split the HTML into `templates/` and `static/` folders
- Media controls (play/pause, next/previous) via `playerctl`
- Per-application volume and output device switching
- PIN or token protection
- Run as a systemd service so it starts on boot
