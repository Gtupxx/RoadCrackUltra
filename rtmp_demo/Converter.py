import cv2
import ffmpeg
import numpy as np


def process_rtmp_stream(input_rtmp_url, output_rtmp_url):
    """
    处理 RTMP 视频流：从输入地址拉流，转换为灰度图像，并推送到输出 RTMP 地址。

    :param input_rtmp_url: 输入 RTMP 流地址
    :param output_rtmp_url: 输出 RTMP 流地址
    """
    # 打开 RTMP 视频流
    cap = cv2.VideoCapture(input_rtmp_url)
    if not cap.isOpened():
        print("❌ 无法打开 RTMP 流:", input_rtmp_url)
        return

    # 获取视频流参数
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 启动 FFmpeg 推流进程
    process = (
        ffmpeg.input(
            "pipe:", format="rawvideo", pix_fmt="bgr24", s=f"{width}x{height}", r=fps
        )
        .output(
            output_rtmp_url,
            format="flv",
            vcodec="libx264",
            pix_fmt="yuv420p",
            r=fps,
            preset="ultrafast",
            tune="zerolatency",
            bufsize="500k",
        )
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ 读取视频帧失败")
                break

            # 转换为灰度图像
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)  # 保持三通道格式

            # 推流
            process.stdin.write(gray_frame.tobytes())

            # 显示本地窗口（可选）
            cv2.imshow("Gray Video", gray_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\n🛑 手动停止推流")

    finally:
        # 释放资源
        cap.release()
        process.stdin.close()
        process.wait()
        cv2.destroyAllWindows()
        print("✅ 推流已结束")


# 示例调用
if __name__ == "__main__":
    input_rtmp_url = "rtmp://127.0.0.1/live/stream"
    output_rtmp_url = "rtmp://127.0.0.1/live/out"
    process_rtmp_stream(input_rtmp_url, output_rtmp_url)
