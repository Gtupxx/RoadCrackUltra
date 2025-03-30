from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import re
import time  # 用于计算 FPS

app = Flask(__name__)
socketio = SocketIO(app)


# 示例处理函数：将图像转换为灰度图后再转回 BGR 格式（便于显示）喵~
def process_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return processed


# 用于计算 FPS
frame_times = []
fps_window = 3  # FPS 计算时间窗口，单位：秒


@app.route("/")
def index():
    return render_template("index_camera.html")


@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


@socketio.on("send_image")
def handle_image(data):
    image_data = data.get("image")
    # 去掉前缀 "data:image/png;base64,"
    img_str = re.sub("^data:image/.+;base64,", "", image_data)
    img_bytes = base64.b64decode(img_str)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    ret, buffer = cv2.imencode(".png", img)
    img_base64 = base64.b64encode(buffer).decode("utf-8")
    img_data_url = "data:image/png;base64," + img_base64

    # 发送原始图像给客户端
    emit("receive_image", {"image": img_data_url})


# @socketio.on('send_image')
# def handle_image(data):
#     global frame_times

#     image_data = data.get('image')
#     # 去掉前缀 "data:image/png;base64,"
#     img_str = re.sub('^data:image/.+;base64,', '', image_data)
#     img_bytes = base64.b64decode(img_str)
#     nparr = np.frombuffer(img_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

#     # 记录每一帧的处理时间
#     current_time = time.time()
#     frame_times.append(current_time)

#     # 移除超过时间窗口的帧
#     frame_times = [t for t in frame_times if current_time - t <= fps_window]

#     # 计算 FPS
#     fps = len(frame_times) / fps_window

#     processed_img = process_image(img)

#     # 在图像的左上角绘制平均 FPS 信息
#     font = cv2.FONT_HERSHEY_SIMPLEX
#     cv2.putText(processed_img, f'Avg FPS: {fps:.2f}', (10, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

#     ret, buffer = cv2.imencode('.png', processed_img)
#     processed_base64 = base64.b64encode(buffer).decode('utf-8')
#     processed_data_url = 'data:image/png;base64,' + processed_base64

#     # 发送处理后的图像给客户端
#     emit('receive_image', {'image': processed_data_url})

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", debug=True)
