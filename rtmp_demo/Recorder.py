import subprocess
import cv2

def start_rtmp_stream(rtmp_url):
    """
    从摄像头推流到指定的 RTMP 地址。
    """
    print(f"📡 正在推流到: {rtmp_url}")

    # 选择摄像头
    cap = cv2.VideoCapture(0)  # 0 代表默认摄像头
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    # 获取摄像头参数
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS) or 30)  # 有些摄像头无法正确返回 FPS，默认 30

    # FFmpeg 推流命令
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",  # 覆盖输出
        "-f", "rawvideo",
        "-pixel_format", "bgr24",
        "-video_size", f"{width}x{height}",
        "-framerate", str(fps),
        "-i", "-",  # 从标准输入读取视频流
        "-vcodec", "libx264",  # H.264 编码
        "-b:v", "1000k",  # 码率
        "-an",  # 不处理音频
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-tune", "zerolatency",  # 低延迟
        "-f", "flv",  # RTMP 使用 FLV 格式
        rtmp_url
    ]

    # 启动 FFmpeg 进程
    ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ 读取摄像头失败")
                break
            ffmpeg_process.stdin.write(frame.tobytes())

    except KeyboardInterrupt:
        print("\n🛑 结束推流...")

    finally:
        cap.release()
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()

if __name__ == "__main__":
    # rtmp_url = "rtmp://127.0.0.1/live/stream"
    rtmp_url = "rtmp://47.116.192.41/live/stream"
    start_rtmp_stream(rtmp_url)
    print("✅ 推流已停止")
