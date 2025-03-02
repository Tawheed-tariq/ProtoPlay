import streamlit as st
from network import create_hub, add_device, get_devices, create_direct_link, send_data, get_hubs

st.title("🌐 Network Simulator (Multiple Hubs & Direct Links)")

# Create a Hub
st.header("🏢 Create a Hub")
hub_name = st.text_input("Enter Hub Name:")
if st.button("Create Hub"):
    st.success(create_hub(hub_name))

# Add a Device
st.header("🔌 Add a Device")
device_name = st.text_input("Device Name")
mac_address = st.text_input("MAC Address")

# Get the updated list of hubs
available_hubs = get_hubs()
selected_hub = st.selectbox("Select a Hub", [""] + available_hubs)

if st.button("Connect Device"):
    if selected_hub:
        st.success(add_device(device_name, mac_address, selected_hub))
    else:
        st.error("Please select a hub!")

# Show Connected Devices
st.header("📋 Connected Devices")
devices = get_devices()
if devices:
    st.table(devices)
else:
    st.info("No devices connected.")

# Create Direct Link
st.header("🔗 Create Direct Connection")
if len(devices) >= 2:
    device1 = st.selectbox("Select Device 1", [d["Device Name"] for d in devices])
    device2 = st.selectbox("Select Device 2", [d["Device Name"] for d in devices if d["Device Name"] != device1])
    if st.button("Create Direct Link"):
        st.success(create_direct_link(device1, device2))

# Send Data
st.header("📩 Send Data")
if len(devices) >= 2:
    sender = st.selectbox("Sender", [d["Device Name"] for d in devices])
    receiver = st.selectbox("Receiver", [d["Device Name"] for d in devices if d["Device Name"] != sender])
    message = st.text_input("Message")
    transmission_method = st.radio("Choose Transmission Method", ["Hub", "Direct Link"])

    if st.button("Send"):
        st.success(send_data(sender, receiver, message, transmission_method))
else:
    st.warning("At least 2 devices required to send data!")