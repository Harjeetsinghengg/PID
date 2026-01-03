# Filename: pid_dashboard.py

import streamlit as st
import numpy as np
import pandas as pd
import time
from simple_pid import PID
import plotly.graph_objects as go

# ------------------------
# Streamlit App Settings
# ------------------------
st.set_page_config(page_title="PID Temperature Control", layout="wide")
st.title("🛠 PID Temperature Control Dashboard")

# ------------------------
# User Inputs
# ------------------------
st.sidebar.header("Process Settings")
setpoint = st.sidebar.slider("Desired Temperature (°C)", min_value=20, max_value=100, value=60, step=1)

st.sidebar.header("PID Settings")
Kp = st.sidebar.number_input("Kp (Proportional Gain)", min_value=0.0, value=2.0, step=0.1)
Ki = st.sidebar.number_input("Ki (Integral Gain)", min_value=0.0, value=0.1, step=0.01)
Kd = st.sidebar.number_input("Kd (Derivative Gain)", min_value=0.0, value=0.01, step=0.01)

st.sidebar.header("Simulation Settings")
sim_speed = st.sidebar.slider("Simulation Speed (ms per step)", 10, 500, 50)

# ------------------------
# Initialize PID Controller
# ------------------------
pid = PID(Kp, Ki, Kd, setpoint=setpoint)
pid.output_limits = (0, 100)  # Output throttle % (0-100)

# ------------------------
# Initialize Process Variables
# ------------------------
if 'temperature' not in st.session_state:
    st.session_state.temperature = 25.0  # initial temp
if 'throttle' not in st.session_state:
    st.session_state.throttle = 0.0

# ------------------------
# Process Simulation Function
# ------------------------
def simulate_process(temp, throttle):
    """
    Simple first-order process simulation
    temp: current temperature
    throttle: cooling output (%)
    """
    ambient_temp = 25
    heat_rate = 0.5  # heating constant
    cool_rate = 0.3 * (throttle/100)  # cooling proportional to throttle
    # Update temperature
    temp += heat_rate - cool_rate
    # Add some small random noise
    temp += np.random.normal(0, 0.05)
    return temp

# ------------------------
# Data Storage
# ------------------------
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Temperature', 'Throttle'])

# ------------------------
# Simulation Loop
# ------------------------
run_button = st.button("Start Simulation")

if run_button:
    st.session_state.running = True

if 'running' not in st.session_state:
    st.session_state.running = False

chart_area = st.empty()
table_area = st.empty()

t = 0

while st.session_state.running:
    # Update PID output based on current temperature
    pid.setpoint = setpoint
    throttle = pid(st.session_state.temperature)
    
    # Update process variable
    st.session_state.temperature = simulate_process(st.session_state.temperature, throttle)
    
    # Store history
    st.session_state.history = pd.concat([st.session_state.history,
                                          pd.DataFrame({'Time':[t],
                                                        'Temperature':[st.session_state.temperature],
                                                        'Throttle':[throttle]})], ignore_index=True)
    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=st.session_state.history['Time'], 
                             y=st.session_state.history['Temperature'],
                             mode='lines+markers', name='Temperature (°C)'))
    fig.add_trace(go.Scatter(x=st.session_state.history['Time'], 
                             y=st.session_state.history['Throttle'],
                             mode='lines+markers', name='Cooling Valve (%)',
                             yaxis='y2'))

    # Dual Y-axis
    fig.update_layout(
        yaxis=dict(title='Temperature (°C)'),
        yaxis2=dict(title='Throttle (%)', overlaying='y', side='right'),
        xaxis=dict(title='Time Steps'),
        title="Process Temperature & Cooling Valve PID Output",
        legend=dict(x=0, y=1)
    )
    
    chart_area.plotly_chart(fig, use_container_width=True)
    
    # Show latest values
    table_area.dataframe(st.session_state.history.tail(5))
    
    t += 1
    time.sleep(sim_speed/1000)
    
    # Stop button
    stop_button = st.button("Stop Simulation")
    if stop_button:
        st.session_state.running = False
        break
