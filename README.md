# 🖐️ Hand Mouse — Real-time Gesture Control

Control your **mouse cursor** using **hand gestures** via webcam.  
No GUI window — runs entirely in your terminal.

Supported on **macOS**, **Windows**, and **Linux**.

---

## ✨ Features

| Gesture | Action |
|---------|--------|
| ✋ Open hand | Move mouse (index finger tracks cursor) |
| 👊 Fist (all fingers curled) | **Single click** |
| ✌️ Peace sign (2 fingers up) | **Double click** |
| Press **Q** | Quit program |

- **No GUI window** — camera runs in background, status in terminal
- **Smooth cursor** — dead zone + EMA filtering
- **Real-time** — 25-30 FPS on modern hardware
- **Cross-platform** — macOS, Windows, Linux

---

## 📋 Minimum Specifications

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | macOS 11+, Windows 10+, Linux (x86_64) | macOS 13+, Windows 11 |
| **CPU** | Dual-core 2.0 GHz | Quad-core 2.5 GHz |
| **RAM** | 4 GB | 8 GB |
| **Camera** | 720p webcam | 1080p webcam |
| **Python** | 3.8 – 3.11 | 3.11 |
| **GPU** | CPU-only (slower) | Any GPU (better FPS) |

> **Note:** MediaPipe works best with Python 3.8–3.11.  
> Python 3.12+ may require an alternate install method.

---

## 🚀 Installation

### 1. Install Python (if not installed)

**macOS** — Python 3.8–3.11 recommended:

```bash
# Check your version
python3 --version

# If you need 3.11 (recommended):
brew install python@3.11
```

**Windows** — Download from [python.org](https://www.python.org/downloads/) (3.11 recommended).  
During install, check **"Add Python to PATH"**.

### 2. Clone the repo

```bash
git clone https://github.com/rezayw/webcam-hand-tracking.git
cd webcam-hand-tracking
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install opencv-python mediapipe numpy pyautogui pynput
```

---

## 🎮 Usage

### Basic (cross-platform)
```bash
python hand_mouse.py
```

### macOS — convenience command
After installing, you can run `tangan` from anywhere:
```bash
cp hand_mouse.py ~/.local/bin/tangan
chmod +x ~/.local/bin/tangan
# Now just type:
tangan
```
> Make sure `~/.local/bin` is in your `PATH` (add `export PATH="$HOME/.local/bin:$PATH"` to `~/.zshrc` if not).

### Visual mode (show camera preview)
```bash
python hand_tracker.py
```

### Controls
| Key | Action |
|-----|--------|
| **Q** | Stop program |
| **Ctrl+C** | Force stop |

---

## 🧠 How It Works

1. **Webcam** captures video frames in real-time
2. **MediaPipe Hands** detects 21 hand landmarks per frame
3. **Index finger tip** (landmark 8) is mapped to your screen coordinates
4. **Finger curl detection** checks which fingers are bent:
   - All 4 main fingers curled → **fist** → single click
   - Index & middle up, ring & pinky curled → **peace** → double click
5. **Smoothing** (EMA + dead zone) prevents cursor jitter
6. **pyautogui** moves the system cursor and simulates clicks

---

## 🛠️ Configuration

Edit these constants at the top of `hand_mouse.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DETECTION_CONF` | 0.7 | Hand detection confidence (0–1) |
| `TRACKING_CONF` | 0.5 | Tracking confidence (0–1) |
| `SMOOTH_ALPHA` | 0.45 | Cursor smoothness (0=very smooth, 1=instant) |
| `DEAD_ZONE` | 2 | Min pixel movement before cursor reacts |
| `FIST_HOLD_FRAMES` | 4 | Frames to hold fist before click |
| `PEACE_HOLD_FRAMES` | 3 | Frames to hold peace sign before double click |

---

## 🔧 Troubleshooting

### "No module named 'cv2'"
```bash
pip install opencv-python
```

### Camera not opening
- Make sure no other app is using the webcam
- On Windows, try a different `CAM_ID` (change to `1` in the script)
- On Windows, the script auto-falls back to DirectShow backend

### Mouse not moving (macOS)
Grant **Accessibility** permission:
1. Open **System Settings → Privacy & Security → Accessibility**
2. Add and enable **Terminal** (or the app running Python)

### Keyboard 'Q' not detected (macOS)
Grant **Input Monitoring** permission:
1. Open **System Settings → Privacy & Security → Input Monitoring**
2. Add and enable **Terminal**

### Low FPS
- Lower camera resolution (edit `cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)`)
- Close other apps using the camera
- Use a GPU-accelerated setup (MediaPipe uses Metal on macOS by default)

---

## 📁 Project Structure

```
webcam-hand-tracking/
├── hand_mouse.py         # Main cross-platform script (terminal mode)
├── hand_tracker.py       # Visual mode with camera preview window
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── .gitignore            # Ignored files
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

## 🙏 Credits

- [MediaPipe](https://mediapipe.dev/) by Google — hand landmark detection
- [pyautogui](https://pyautogui.readthedocs.io/) — cross-platform mouse control
- [pynput](https://pynput.readthedocs.io/) — keyboard listener
