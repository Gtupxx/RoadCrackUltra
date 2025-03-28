from flask import Flask, Response, render_template, request
import cv2
import torch
from threading import Lock

app = Flask(__name__)

# 预设模型路径
PRESET_MODELS = {
    "yolov5s": "models/yolov5s.pt",  # 轻量模型
    "yolov5m": "models/yolov5m.pt",  # 中等模型
}

# 全局变量与线程锁（确保模型切换线程安全）
model = None
model_lock = Lock()


def load_model(model_name):
    """加载预设模型"""
    global model
    model_path = PRESET_MODELS.get(model_name)
    if not model_path:
        raise ValueError(f"模型 {model_name} 不存在")

    with model_lock:  # 加锁防止并发冲突
        # 释放旧模型内存（如果存在）
        if model is not None:
            del model
            torch.cuda.empty_cache()  # 清理 GPU 缓存（如果使用 GPU）

        # 加载新模型
        model = torch.hub.load(
            "ultralytics/yolov5", "custom", path=model_path, source="local"
        )
        model.conf = 0.5  # 设置置信度阈值
    return model


# 初始化默认模型
load_model("yolov5s")  # 启动时加载 yolov5s


def process_frame(frame):
    """处理帧并运行目标检测"""
    with model_lock:  # 确保模型在使用中不被切换
        if model is None:
            return frame
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = model(img_rgb)
        rendered_frame = results.render()[0]
        return cv2.cvtColor(rendered_frame, cv2.COLOR_RGB2BGR)


@app.route("/set_model")
def set_model():
    """切换模型接口"""
    model_name = request.args.get("name", "yolov5s")
    try:
        load_model(model_name)
        return f"已切换至模型: {model_name}", 200
    except Exception as e:
        return f"切换失败: {str(e)}", 500


def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        # 应用图像处理
        processed_frame = process_frame(frame)
        # 转换为 JPEG 格式
        ret, buffer = cv2.imencode(".jpg", processed_frame)
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    return render_template("index_yolo.html")


@app.route("/set_effect")
def set_effect():
    global effect
    effect = request.args.get("effect", "none")
    return "OK"


if __name__ == "__main__":
    app.run(debug=True)
