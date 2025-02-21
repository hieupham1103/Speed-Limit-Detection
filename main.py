import cv2
import time
import threading
import requests
import os
import math
import numpy as np
from dotenv import load_dotenv

from ultralytics import YOLO
from playsound import playsound
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# Load biến môi trường từ file .env
load_dotenv()

# Arduino Cloud credentials & property IDs
CLIENT_ID    = os.getenv("CLIENT_ID")
CLIENT_SECRET= os.getenv("CLIENT_SECRET")
THING_ID     = os.getenv("THING_ID")
PROPERTY_ID  = os.getenv("ACC_LINEAR_ID")

# Sensor IDs cho accelerometer và magnetometer
ACC_X_ID = os.getenv("ACC_X_ID")
ACC_Y_ID = os.getenv("ACC_Y_ID")
ACC_Z_ID = os.getenv("ACC_Z_ID")

MAG_X_ID = os.getenv("MAG_X_ID")
MAG_Y_ID = os.getenv("MAG_Y_ID")
MAG_Z_ID = os.getenv("MAG_Z_ID")

# Cấu hình YOLO và giới hạn tốc độ (km/h)
LABELS = [30, 70, 120]
ALARM_COOLDOWN = 2  # seconds

# Global variables (chung cho 2 thread)
last_alarm_time = 0
current_speed = 0.0  # km/h (tích lũy từ sensor)
acceleration = 0.0   # m/s², giá trị lấy từ Arduino Cloud (sau chuyển đổi)
bias_speed = 0
last_time = time.time()

# Một lock để bảo vệ cập nhật các biến chung (nếu cần)
sensor_lock = threading.Lock()


def play_alarm_sound():
    """Phát âm thanh cảnh báo khi vượt tốc độ."""
    playsound("alert.wav")


def fetch_oauth_token():
    """
    Lấy access token từ Arduino Cloud bằng OAuth2.
    """
    token_url = "https://api2.arduino.cc/iot/v1/clients/token"
    oauth_client = BackendApplicationClient(client_id=CLIENT_ID)
    oauth_session = OAuth2Session(client=oauth_client)
    token = oauth_session.fetch_token(
        token_url=token_url,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        include_client_id=True,
        audience="https://api2.arduino.cc/iot",
    )
    return token.get("access_token")


def compute_euler_angles(acc, mag):
    """
    Tính roll, pitch, yaw từ dữ liệu Accelerometer và Magnetometer.
    acc: [ax, ay, az] (m/s²)
    mag: [mx, my, mz]
    Trả về (roll, pitch, yaw) tính bằng radian.
    """
    ax, ay, az = acc
    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2))
    
    mx, my, mz = mag
    mag_x = mx * math.cos(pitch) + mz * math.sin(pitch)
    mag_y = mx * math.sin(roll) * math.sin(pitch) + my * math.cos(roll) - mz * math.sin(roll) * math.cos(pitch)
    yaw = math.atan2(-mag_y, mag_x)
    return roll, pitch, yaw


def euler_to_rot_matrix(roll, pitch, yaw):
    """
    Chuyển đổi góc Euler (roll, pitch, yaw) thành ma trận xoay 3x3.
    """
    R_x = np.array([
        [1, 0, 0],
        [0, math.cos(roll), -math.sin(roll)],
        [0, math.sin(roll), math.cos(roll)]
    ])
    R_y = np.array([
        [math.cos(pitch), 0, math.sin(pitch)],
        [0, 1, 0],
        [-math.sin(pitch), 0, math.cos(pitch)]
    ])
    R_z = np.array([
        [math.cos(yaw), -math.sin(yaw), 0],
        [math.sin(yaw), math.cos(yaw), 0],
        [0, 0, 1]
    ])
    return np.dot(R_z, np.dot(R_y, R_x))


def local_to_global(acc_local, acc, mag):
    """
    Chuyển vector gia tốc từ không gian local sang global.
    acc_local: vector gia tốc đo được (ví dụ [ACC_X, ACC_Y, ACC_Z])
    acc: vector accelerometer dùng để tính góc (có thể dùng trực tiếp dữ liệu acc_local)
    mag: vector magnetometer tương ứng.
    Trả về vector gia tốc trong hệ thống global.
    """
    roll, pitch, yaw = compute_euler_angles(acc, mag)
    R = euler_to_rot_matrix(roll, pitch, yaw)
    # Với ma trận xoay R từ global sang local, chuyển đổi ngược lại sử dụng chuyển vị
    R_inv = R.T
    return R_inv.dot(acc_local)


def get_acceleration(access_token):
    """
    Lấy dữ liệu gia tốc và từ trường từ Arduino Cloud, chuyển đổi sang hệ global.
    Trả về giá trị gia tốc theo phương ngang: sqrt(x² + y²) của vector global.
    """
    base_url = f"https://api2.arduino.cc/iot/v2/things/{THING_ID}/properties/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        # Lấy dữ liệu accelerometer
        acc_x = requests.get(base_url + ACC_X_ID, headers=headers).json()["last_value"]
        acc_y = requests.get(base_url + ACC_Y_ID, headers=headers).json()["last_value"]
        acc_z = requests.get(base_url + ACC_Z_ID, headers=headers).json()["last_value"]
        acc_local = np.array([acc_x, acc_y, acc_z])
        
        # Lấy dữ liệu magnetometer
        mag_x = requests.get(base_url + MAG_X_ID, headers=headers).json()["last_value"]
        mag_y = requests.get(base_url + MAG_Y_ID, headers=headers).json()["last_value"]
        mag_z = requests.get(base_url + MAG_Z_ID, headers=headers).json()["last_value"]
        mag = np.array([mag_x, mag_y, mag_z])
        
        # Chuyển vector gia tốc từ local sang global
        acc_global = local_to_global(acc_local, acc_local, mag)
        # Lấy gia tốc theo phương ngang (trục X và Y của global)
        print(acc_local)
        print(acc_global)
        horizontal_acc = math.sqrt(acc_global[0]**2 + acc_global[1]**2)
        return horizontal_acc
    except Exception as e:
        print("[Arduino Cloud] Error:", e)
        return 0


def detect_speed_limit(model, frame):
    """
    Sử dụng YOLO để phát hiện biển báo tốc độ từ frame.
    Trả về giới hạn tốc độ (km/h) nếu phát hiện, hoặc None nếu không.
    """
    results = model(frame, verbose=False)
    detected_limit = None
    best_score = 0
    for result in results:
        for box in result.boxes.data.tolist():
            x1, y1, x2, y2, score, cls = box
            if score > best_score:
                try:
                    best_score = score
                    detected_limit = LABELS[int(cls)]
                except Exception as e:
                    print("[YOLO] Label error:", e)
    return detected_limit


def sensor_thread_func(access_token):
    """
    Thread cập nhật giá trị gia tốc và tính tốc độ bằng cách tích phân gia tốc theo thời gian.
    """
    global last_time, current_speed, acceleration
    while True:
        acc_val = get_acceleration(access_token)
        if acc_val is not None:
            current_time = time.time()
            dt = current_time - last_time
            with sensor_lock:
                # Tích phân gia tốc: cộng dồn (Euler integration)
                current_speed = bias_speed + acc_val * dt * 3.6  # chuyển đổi từ m/s sang km/h
                acceleration = acc_val
                last_time = current_time
            print(f"[Sensor] Acc: {acceleration:.2f} m/s², Speed: {current_speed:.2f} km/h, Δt: {dt:.2f} s")
        else:
            print("[Sensor] No acceleration data.")


def main():
    global last_alarm_time, current_speed

    access_token = fetch_oauth_token()
    print("[Vision] Loading YOLOv5n model...")
    model = YOLO("./30-70-120.pt")
    print("[Vision] Model loaded.")

    # Khởi chạy thread sensor
    sensor_thread = threading.Thread(target=sensor_thread_func, args=(access_token,), daemon=True)
    sensor_thread.start()

    # Chạy detection trong main thread
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("[Vision] Cannot open camera.")
        return

    speed_limit = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Vision] Failed to grab frame.")
            break

        detected_limit = detect_speed_limit(model, frame)
        if detected_limit is not None:
            speed_limit = detected_limit

        with sensor_lock:
            cspeed = current_speed

        cv2.putText(frame, f"Speed: {cspeed:.2f} km/h", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        if speed_limit is not None:
            cv2.putText(frame, f"Speed Limit: {speed_limit:.2f} km/h", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        else:
            cv2.putText(frame, "Speed Limit: No limit", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if speed_limit is not None and cspeed > speed_limit:
            cv2.putText(frame, "WARNING: Over Speed!", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if time.time() - last_alarm_time > ALARM_COOLDOWN:
                threading.Thread(target=play_alarm_sound, daemon=True).start()
                last_alarm_time = time.time()

        cv2.imshow("Speed Warning System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()