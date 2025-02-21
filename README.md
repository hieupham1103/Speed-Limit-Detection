# Dự án Hệ thống Cảnh báo Vượt tốc độ

Một hệ thống tích hợp sử dụng Python, Arduino IoT Cloud và mô hình YOLO (Ultralytics YOLO11n) nhằm phát hiện biển báo tốc độ và tính toán vận tốc dựa trên dữ liệu cảm biến (Accelerometer, Magnetometer, v.v.). Hệ thống sẽ cảnh báo bằng âm thanh khi xe vượt quá giới hạn tốc độ được nhận diện thông qua biển báo tốc độ tư camera hành chình.

Dự án này được thực hiện cho môn MultiDisciplinary của ngành CSE trường Đại Học Việt Đức với mục tiêu tích hợp kiến thức từ các lĩnh vực IoT, Machine Learning và Xử lý tín hiệu.

---

## Giới thiệu

Dự án này có mục đích phát triển một ứng dụng cảnh báo vượt tốc độ bằng cách:
- **Nhận diện biển báo tốc độ:** Sử dụng mô hình YOLO đã được fine-tuned để nhận diện các biển báo tốc độ (ví dụ: 30 km/h, 70 km/h, 120 km/h) từ video do camera cung cấp.
- **Tính vận tốc từ cảm biến:** Lấy dữ liệu cảm biến từ Arduino Cloud qua REST API (Accelerometer và Magnetometer), chuyển đổi từ không gian local sang global bằng cách sử dụng các phép biến đổi Euler, sau đó tích phân gia tốc để tính vận tốc.
- **Cảnh báo:** Hiển thị thông tin vận tốc và giới hạn tốc độ trên video, đồng thời phát âm thanh cảnh báo khi xe vượt quá giới hạn.

Hệ thống được triển khai đa luồng, trong đó:
- **Sensor Thread:** Liên tục truy vấn dữ liệu từ Arduino Cloud và cập nhật giá trị gia tốc, tính toán vận tốc.
- **Main Thread:** Xử lý video, nhận diện biển báo tốc độ và hiển thị kết quả qua OpenCV (cv2.imshow).

---

## Tính năng

- **Tích hợp dữ liệu cảm biến từ Arduino Cloud:** Sử dụng REST API kèm OAuth2 để lấy dữ liệu Accelerometer và Magnetometer.
- **Chuyển đổi dữ liệu cảm biến:** Chuyển vector gia tốc từ hệ local sang hệ global dựa trên góc Euler tính từ Accelerometer và Magnetometer.
- **Tính vận tốc:** Tích phân gia tốc theo thời gian để ước lượng vận tốc hiện tại (km/h).
- **Nhận diện biển báo tốc độ:** Dùng mô hình YOLO11n (fine-tuned) để phát hiện biển báo tốc độ và xác định giới hạn tốc độ.
- **Cảnh báo âm thanh:** Phát cảnh báo khi xe vượt quá giới hạn tốc độ (với ngưỡng thời gian giữa các lần cảnh báo).
- **Hiển thị trực quan:** In thông tin vận tốc, giới hạn tốc độ và cảnh báo lên video.

---

## Yêu cầu

- **Python 3.7+**
- **Các thư viện Python:**
  - `opencv-python`
  - `ultralytics`
  - `playsound`
  - `requests`
  - `python-dotenv`
  - `oauthlib`
  - `requests_oauthlib`
  - `numpy`
- **Arduino IoT Cloud:**  
  Tài khoản Arduino IoT Cloud với thiết bị (Thing) và các thuộc tính cảm biến được cấu hình (Cần mua gói từ Entry trở lên để có thể dùng được API).
- **Camera:**  
  Để nhận diện biển báo tốc độ.
- **Mô hình YOLO:**  
  File mô hình đã được fine-tuned (ví dụ: `30-70-120.pt`).

---

## Cài đặt

1. **Clone repository:**

   ```bash
   git clone https://github.com/yourusername/your-project.git
   cd your-project
   ```

2. **Cài đặt các thư viện cần thiết:**
   ```bash
   pip install opencv-python ultralytics playsound requests python-dotenv oauthlib requests_oauthlib numpy
   ```

3. **Cấu hình file .env:**

   Tạo file `.env` trong thư mục gốc dự án và thêm các biến môi trường sau:

   ```ini
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   THING_ID=your_thing_id
   ACC_LINEAR_ID=your_acc_linear_property_id
   ACC_X_ID=your_acc_x_property_id
   ACC_Y_ID=your_acc_y_property_id
   ACC_Z_ID=your_acc_z_property_id
   MAG_X_ID=your_mag_x_property_id
   MAG_Y_ID=your_mag_y_property_id
   MAG_Z_ID=your_mag_z_property_id
   ```

4. **Chuẩn bị file mô hình YOLO:**

   Đảm bảo file mô hình (ví dụ `30-70-120.pt`) nằm trong thư mục dự án hoặc cập nhật đường dẫn chính xác trong code.

---

## Cấu trúc dự án

```
project/
├── main.py                # Code chính của dự án
├── 30-70-120.pt           # File mô hình YOLO đã fine-tuned
├── .env                   # File cấu hình biến môi trường
├── requirements.txt       # (Tùy chọn) Danh sách các thư viện cần thiết
└── README.md              # Tài liệu hướng dẫn dự án (README này)
```

---

## Cách sử dụng

1. **Kết nối Arduino IoT Cloud:**
   - Cấu hình thiết bị (Thing) trên Arduino IoT Cloud và xác định các thuộc tính cần thiết (Accelerometer, Magnetometer, Accelerometer_Linear,...).

2. **Chạy dự án:**

   ```bash
   python main.py
   ```

   - **Sensor Thread:** Sẽ liên tục truy vấn dữ liệu từ Arduino Cloud, chuyển đổi vector gia tốc sang hệ thống global và tích phân để tính vận tốc.
   - **Main Thread:** Sẽ mở camera, nhận diện biển báo tốc độ qua YOLO và hiển thị thông tin vận tốc, giới hạn tốc độ cùng cảnh báo nếu vượt quá.

3. **Đóng chương trình:**
   - Nhấn phím `q` trên cửa sổ video để thoát.

---

## Train lại mô hình detection để mở rộng biển báo
```
project/
└──/Train
    ├── datasets        # Dataset để train
    └──/train.ipynb     # Chạy file notebook này để train lại mô hình
```
---

# Cơ chế hoạt động của Hệ thống Cảnh báo Vượt tốc độ

Dự án sử dụng **Arduino IoT Cloud, OpenCV, YOLO (Deep Learning)** và các thuật toán xử lý tín hiệu để nhận diện biển báo tốc độ, tính toán vận tốc của phương tiện, và đưa ra cảnh báo nếu có vi phạm tốc độ. Hệ thống hoạt động theo các bước sau:

---

## 1. Thu thập dữ liệu cảm biến từ Arduino IoT Cloud
Hệ thống sử dụng các cảm biến gia tốc (**Accelerometer**) và từ trường (**Magnetometer**) được kết nối với **Arduino IoT Cloud**. Dữ liệu cảm biến này được đọc qua **REST API** của Arduino Cloud với cơ chế **OAuth2** để lấy thông tin theo thời gian thực.

### Quy trình lấy dữ liệu từ Arduino Cloud:
- Gửi yêu cầu **OAuth2** để lấy `access_token`.
- Dùng `access_token` để lấy dữ liệu từ các thuộc tính cảm biến trên thiết bị (`Thing`).
- Cảm biến gửi dữ liệu gia tốc (`ax, ay, az`) và từ trường (`mx, my, mz`) để xác định góc nghiêng của thiết bị.

---

## 2. Chuyển đổi dữ liệu cảm biến
### 2.1. Xác định góc quay của thiết bị (Orientation)
Từ dữ liệu **Magnetometer**, hệ thống xác định hướng của thiết bị trong không gian bằng cách tính toán **góc Euler** (Roll, Pitch, Yaw).  

Công thức tính Roll & Pitch từ gia tốc kế:  

$$
\text{Roll} = \arctan{\left(\frac{a_y}{a_z}\right)}
$$

$$
\text{Pitch} = \arctan{\left(\frac{-a_x}{\sqrt{a_y^2 + a_z^2}}\right)}
$$

$$
\text{Yaw} = \arctan{\left(\frac{m_y}{m_x}\right)}
$$

Từ đó, ta có thể suy ra ma trận biến đổi **Từ không gian local sang global**.

### 2.2. Chuyển đổi gia tốc từ local → global
Gia tốc đo từ **Accelerometer** là gia tốc trong hệ tọa độ của cảm biến, cần được chuyển sang hệ tọa độ toàn cục (global) bằng cách sử dụng ma trận xoay dựa trên góc Euler đã tính được.

$$
\begin{bmatrix} a_x^{(\text{global})} \\
a_y^{(\text{global})} \\
a_z^{(\text{global})}
\end{bmatrix}
= R \begin{bmatrix}
a_x^{(\text{local})} \\
a_y^{(\text{local})} \\
a_z^{(\text{local})}
\end{bmatrix}
$$

Với $R$ là ma trận quay dựa trên góc Euler.

### **2.3. Tính toán vận tốc từ gia tốc**
- **Tích phân dữ liệu gia tốc** để ước lượng vận tốc của phương tiện theo thời gian:

$$
v_x(t) = a_x(t) \cdot \Delta t
$$

$$
v_y(t) = a_y(t) \cdot \Delta t
$$

$$
v = \sqrt{v_x^2 + v_y^2}
$$

---

## 3. Nhận diện biển báo tốc độ từ video (YOLOv5n)
Hệ thống sử dụng mô hình **YOLOv5n** (phiên bản nhẹ, nhanh) để phát hiện biển báo tốc độ từ camera.  
- Dữ liệu video được lấy từ **camera gắn trên phương tiện** hoặc video phát lại.  
- Mô hình YOLO đã được **fine-tuned** trên tập dữ liệu chứa các biển báo tốc độ phổ biến (30 km/h, 50 km/h, 70 km/h, 120 km/h,...).  
- Khi YOLO phát hiện biển báo tốc độ, hệ thống sẽ đọc số giới hạn tốc độ từ bounding box.

### Quy trình nhận diện:
1. Đọc khung hình từ video.
2. Dùng YOLO để phát hiện biển báo tốc độ và đọc thông tin.
3. Lưu lại giá trị giới hạn tốc độ để so sánh với vận tốc tính được.

---

## 4. Cảnh báo nếu vượt tốc độ
Sau khi hệ thống có được **vận tốc hiện tại** và **giới hạn tốc độ**, hệ thống sẽ kiểm tra xem phương tiện có vượt quá tốc độ không:

$$
\text{Nếu } v_{\text{current}} > v_{\text{limit}}, \text{ phát cảnh báo!}
$$

### Cơ chế cảnh báo:
- **Hiển thị trên video**: In vận tốc hiện tại và giới hạn tốc độ lên màn hình bằng OpenCV.
- **Âm thanh cảnh báo**: Sử dụng `playsound` để phát cảnh báo âm thanh khi phương tiện vượt quá tốc độ.

---

## 5. Đa luồng để xử lý hiệu quả
Hệ thống được thiết kế theo mô hình **đa luồng (Multithreading)** để đảm bảo hiệu suất:
- **Thread 1: Lấy dữ liệu cảm biến từ Arduino Cloud, tính toán vận tốc.**
- **Thread 2: Nhận diện biển báo tốc độ từ camera.**
- **Main Thread: Xử lý hiển thị OpenCV, phát cảnh báo.**

**Lợi ích của đa luồng**:
- Đảm bảo không có độ trễ khi cập nhật dữ liệu cảm biến.
- Video được xử lý trơn tru, không bị giật lag.
- Cảnh báo được đưa ra **ngay lập tức** khi có vi phạm tốc độ.

---

## Liên hệ

Nếu có bất kỳ câu hỏi hoặc góp ý nào, vui lòng liên hệ qua [104240027@student.vgu.edu.vn](mailto:104240027@student.vgu.edu.vn).

