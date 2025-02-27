import streamlit as st
import json
import pandas as pd

# Tiêu đề trang
st.title("Speed & Acceleration History Viewer")

# Nhập client id từ người dùng
client_id = st.text_input("Enter Client ID", value="")

if client_id:
    try:
        # Load file JSON chứa lịch sử dữ liệu
        with open("database.json", "r") as f:
            history_data = json.load(f)

        # Kiểm tra xem client id có tồn tại trong dữ liệu không
        if client_id in history_data:
            # Chuyển dữ liệu thành DataFrame
            df = pd.DataFrame(history_data[client_id])
            # Chuyển đổi timestamp sang định dạng datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df = df.sort_values("timestamp")

            st.subheader(f"History for Client ID: {client_id}")
            st.write(df)

            # Biểu đồ tốc độ theo thời gian
            st.line_chart(df.set_index("timestamp")["speed"])
            # Biểu đồ gia tốc theo thời gian
            st.line_chart(df.set_index("timestamp")["acceleration"])
        else:
            st.error("Client ID not found in history data.")
    except Exception as e:
        st.error(f"Error loading file: {e}")
