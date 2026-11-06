<p align="center">
  <img src="assets/logo.svg" alt="Volume Remote logo" width="128" height="128">
</p>

# Volume Remote

Use your Android phone's browser as a volume remote for your Ubuntu laptop.
No app install needed on the phone — it's just a web page served by your laptop.

## Setup (on your laptop)

1. Make sure `pactl` is installed (it comes with PulseAudio/PipeWire, which is standard on Ubuntu):
   ```bash
   pactl --version
   ```
   If missing: `sudo apt install pulseaudio-utils`

2. Install Flask:
   ```bash
   pip install flask --break-system-packages
   ```
   (or use a virtualenv if you prefer)

3. Run the server:
   ```bash
   python3 server.py
   ```
   It will print something like:
   ```
   On your phone (same WiFi), open: http://192.168.1.42:5000
   ```

## Tray icon (optional)

Run with `--tray` to get an icon in the top bar:

```bash
python3 server.py --tray
```

Its menu copies the phone URL, shows the current volume, toggles mute and quits the server.

It uses GTK and AppIndicator, which are usually already on Ubuntu. If they're missing:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

Use your system Python for this, since a virtualenv won't see these packages by default. If the libraries or a graphical session aren't available, the server prints why and runs without the icon.

## Use it (on your phone)

1. Connect your phone to the **same WiFi network** as your laptop.
2. Open the printed URL in your phone's browser (Chrome, Firefox, etc.).
3. Optional: tap your browser's menu → "Add to Home Screen" so it behaves like an app.

You'll see a big volume readout, a slider, +/- buttons, and a mute toggle. Changes apply instantly to your laptop's system volume.

## Notes

- The laptop and phone must be on the same local network (same WiFi router). This won't work over mobile data or different networks.
- If your laptop's IP address changes (e.g. you reconnect to WiFi), just re-run `server.py` — it'll print the new address.
- If your firewall blocks it, allow incoming connections on port 5000:
  ```bash
  sudo ufw allow 5000/tcp
  ```
- To keep it running in the background: `nohup python3 server.py &`, or set it up as a systemd service if you want it to survive reboots — just ask and I can put that together too.
- Volume control uses `pactl`, which works with both PulseAudio and PipeWire (Ubuntu's current default sound server), so this should work out of the box on any recent Ubuntu version.
