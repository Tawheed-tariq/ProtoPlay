import streamlit as st
from port_manager import PortManager
from server import start_server
from client import start_client
import threading
import time

st.set_page_config(page_title="Network Simulator", layout="centered")
st.title("🖧 Network Simulator: Port & Process Communication")

if "pm" not in st.session_state:
    st.session_state.pm = PortManager()
if "logs" not in st.session_state:
    st.session_state.logs = []

pm = st.session_state.pm
logs = st.session_state.logs

# --- Step 1: Assign ports ---
st.subheader("1️⃣ Assign Ports")
col1, col2 = st.columns(2)

with col1:
    service = st.selectbox("Select well-known port for server", list(pm.well_known_ports.keys()))
    if st.button("Assign Server Port"):
        port = pm.assign_well_known_port(service)
        if port:
            st.session_state.server_port = port
            st.success(f"Server assigned to port {port}")
        else:
            st.error("Port already assigned!")

with col2:
    if st.button("Assign Ephemeral Port for Client"):
        port = pm.assign_ephemeral_port()
        st.session_state.client_port = port
        st.success(f"Client assigned to ephemeral port {port}")

# --- Step 2: Start Communication ---
if "server_port" in st.session_state and "client_port" in st.session_state:
    st.subheader("2️⃣ Start Communication")
    if st.button("Start Server and Client"):
        server_thread = threading.Thread(
            target=start_server,
            args=(st.session_state.server_port, logs),
            daemon=True
        )
        server_thread.start()

        time.sleep(1)  # Ensure server starts first

        start_client(
            st.session_state.server_port,
            st.session_state.client_port,
            logs
        )

# --- Step 3: Logs ---
st.subheader("3️⃣ Output Logs")
if logs:
    st.code("\n".join(logs))
else:
    st.info("No logs yet. Assign ports and start communication.")
