import streamlit as st
from core.csma_main import csmaCD
from core.layer_simulation import layerSimulation
from crc.crc import crc_error_detection
from FlowControl.stopAndWait import stopAndWait
from FlowControl.goBackN import go_back_n
st.set_page_config(page_title="Network Simulator", layout="wide")

st.title("Network Simulator")

st.sidebar.header("Selection")
selection_options = ["Layer Selection", "Simulation Selection"]
selected_option = st.sidebar.radio(
    "Select Mode",
    selection_options,
    index=0
)

if selected_option == "Layer Selection":
    st.session_state.selected_layer = True
    st.session_state.selected_simulation = None
else:
    simulation_options = ["CRC", "CSMA/CD", "Stop-and-Wait", "Go Back N"]
    selected_simulation = st.sidebar.radio(
        "Select Simulation",
        simulation_options,
        index=0
    )
    st.session_state.selected_simulation = selected_simulation
    st.session_state.selected_layer = False

if st.session_state.selected_layer:
    layerSimulation()

elif st.session_state.selected_simulation:
    selected_simulation = st.session_state.selected_simulation
    if selected_simulation == "CRC":
        crc_error_detection()
    elif selected_simulation == "CSMA/CD":
        csmaCD()
    elif selected_simulation == "Stop-and-Wait":
        stopAndWait()
    elif selected_simulation == "Go Back N":
        go_back_n()
    else:
        st.error("Invalid simulation selected.")
else:
    st.warning("Select a mode to begin simulation.")