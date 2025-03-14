import streamlit as st
from core.csma_cd import csmaCD
from core.layer_simulation import layerSimulation
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
    st.session_state.selected_layer = 1
    layer_options = {1: "Physical Layer", 2: "Data Link Layer"}
    selected_layer = st.sidebar.radio(
        "Select Network Layer Focus",
        list(layer_options.keys()),
        format_func=lambda x: layer_options[x],
        index=st.session_state.selected_layer - 1
    )
    st.session_state.selected_layer = selected_layer
    st.session_state.selected_simulation = None
else:
    simulation_options = ["CRC", "CSMA/CD"]
    selected_simulation = st.sidebar.radio(
        "Select Simulation",
        simulation_options,
        index=0
    )
    st.session_state.selected_simulation = selected_simulation
    st.session_state.selected_layer = None

if st.session_state.selected_layer:
    layerSimulation(st.session_state.selected_layer, layer_options)

elif st.session_state.selected_simulation:
    selected_simulation = st.session_state.selected_simulation
    if selected_simulation == "CRC":
        st.write("CRC Simulation")
    elif selected_simulation == "CSMA/CD":
        csmaCD()
    else:
        st.error("Invalid simulation selected.")
else:
    st.warning("Select a mode to begin simulation.")