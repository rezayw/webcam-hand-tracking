#!/usr/bin/env python3
"""
Real-time Hand Tracking with MediaPipe + OpenCV
Fitur: landmark detection, gesture recognition (jumlah jari), FPS, bounding box
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import sys

# ─── Konfigurasi ─────────────────────────────────────────────────
CAM_ID = 0
MAX_HANDS = 2
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.5

# Warna (BGR)
COLOR_LANDMARK = (0, 255, 0)       # hijau terang
COLOR_CONNECTION = (255, 255, 255)  # putih
COLOR_BBOX = (0, 165, 255)          # oranye
COLOR_FPS = (0, 255, 255)           # kuning
COLOR_TEXT = (255, 255, 255)        # putih
COLOR_BG = (0, 0, 0)               # hitam
COLOR_GESTURE_BG = (30, 30, 30)    # abu-abu gelap

# ─── Inisialisasi MediaPipe ──────────────────────────────────────
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=MAX_HANDS,
    min_detection_confidence=DETECTION_CONFIDENCE,
    min_tracking_confidence=TRACKING_CONFIDENCE,
)

# Custom drawing spec — landmark lebih besar & terang
landmark_dot_spec = mp_draw.DrawingSpec(
    color=COLOR_LANDMARK, thickness=2, circle_radius=4
)
connection_spec = mp_draw.DrawingSpec(
    color=COLOR_CONNECTION, thickness=2
)


def count_fingers(landmarks, handedness):
    """
    Hitung jumlah jari yang terbuka.
    Menggunakan landmark tip jari (8, 12, 16, 20) vs PIP (6, 10, 14, 18).
    Ibu jari (4) vs landmark 3 — dibedakan berdasarkan tangan kiri/kanan.
    """
    fingers = []
    tips_ids = [4, 8, 12, 16, 20]

    # Ibu jari: bandingkan x-coordinate tip vs IP joint
    # Tangan kanan: tip lebih ke kanan (x lebih besar) = terbuka
    # Tangan kiri: tip lebih ke kiri (x lebih kecil) = terbuka
    if handedness == "Right":
        if landmarks[tips_ids[0]].x > landmarks[tips_ids[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)
    else:  # Left
        if landmarks[tips_ids[0]].x < landmarks[tips_ids[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)

    # 4 jari lainnya: tip y < pip y = terbuka (y naik ke bawah di OpenCV)
    for idx in range(1, 5):
        tip = tips_ids[idx]
        pip = tip - 2
        if landmarks[tip].y < landmarks[pip].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers


def get_gesture_name(fingers):
    """Terjemahkan jumlah jari ke nama gesture."""
    total = sum(fingers)
    if total == 0:
        return "Fist 👊"
    elif total == 1:
        return "Point ☝️"
    elif total == 2:
        return "Peace ✌️"
    elif total == 3:
        return "Three 🖖"
    elif total == 4:
        return "Four 🖐️"
    elif total == 5:
        return "Open Hand ✋"
    return "—"


def main():
    print("=" * 50)
    print("  REAL-TIME HAND TRACKING")
    print("=" * 50)
    print("  Kamera : Webcam utama")
    print(f"  Max    : {MAX_HANDS} tangan")
    print(f"  FPS    : real-time")
    print("-" * 50)
    print("  Controls:")
    print("    [Q] / ESC → Keluar")
    print("=" * 50)
    print()

    cap = cv2.VideoCapture(CAM_ID)
    if not cap.isOpened():
        print("  ERROR: Tidak bisa membuka kamera. Pastikan webcam tersambung.")
        sys.exit(1)

    # Set resolusi untuk performa lebih baik
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    p_time = 0
    frame_count = 0
    fps = 0

    cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ERROR: Gagal membaca frame dari kamera.")
            break

        # Flip horizontal agar mirror (lebih natural)
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert BGR → RGB untuk MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # ─── Drawing overlay (konsisten, tidak bergantung deteksi) ────
        overlay = frame.copy()

        # Info panel bawah
        panel_y = h - 50

        # ─── Jika tangan terdeteksi ──────────────────────────────────
        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Dapatkan handedness
                handedness = "Unknown"
                if results.multi_handedness and idx < len(results.multi_handedness):
                    handedness = results.multi_handedness[idx].classification[0].label

                # Gambar landmarks dengan custom spec
                mp_draw.draw_landmarks(
                    overlay,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    landmark_dot_spec,
                    connection_spec,
                )

                # Hitung bounding box
                x_coords = [lm.x for lm in hand_landmarks.landmark]
                y_coords = [lm.y for lm in hand_landmarks.landmark]
                x_min = int(min(x_coords) * w) - 20
                x_max = int(max(x_coords) * w) + 20
                y_min = int(min(y_coords) * h) - 20
                y_max = int(max(y_coords) * h) + 20
                # Clamp ke frame
                x_min = max(0, x_min)
                x_max = min(w, x_max)
                y_min = max(0, y_min)
                y_max = min(h, y_max)

                # Gambar bounding box
                cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), COLOR_BBOX, 2)

                # Hitung jumlah jari
                landmarks = hand_landmarks.landmark
                fingers = count_fingers(landmarks, handedness)
                total_fingers = sum(fingers)
                gesture = get_gesture_name(fingers)

                # Label tangan + gesture
                label = f"{handedness}: {gesture}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                label_x = x_min
                label_y = y_min - 10 if y_min > 25 else y_min + 25

                # Background label
                cv2.rectangle(
                    overlay,
                    (label_x - 5, label_y - label_size[1] - 5),
                    (label_x + label_size[0] + 5, label_y + 5),
                    (0, 0, 0),
                    -1,
                )
                cv2.putText(
                    overlay, label, (label_x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXT, 2,
                )

                # Visualisasi jumlah jari (dot indicator)
                for f_idx, is_up in enumerate(fingers):
                    dot_x = x_max - (4 - f_idx) * 18 - 10
                    dot_y = y_max + 15
                    dot_color = (0, 255, 0) if is_up else (0, 0, 255)
                    cv2.circle(overlay, (dot_x, dot_y), 5, dot_color, -1)

                # Tampilkan info landmark (koordinat landmark 8 = tip telunjuk)
                tip_idx = 8  # ujung jari telunjuk
                tip = landmarks[tip_idx]
                cx, cy = int(tip.x * w), int(tip.y * h)
                coord_text = f"({cx}, {cy})"
                cv2.putText(
                    overlay, coord_text, (cx + 10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_LANDMARK, 1,
                )

        # ─── Gabungkan overlay transparan ──────────────────────────
        alpha = 0.85
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # ─── FPS counter ──────────────────────────────────────────
        frame_count += 1
        c_time = time.time()
        if c_time - p_time >= 1.0:
            fps = frame_count
            frame_count = 0
            p_time = c_time

        cv2.putText(
            frame, f"FPS: {fps}", (w - 140, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_FPS, 2,
        )

        # ─── Info bar bawah ───────────────────────────────────────
        cv2.rectangle(frame, (0, h - 45), (w, h), COLOR_BG, -1)
        status_text = f"  [Q] Keluar  |  Tangan: {len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0}"
        cv2.putText(
            frame, status_text, (15, h - 18),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_TEXT, 1,
        )

        # ─── Tampilkan ────────────────────────────────────────────
        cv2.imshow("Hand Tracking", frame)

        # ─── Keluar dengan Q atau ESC ─────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

    # ─── Cleanup ──────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    print("  👋 Selesai. Terima kasih!")


if __name__ == "__main__":
    main()
