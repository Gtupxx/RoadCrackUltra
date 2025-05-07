import streamlit as st
import numpy as np
import time
import pandas as pd
import altair as alt
from collections import deque
import cv2  # 导入 OpenCV 库

time_window = 10
frame_times = deque(maxlen=1000)  # 存储时间戳
fps_history = deque(maxlen=1000)
drop_count_history = deque(maxlen=1000)
bandwidth_history = deque(maxlen=1000)
keyframe_interval_history = deque(maxlen=1000)  # 用来存储关键帧间隔

start_timestamp = time.time()  # 记录开始时间

def get_rtmp_frame(rtmp_url):
    # 初始化这些变量在函数内部
    last_fps_time = time.time() - start_timestamp  # 上次计算 FPS 的时间
    fps_interval = 1  # 每秒计算一次 FPS
    last_bandwidth_time = time.time() - start_timestamp  # 上次计算网速的时间
    drop_count = 0
    prev_time = time.time()

    # 使用 OpenCV 打开 RTMP 流
    cap = cv2.VideoCapture(rtmp_url)  
    last_keyframe_time = None  # 上次关键帧的时间

    while True:
        ret, frame = cap.read()  # 读取视频帧
        if not ret:
            drop_count += 1
            continue

        current_time = float(time.time() - start_timestamp)

        # 每秒更新 FPS
        if current_time - last_fps_time >= fps_interval:
            if len(frame_times) > 1:  # 确保队列中有足够的元素计算 FPS
                fps = len(frame_times) / (current_time - frame_times[0] + 1e-8)
            else:
                fps = 0
            fps_history.append(fps)
            last_fps_time = current_time  # 重置时间
        else:
            fps = fps_history[-1] if fps_history else 0
            fps_history.append(fps)

        # 每秒更新网速
        if current_time - last_bandwidth_time >= 1:
            bandwidth = np.random.uniform(0.9, 1.3)  # 模拟网速
            bandwidth_history.append(bandwidth)
            last_bandwidth_time = current_time  # 重置网速计算时间
        else:
            bandwidth = bandwidth_history[-1] if bandwidth_history else 0
            bandwidth_history.append(bandwidth)

        # 计算关键帧间隔
        if cap.get(cv2.CAP_PROP_POS_FRAMES) % cap.get(cv2.CAP_PROP_FPS) == 0:  # 检查是否为关键帧
            if last_keyframe_time is not None:
                keyframe_interval = current_time - last_keyframe_time
            else:
                keyframe_interval = 0
            keyframe_interval_history.append(keyframe_interval)  # 保存关键帧间隔
            last_keyframe_time = current_time  # 更新关键帧时间
        else:
            keyframe_interval = keyframe_interval_history[-1] if keyframe_interval_history else 0
            keyframe_interval_history.append(keyframe_interval)  # 保存非关键帧间隔

        if len(frame_times) > 0:
            while current_time - frame_times[0] > time_window:
                frame_times.popleft()
                fps_history.popleft()
                bandwidth_history.popleft()
                drop_count_history.popleft()
                keyframe_interval_history.popleft()

        # 记录数据
        frame_times.append(current_time)
        drop_count_history.append(drop_count)

        # 获取当前帧尺寸
        h, w, _ = frame.shape

        # 生成统计信息
        info_text = f"❌ 丢帧: {drop_count} | ⚡ FPS: {fps:.2f} | 📏 分辨率: {w}x{h} | 📡 网速: {bandwidth:.2f} Mbps"
        
        # 转换为 RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        yield frame_rgb, info_text, current_time

    cap.release()

# st.set_page_config(layout="wide")  # 宽屏模式
st.title("📡 RTMP 视频流播放（数据可视化）")

rtmp_url = st.text_input("输入 RTMP 直播地址", "rtmp://127.0.0.1/live/out")

if st.button("开始播放"):
    frame_generator = get_rtmp_frame(rtmp_url)
    last_window_start = time.time() - start_timestamp  # 上次窗口起点

    frame_display = st.image([])  # 视频展示
    stats_display = st.empty()  # 统计信息
    chart_display = st.empty()  # 折线图

    for frame, info_text, timestamp in frame_generator:
        # 🎥 更新视频
        frame_display.image(frame, channels="RGB", use_container_width=True)

        # 📊 更新统计信息
        stats_display.markdown(f"**{info_text}**")

        # ⏳ **控制坐标轴更新时间**（固定时间窗口）  
        if timestamp - last_window_start > time_window:
            last_window_start = timestamp - 3  # 更新窗口起点
            if len(frame_times) > 0:
                while frame_times[0] < last_window_start:
                    frame_times.popleft()
                    fps_history.popleft()
                    bandwidth_history.popleft()
                    drop_count_history.popleft()
                    keyframe_interval_history.popleft()

        # 📉 只更新数据，不重绘整个图表
        df = pd.DataFrame(
            {
                "时间": list(frame_times),
                "FPS": list(fps_history),
                "丢帧数": list(drop_count_history),
                "网速 (Mbps)": list(bandwidth_history),
                "关键帧间隔 (秒)": list(keyframe_interval_history),  # 添加关键帧间隔
            }
        )

        # ✅ 确保 df 不为空再渲染
        if not df.empty:
            # 🎨 使用 Altair 创建折线图
            # 将数据转换为长格式，用于同时绘制多个变量
            df_melted = df.melt(
                id_vars=["时间"],
                value_vars=["FPS", "丢帧数", "网速 (Mbps)", "关键帧间隔 (秒)"],  # 关键帧间隔也绘制在图表上
                var_name="Variable",
                value_name="Value",
            )

            # 创建图表
            chart = (
                alt.Chart(df_melted)
                .mark_line()
                .encode(
                    x=alt.X(
                        "时间:Q",
                        title="时间",
                        scale=alt.Scale(
                            domain=[last_window_start, last_window_start + time_window]
                        ),
                    ),
                    y=alt.Y("Value:Q", title="数值", scale=alt.Scale(zero=False)),
                    color="Variable:N",
                    tooltip=["时间:T", "Value:Q", "Variable:N"],
                )
                .properties(
                    title="实时视频数据（FPS、丢帧数、网速、关键帧间隔）", width="container"
                )
            )

            chart_display.altair_chart(chart, use_container_width=True)
