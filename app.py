import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.graph_objects as go

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="PID Temperature Control", layout="wide")
st.title("🔥 PID Temperature Control Dashboard")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("Setpoint")
setpoint = st.sidebar.slider("Target Temperature (°C)", 20, 100, 60)

st.sidebar.header("PID Parameters")
Kp = st.sidebar.slider("Kp", 0.0, 10.0, 2.0, 0.1)
Ki = st.sidebar.slider("Ki", 0.0, 1.0, 0.1, 0.01)
Kd = st.sidebar.slider("Kd", 0.0, 1.0, 0.05, 0.01)

st.sidebar.header("Simulation Speed")
delay = st.sidebar.slider("Loop Delay (ms)", 50, 500, 100)

# -----------------------------
# Session State Init
# -----------------------------
if "temp" not in st.session_state:
    st.session_state.temp = 25.0

if "integral" not in st.session_state:
    st.session_state.integral = 0.0

if "prev_error" not in st.session_state:
    st.session_state.prev_error = 0.0

if "data" not in st.session_state:
    st.session_state.data = []

if "running" not in st.session_state:
    st.session_state.running = False

# -----------------------------
# PID Function
# -----------------------------
def pid_controller(sp, pv):
    error = sp - pv
    st.session_state.integral += error
    derivative = error - st.session_state.prev_error

    output = (
        Kp * error +
        Ki * st.session_state.integral +
        Kd * derivative
    )

    st.session_state.prev_error = error
    return max(0, min(100, output))  # Clamp 0–100%

# -----------------------------
# Process Model
# -----------------------------
def process_model(temp, valve):
    ambient = 25
    heating = 0.4
    cooling = 0.05 * valve
    noise = np.random.normal(0, 0.05)
    return temp + heating - cooling + noise

# -----------------------------
# Controls
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Start"):
        st.session_state.running = True

with col2:
    if st.button("⏹ Stop"):
        st.session_state.running = False

chart = st.empty()

# -----------------------------
# Main Loop
# -----------------------------
while st.session_state.running:
    valve = pid_controller(setpoint, st.session_state.temp)
    st.session_state.temp = process_model(st.session_state.temp, valve)

    st.session_state.data.append([
        len(st.session_state.data),
        st.session_state.temp,
        valve
    ])

    df = pd.DataFrame(
        st.session_state.data,
        columns=["Time", "Temperature", "Valve"]
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Time"], y=df["Temperature"],
        mode="lines", name="Temperature (°C)"
    ))
    fig.add_trace(go.Scatter(
        x=df["Time"], y=df["Valve"],
        mode="lines", name="Valve Output (%)",
        yaxis="y2"
    ))

    fig.update_layout(
        yaxis=dict(title="Temperature (°C)"),
        yaxis2=dict(
            title="Valve (%)",
            overlaying="y",
            side="right"
        ),
        title="PID Control – Temperature vs Valve",
        xaxis_title="Time Step"
    )

    chart.plotly_chart(fig, use_container_width=True)
    time.sleep(delay / 1000)
