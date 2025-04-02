import cv2
import numpy as np


def show_rtmp_stream(rtmp_url):
    cap = cv2.VideoCapture(rtmp_url)

    if not cap.isOpened():
        print("❌ 无法打开 RTMP 输出流")
        exit()

    while True:
        # 读取视频帧
        ret, oframe = cap.read()  # ret 表示是否读取成功，oframe 是读取到的帧
        if not ret:
            print("⚠️ 读取视频帧失败")
            break

        # 确保 oframe 是有效图像
        if oframe is not None:
            cv2.imshow("Output Video", oframe)

        # 如果按下 'q' 键则退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # 释放资源
    cap.release()
    
if __name__ == "__main__":
    # 显示 RTMP 输出流
    rtmp_url = "rtmp://127.0.0.1/live/out"

    print(f"📡 正在显示 RTMP 输出流: {rtmp_url}")
    show_rtmp_stream(rtmp_url)
    
    cv2.destroyAllWindows()
