import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import requests
import math
import pyaudio

# ---------------- CONFIG ----------------
NODEMCU_IP = "http://192.168.4.1"
MOTOR_ON_URL = NODEMCU_IP + "/motor/on"
MOTOR_OFF_URL = NODEMCU_IP + "/motor/off"
LED_GREEN_URL = NODEMCU_IP + "/led/green"
LED_RED_URL = NODEMCU_IP + "/led/red"

CLOSE_THRESH = 0.25       # normalized eye closure threshold
EYE_CONSEC_FRAMES = 3     # frames to confirm eyes closed
NODEMCU_PING_INTERVAL = 1.0
GRACE_FRAMES = 3          # frames to wait if face disappears temporarily

# ---------------- GLOBALS ----------------
node_connected = False

# ---------------- FACE/EYE SETUP ----------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False,
                                  max_num_faces=1,
                                  refine_landmarks=True,
                                  min_detection_confidence=0.5,
                                  min_tracking_confidence=0.5)

# Iris vertical landmarks for detecting eye closure
LEFT_EYE_VERT = [159, 145]
RIGHT_EYE_VERT = [386, 374]
# Eye corners for normalization
LEFT_EYE_HOR = [33, 133]
RIGHT_EYE_HOR = [263, 362]

# ---------------- BUZZER ----------------
class BuzzerPlayer:
    def __init__(self, freq=1000, volume=0.08):
        self.freq = freq
        self.volume = volume
        self.on = False  # tone flag
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        p = pyaudio.PyAudio()
        fs = 44100
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=fs,
                        output=True)
        chunk = 1024
        t = 0
        while True:
            if self.on:
                samples = (np.sin(2*np.pi*np.arange(chunk)*self.freq/fs + t)).astype(np.float32)
                stream.write(self.volume * samples)
                t += 2*np.pi*chunk*self.freq/fs
            else:
                time.sleep(0.05)

    def start(self):
        self.on = True

    def stop(self):
        self.on = False

buzzer = BuzzerPlayer(freq=1000, volume=0.08)

# ---------------- HELPER FUNCTIONS ----------------
def euclidean(a, b):
    return math.dist(a, b)

def normalized_eye_ratio(lm, vert_pts, hor_pts, img_w, img_h):
    top = (lm[vert_pts[0]].x * img_w, lm[vert_pts[0]].y * img_h)
    bottom = (lm[vert_pts[1]].x * img_w, lm[vert_pts[1]].y * img_h)
    vert_dist = euclidean(top, bottom)
    left_corner = (lm[hor_pts[0]].x * img_w, lm[hor_pts[0]].y * img_h)
    right_corner = (lm[hor_pts[1]].x * img_w, lm[hor_pts[1]].y * img_h)
    hor_dist = euclidean(left_corner, right_corner)
    return vert_dist / hor_dist, top, bottom

def send_get(url, timeout=0.5):
    try:
        resp = requests.get(url, timeout=timeout)
        print(f"[HTTP] GET {url} -> {resp.status_code}: {resp.text}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to reach {url}: {e}")
        return False

# ---------------- NODEMCU CONNECTION TRACKER ----------------
def node_tracker():
    global node_connected
    while True:
        try:
            resp = requests.get(NODEMCU_IP, timeout=0.5)
            if resp.status_code == 200 and not node_connected:
                print("[INFO] NodeMCU Connected")
            node_connected = True
        except:
            if node_connected:
                print("[WARN] NodeMCU Disconnected")
            node_connected = False
        time.sleep(NODEMCU_PING_INTERVAL)

tracker_thread = threading.Thread(target=node_tracker, daemon=True)
tracker_thread.start()

# ---------------- MAIN LOOP ----------------
cap = cv2.VideoCapture(0)
closed_frames = 0
eyes_closed = False
lost_face_counter = 0
driver_status = "UNKNOWN"

# Initial state
send_get(MOTOR_ON_URL)
send_get(LED_GREEN_URL)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        img_h, img_w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            lost_face_counter = 0
            lm = results.multi_face_landmarks[0].landmark

            # Left eye
            left_ratio, left_top, left_bottom = normalized_eye_ratio(lm, LEFT_EYE_VERT, LEFT_EYE_HOR, img_w, img_h)
            # Right eye
            right_ratio, right_top, right_bottom = normalized_eye_ratio(lm, RIGHT_EYE_VERT, RIGHT_EYE_HOR, img_w, img_h)

            # Draw eye points
            for pt in [left_top, left_bottom, right_top, right_bottom]:
                cv2.circle(frame, (int(pt[0]), int(pt[1])), 2, (0,255,0), -1)

            # Check eyes
            if left_ratio < CLOSE_THRESH and right_ratio < CLOSE_THRESH:
                closed_frames += 1
            else:
                closed_frames = 0

            # Continuous state handling
            if closed_frames >= EYE_CONSEC_FRAMES:
                eyes_closed = True
                driver_status = "SLEEPING"
                buzzer.start()              # start tone
                send_get(MOTOR_OFF_URL)
                send_get(LED_RED_URL)
            else:
                eyes_closed = False
                driver_status = "ACTIVE"
                buzzer.stop()               # stop tone
                send_get(MOTOR_ON_URL)
                send_get(LED_GREEN_URL)

        else:
            # Face lost
            lost_face_counter += 1
            if lost_face_counter >= GRACE_FRAMES:
                eyes_closed = False
                driver_status = "NO FACE"
                buzzer.stop()
                send_get(MOTOR_ON_URL)

        # Overlay driver status
        cv2.putText(frame, f"Driver Status: {driver_status}", (10,60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0,255,0) if driver_status=="ACTIVE" else (0,0,255), 2)

        # Overlay NodeMCU connection status
        conn_text = "NodeMCU Connected" if node_connected else "NodeMCU Disconnected"
        cv2.putText(frame, conn_text, (10,90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0,255,0) if node_connected else (0,0,255), 2)

        cv2.imshow("Driver Assist - Press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    buzzer.stop()
    cap.release()
    cv2.destroyAllWindows()
