#!/usr/bin/env python3
"""
Hand Mouse — Real-time hand gesture mouse control.
Control your cursor with hand gestures via webcam. No GUI window.

Supported Platforms: macOS, Windows, Linux

Gestures:
  ✋ Open hand         → Move mouse (index finger)
  👊 Fist (all curled) → Single click
  ✌️ Peace (2 fingers) → Double click
  Press Q              → Quit
"""

import sys
import os
import time
import platform

# ─── Platform-specific setup ──────────────────────────────────
IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

if IS_MAC:
    # macOS: ensure user site-packages is in path (pip3 installs there)
    _user_site = os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages")
    if _user_site not in sys.path and os.path.isdir(_user_site):
        sys.path.insert(0, _user_site)

# ─── Dependencies ─────────────────────────────────────────────
try:
    import cv2
    import mediapipe as mp
    import numpy as np
    import pyautogui
    pyautogui.FAILSAFE = False
    SCREEN_W, SCREEN_H = pyautogui.size()
except ImportError as e:
    print(f"  ❌ Missing dependency: {e}")
    print("  Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from pynput import keyboard
except ImportError:
    print("  ❌ pynput not found. Install: pip install pynput")
    sys.exit(1)

# ─── Config ───────────────────────────────────────────────────
CAM_ID = 0
DETECTION_CONF = 0.7
TRACKING_CONF = 0.5

# Screen mapping zone (center region mapped to full screen)
MAP_X_MIN, MAP_X_MAX = 0.03, 0.97
MAP_Y_MIN, MAP_Y_MAX = 0.03, 0.93

# Smoothing
SMOOTH_ALPHA = 0.45
DEAD_ZONE = 2

# Gesture hold frames
FIST_HOLD_FRAMES = 4
PEACE_HOLD_FRAMES = 3
POST_COOLDOWN = 8
DEBOUNCE_MS = 350

# ─── Landmarks ────────────────────────────────────────────────
TIP_IDS = [4, 8, 12, 16, 20]
PIP_IDS = [3, 6, 10, 14, 18]
FINGER_NAMES = ["Idx", "Mid", "Ring", "Pinky"]

# ─── MediaPipe ────────────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=DETECTION_CONF,
    min_tracking_confidence=TRACKING_CONF,
)

# ─── State ────────────────────────────────────────────────────
smooth_x = SCREEN_W // 2
smooth_y = SCREEN_H // 2
fist_count = 0
peace_count = 0
cooldown = 0
last_click_ms = 0
quit_flag = False
click_msg = ""


# ─── Helpers ──────────────────────────────────────────────────

def landmark_to_screen(lm_x, lm_y, fw, fh):
    """Map normalized landmark → screen coordinates."""
    mx = max(MAP_X_MIN, min(lm_x, MAP_X_MAX))
    my = max(MAP_Y_MIN, min(lm_y, MAP_Y_MAX))
    sx = (mx - MAP_X_MIN) / (MAP_X_MAX - MAP_X_MIN) * SCREEN_W
    sy = (my - MAP_Y_MIN) / (MAP_Y_MAX - MAP_Y_MIN) * SCREEN_H
    return int(sx), int(sy)


def get_curled(landmarks):
    """Check curl state of 4 main fingers (index→pinky)."""
    curled = []
    for fi in range(1, 5):
        tip = landmarks[TIP_IDS[fi]]
        pip = landmarks[PIP_IDS[fi]]
        # Curled = fingertip below PIP joint (larger y = lower in image)
        curled.append(tip.y > pip.y)
    return sum(curled), curled


def detect_gesture(curled):
    """Classify gesture from finger curl pattern."""
    if all(curled):
        return "fist"
    if not curled[0] and not curled[1] and curled[2] and curled[3]:
        return "peace"
    return "none"


def on_press(key):
    """Keyboard listener callback — Q to quit."""
    global quit_flag
    try:
        if hasattr(key, 'char') and key.char and key.char.lower() == 'q':
            quit_flag = True
            return False
    except AttributeError:
        pass


def print_status(fps_val, gesture, n_curled, sx, sy, click=""):
    """Update status line in terminal."""
    icons = {"fist": "👊", "peace": "✌️", "none": "✋"}
    names = {"fist": "SINGLE", "peace": "DOUBLE", "none": "MOUSE"}
    icon = icons.get(gesture, "—")
    name = names.get(gesture, "—")
    click_str = f"  {click}" if click else ""
    line = f"\r{icon} {name}  |  Fingers:{4 - n_curled}  |  Screen:({sx},{sy})  |  FPS:{fps_val}{click_str}   "
    sys.stdout.write(line.ljust(80))
    sys.stdout.flush()


def print_banner():
    """Show startup info."""
    os_name = platform.system()
    banner = f"""
╔══════════════════════════════════════════╗
║        🖐️  HAND MOUSE                    ║
║        Real-time Gesture Control         ║
╠══════════════════════════════════════════╣
║  Platform : {os_name:<29} ║
║  Screen   : {SCREEN_W} x {SCREEN_H:<23} ║
╠══════════════════════════════════════════╣
║  ✋ Open hand         → move mouse       ║
║  👊 Fist              → single click     ║
║  ✌️ Peace (2 fingers) → double click     ║
║  [Q]                 → quit              ║
╚══════════════════════════════════════════╝
"""
    print(banner)


# ─── Main ─────────────────────────────────────────────────────

def main():
    global smooth_x, smooth_y, fist_count, peace_count, cooldown, last_click_ms, quit_flag, click_msg

    # Start keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()

    # Open camera
    cap = cv2.VideoCapture(CAM_ID)
    if not cap.isOpened():
        # Windows fallback: try DirectShow
        if IS_WIN:
            cap = cv2.VideoCapture(CAM_ID, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("  ❌ Could not open webcam. Check camera connection.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Clear screen and show banner
    os.system('cls' if IS_WIN else 'clear')
    print_banner()
    print("  Status: waiting for hand...\n")

    p_time = 0
    fcount = 0
    fps = 0
    click_timer = 0
    last_gesture = "none"

    while not quit_flag:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.03)
            continue

        # Mirror frame for natural interaction
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        hand_detected = False
        n_curled = 0
        curled = [False] * 4
        gesture = "none"

        if cooldown > 0:
            cooldown -= 1

        if results.multi_hand_landmarks:
            hand_detected = True
            hl = results.multi_hand_landmarks[0]
            landmarks = hl.landmark

            # Index finger tip (landmark 8) → cursor
            idx = landmarks[8]
            tx, ty = landmark_to_screen(idx.x, idx.y, frame.shape[1], frame.shape[0])
            dx = tx - smooth_x
            dy = ty - smooth_y
            if abs(dx) > DEAD_ZONE or abs(dy) > DEAD_ZONE:
                smooth_x = int(smooth_x + dx * SMOOTH_ALPHA)
                smooth_y = int(smooth_y + dy * SMOOTH_ALPHA)

            if cooldown == 0:
                pyautogui.moveTo(smooth_x, smooth_y, duration=0)

            # Gesture detection
            n_curled, curled = get_curled(landmarks)
            gesture = detect_gesture(curled)

            if cooldown == 0:
                if gesture == "fist":
                    fist_count += 1
                    peace_count = 0
                    if fist_count >= FIST_HOLD_FRAMES:
                        now = time.time() * 1000
                        if now - last_click_ms > DEBOUNCE_MS:
                            pyautogui.click(button='left')
                            last_click_ms = now
                            cooldown = POST_COOLDOWN
                            click_msg = "💥 CLICK!"
                            click_timer = 12
                            fist_count = 0

                elif gesture == "peace":
                    peace_count += 1
                    fist_count = 0
                    if peace_count >= PEACE_HOLD_FRAMES:
                        now = time.time() * 1000
                        if now - last_click_ms > DEBOUNCE_MS:
                            pyautogui.click(button='left')
                            pyautogui.click(button='left')
                            last_click_ms = now
                            cooldown = POST_COOLDOWN
                            click_msg = "💥 DOUBLE CLICK!"
                            click_timer = 12
                            peace_count = 0
                else:
                    fist_count = 0
                    peace_count = 0
            else:
                fist_count = 0
                peace_count = 0

        # Click message fade
        if click_timer > 0:
            click_timer -= 1
            if click_timer == 0:
                click_msg = ""

        # FPS
        fcount += 1
        ct = time.time()
        if ct - p_time >= 1.0:
            fps = fcount
            fcount = 0
            p_time = ct

        # Status display
        if hand_detected:
            last_gesture = gesture
        print_status(fps, last_gesture, n_curled if hand_detected else 0,
                     smooth_x, smooth_y, click_msg)

        time.sleep(0.01)

    # ─── Cleanup ────────────────────────────────────────────────
    cap.release()
    hands.close()
    print("\n\n  👋 Goodbye!\n")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    main()
