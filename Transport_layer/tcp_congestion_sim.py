import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

# Configure page
st.set_page_config(page_title="TCP Congestion Control Simulator", layout="wide")

# Title and introduction
st.title("📡 TCP Congestion Control Simulator")
st.markdown("""
Simulates the behavior of TCP congestion control with three phases:

- **Slow Start:** Exponential increase of congestion window
- **Congestion Avoidance:** Linear growth after `ssthresh` is reached
- **Fast Retransmit & Fast Recovery:** Triggered by packet loss

👉 Adjust the controls below to simulate network events and visualize how TCP adapts.
""")

# Sidebar inputs
st.sidebar.header("🛠 Simulation Controls")
max_rounds = st.sidebar.slider("Number of Rounds (Time Steps)", min_value=10, max_value=100, value=50)
ssthresh_init = st.sidebar.number_input("Initial Slow Start Threshold (ssthresh)", min_value=1, value=16)
loss_rounds = st.sidebar.multiselect(
    "Select Rounds Where Packet Loss Occurs (0-indexed)", 
    options=list(range(max_rounds)), 
    default=[]
)

# State setup
cwnd = 1.0
ssthresh = ssthresh_init
cwnd_history = []
state_history = []

# TCP state constants
SLOW_START = "Slow Start"
CONG_AVOID = "Congestion Avoidance"
FAST_RECOVERY = "Fast Recovery"
state = SLOW_START
recovery_start = -1

# Simulation loop
for round_num in range(max_rounds):
    loss = round_num in loss_rounds

    if state == SLOW_START:
        if loss:
            ssthresh = max(cwnd / 2, 1)
            cwnd = ssthresh + 3
            state = FAST_RECOVERY
            recovery_start = round_num
        else:
            cwnd *= 2
            if cwnd >= ssthresh:
                cwnd = ssthresh
                state = CONG_AVOID

    elif state == CONG_AVOID:
        if loss:
            ssthresh = max(cwnd / 2, 1)
            cwnd = ssthresh + 3
            state = FAST_RECOVERY
            recovery_start = round_num
        else:
            cwnd += 1

    elif state == FAST_RECOVERY:
        if round_num - recovery_start >= 3:
            cwnd = ssthresh
            state = CONG_AVOID
        elif loss:
            ssthresh = max(cwnd / 2, 1)
            cwnd = ssthresh + 3
            recovery_start = round_num

    cwnd_history.append(cwnd)
    state_history.append(state)

# Plotting
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(range(max_rounds), cwnd_history, marker='o', label="Congestion Window (cwnd)", color='black')

# Add vertical lines for losses
for i, loss_r in enumerate(loss_rounds):
    ax.axvline(loss_r, color='red', linestyle='--', alpha=0.6, label="Packet Loss" if i == 0 else "")

# Highlight phases with background color
for i in range(max_rounds):
    color = {"Slow Start": "green", "Congestion Avoidance": "blue", "Fast Recovery": "orange"}[state_history[i]]
    ax.axvspan(i, i + 1, color=color, alpha=0.07)

# Labels and legend
ax.set_title("TCP Congestion Control Behavior", fontsize=16)
ax.set_xlabel("Round Number", fontsize=12)
ax.set_ylabel("Congestion Window (cwnd in MSS)", fontsize=12)
ax.grid(True)
ax.legend(loc="upper left")
st.pyplot(fig)

# Detailed output
st.subheader("📊 Round-wise TCP State Data")
df = pd.DataFrame({
    "Round": list(range(max_rounds)),
    "Congestion Window (cwnd)": cwnd_history,
    "TCP Phase": state_history,
    "Packet Loss": ["Yes" if i in loss_rounds else "No" for i in range(max_rounds)]
})
st.dataframe(df.style.format({"Congestion Window (cwnd)": "{:.2f}"}))
