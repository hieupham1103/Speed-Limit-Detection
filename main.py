import cv2
import time
from ultralytics import YOLO
from playsound import playsound
import threading

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import time

import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
THING_ID = os.getenv("THING_ID")
PROPERTY_ID = os.getenv("PROPERTY_ID")

LABELS  = [30, 70, 120]

ALARM_COOLDOWN = 2  
last_alarm_time = 0

acceleration = 0.0    # m/s², giá trị nhận từ Arduino Cloud
last_time = time.time()

def play_alarm():
    playsound("alert.wav")

def main():
    global last_alarm_time
    global last_time
    global acceleration
    
    oauth_client = BackendApplicationClient(client_id=CLIENT_ID)
    token_url = "https://api2.arduino.cc/iot/v1/clients/token"

    oauth = OAuth2Session(client=oauth_client)
    token = oauth.fetch_token(
        token_url=token_url,
        client_id= CLIENT_ID,
        client_secret=CLIENT_SECRET,
        include_client_id=True,
        audience="https://api2.arduino.cc/iot",
    )

    # store access token in access_token variable
    access_token = token.get("access_token")

    url = f"https://api2.arduino.cc/iot/v2/things/{THING_ID}/properties/{PROPERTY_ID}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    print("[Vision] Đang load mô hình YOLOv5n sử dụng ultralytics...")
    # Load mô hình đã fine-tuned (đảm bảo file '30-70-120.pt' có sẵn)
    model = YOLO("./30-70-120.pt")
    print("[Vision] Mô hình đã được load.")


    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("[Vision] Không thể mở camera.")
        return

    speed_limit = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Vision] Không nhận được frame từ camera.")
            break

        results = model(frame, verbose=False)
        temp_speed_limit, temp_score = None, 0
        for result in results:
            for box in result.boxes.data.tolist():
                x1, y1, x2, y2, score, cls = box
                if score > temp_score:
                    try:
                        temp_score = score
                        temp_speed_limit = LABELS[int(cls)]
                    except Exception as e:
                        print("Lỗi trong xử lý nhãn:", e)
                        pass
        if temp_speed_limit is not None:
            speed_limit = temp_speed_limit
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # print("Property Data:", data["last_value"])
            acceleration = max(0.0, data["last_value"] - 0.99)
            data["last_value"]
            current_time = time.time()
            dt = current_time - last_time
            # Tích phân: v = v_prev + a * dt (giả sử dữ liệu gia tốc ổn định giữa 2 lần đo)
            current_speed = acceleration * dt * 3.6  # chuyển đổi từ m/s sang km/h (nhân 3.6)
            last_time = current_time
            print(f"Acceleration: {acceleration:.2f} m/s², Speed: {current_speed:.2f} km/h, Delta Time: {dt:.2f} s")
        else:
            print("Error:", response.status_code, response.text)
        
        
        
        cspeed = current_speed
        
        cv2.putText(frame, f"Speed: {cspeed:.2f} km/h", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        if speed_limit is not None:
            cv2.putText(frame, f"Speed Limit: {speed_limit:.2f} km/h", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        else:
            cv2.putText(frame, f"Speed Limit: No limit", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if speed_limit is not None and cspeed > speed_limit:
            cv2.putText(frame, "WARNING: Over Speed!", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            now = time.time()
            if now - last_alarm_time > ALARM_COOLDOWN:
                threading.Thread(target=play_alarm, daemon=True).start()
                last_alarm_time = now

        cv2.imshow("Speed Warning System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
