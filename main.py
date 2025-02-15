import cv2
import socket
import time
from ultralytics import YOLO
from geopy.distance import geodesic
from playsound import playsound
import threading  # Chỉ dùng cho phát âm thanh cảnh báo (có thể giữ nguyên)

# ---------------------------
# Cấu hình toàn cục
# ---------------------------
HOST = '100.116.69.56'  # Địa chỉ IP của điện thoại
# HOST = "iphone-15-pro-max.tail095752.ts.net"
PORT = 11123             # Cổng đã cấu hình trên ứng dụng GPS
LABELS  = [30, 70, 120]

ALARM_COOLDOWN = 2  
last_alarm_time = 0

def play_alarm():
    playsound("alert.wav")

def convert_to_decimal(degree_min, direction):
    """
    Chuyển đổi tọa độ từ định dạng độ-phút (dmm) sang độ thập phân.
    Ví dụ: '1106.38561' với 'N' -> 11 + 6.38561/60
    """
    degree = int(float(degree_min) / 100)
    minute = float(degree_min) - degree * 100
    decimal = degree + minute / 60
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def init_gps():
    """
    Khởi tạo kết nối GPS qua socket ở chế độ non-blocking.
    """
    try:
        gps_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gps_sock.connect((HOST, PORT))
        gps_sock.setblocking(False)  # Chế độ non-blocking
        print("[GPS] Đã kết nối tới điện thoại.")
        return gps_sock
    except Exception as e:
        print("[GPS] Lỗi khi kết nối:", e)
        return None

def process_gps_data(gps_sock, last_position, last_time, current_speed):
    """
    Kiểm tra dữ liệu GPS có sẵn từ socket và cập nhật current_speed,
    last_position, last_time dựa trên dữ liệu mới.
    """
    try:
        data = gps_sock.recv(1024).decode('utf-8').strip()
    except BlockingIOError:
        # Không có dữ liệu mới
        data = ""
    except Exception as e:
        print("[GPS] Lỗi:", e)
        return current_speed, last_position, last_time

    if data and data.startswith('$GPRMC'):
        parts = data.split(',')
        if parts[2] == 'A':  # Dữ liệu hợp lệ
            lat = parts[3]
            lat_dir = parts[4]
            lon = parts[5]
            lon_dir = parts[6]

            latitude = convert_to_decimal(lat, lat_dir)
            longitude = convert_to_decimal(lon, lon_dir)
            current_time = time.time()

            if last_position is not None and last_time is not None:
                current_position = (latitude, longitude)
                distance = geodesic(last_position, current_position).meters
                time_diff = current_time - last_time
                if time_diff > 0:
                    speed_m_s = distance / time_diff  # m/s
                    speed_kmh = speed_m_s * 3.6       # km/h
                    current_speed = speed_kmh

            last_position = (latitude, longitude)
            last_time = current_time

    return current_speed, last_position, last_time

def main():
    global last_alarm_time

    print("[Vision] Đang load mô hình YOLOv5n sử dụng ultralytics...")
    # Load mô hình đã fine-tuned (đảm bảo file '30-70-120.pt' có sẵn)
    model = YOLO("./30-70-120.pt")
    print("[Vision] Mô hình đã được load.")

    # Khởi tạo kết nối GPS
    gps_sock = init_gps()
    last_position = None
    last_time = None
    current_speed = 0.0

    # Mở camera (thay đổi chỉ số nếu cần)
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

        # Cập nhật dữ liệu GPS nếu có dữ liệu mới
        if gps_sock:
            current_speed, last_position, last_time = process_gps_data(
                gps_sock, last_position, last_time, current_speed
            )

        # Sử dụng mô hình YOLO để nhận diện biển báo tốc độ
        results = model(frame)
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

        cspeed = current_speed  # Tốc độ hiện tại tính từ GPS

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
                # Phát âm thanh cảnh báo (sử dụng thread để không làm chậm vòng lặp)
                threading.Thread(target=play_alarm, daemon=True).start()
                last_alarm_time = now

        cv2.imshow("Speed Warning System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    if gps_sock:
        gps_sock.close()

if __name__ == "__main__":
    main()
