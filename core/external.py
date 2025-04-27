import streamlit as st
from core.devices import EndDevice, Hub, Switch, Bridge, Router
from core.network import Network
import time
from core.functions import visualize_topology, find_path, restore_connections, initialize_session_state

def create_prebuilt_network(network_type):
    """Create a prebuilt network configuration"""
    # Clear existing network
    for key in ['network', 'devices', 'hubs', 'switches', 'bridges', 'connections', 'messages', 'routers']:
        if key in st.session_state:
            del st.session_state[key]
    
    # Initialize fresh network
    initialize_session_state(Network)
    
    if network_type == "basic_hub_switch":
        # Create a basic network with 2 hubs connected to a switch, each with 3 devices
        try:
            # Create switch
            switch = Switch("Switch1")
            st.session_state.switches["Switch1"] = switch
            st.session_state.network.add_switch(switch)
            
            # Create hubs
            hub1 = Hub("Hub1")
            hub2 = Hub("Hub2")
            st.session_state.hubs["Hub1"] = hub1
            st.session_state.hubs["Hub2"] = hub2
            st.session_state.network.add_hub(hub1)
            st.session_state.network.add_hub(hub2)
            
            # Connect hubs to switch
            switch.connect(hub1)
            switch.connect(hub2)
            st.session_state.connections.extend([(switch, hub1), (switch, hub2)])
            
            # Create devices for Hub1
            for i in range(1, 4):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{i:02d}"
                ip = f"192.168.1.{i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                hub1.connect(device)
                st.session_state.connections.append((hub1, device))
            
            # Create devices for Hub2
            for i in range(4, 7):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{i:02d}"
                ip = f"192.168.1.{i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                hub2.connect(device)
                st.session_state.connections.append((hub2, device))
            
            st.success("Basic Hub-Switch Network created successfully!")
            return True
            
        except Exception as e:
            st.error(f"Error creating prebuilt network: {str(e)}")
            return False
    
    elif network_type == "router_network":
        # Create a more advanced network with a router, switch, and multiple devices
        try:
            # Create router
            router = Router("Router1")
            st.session_state.routers["Router1"] = router
            st.session_state.network.add_router(router)
            
            # Add router interface
            router.add_interface("eth0", "192.168.1.1", "00:1A:2B:3C:4D:01", "255.255.255.0")
            router.add_interface("eth1", "192.168.2.1", "00:1A:2B:3C:4D:02", "255.255.255.0")
            
            # Create switch
            switch = Switch("Switch1")
            st.session_state.switches["Switch1"] = switch
            st.session_state.network.add_switch(switch)

            # Connect router to switch
            router.connect(switch, "eth0")
            switch.port_table[router] = len(switch.port_table)
            switch.set_port_vlan(router, 1)
            st.session_state.connections.append((router, switch))
                        
            # Create devices
            for i in range(1, 5):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{10+i:02d}"
                ip = f"192.168.1.{10+i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                device.set_gateway("192.168.1.1")  # Set router as gateway
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                switch.connect(device)
                st.session_state.connections.append((switch, device))

            
            # Create switch
            switch2 = Switch("Switch2")
            st.session_state.switches["Switch2"] = switch2
            st.session_state.network.add_switch(switch2)

            # Connect router to switch
            router.connect(switch2, "eth1")
            switch2.port_table[router] = len(switch2.port_table)
            switch2.set_port_vlan(router, 1)
            st.session_state.connections.append((router, switch2))
                        
            # Create devices
            for i in range(5, 10):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{10+i:02d}"
                ip = f"192.168.2.{10+i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                device.set_gateway("192.168.2.1")  # Set router as gateway
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                switch2.connect(device)
                st.session_state.connections.append((switch2, device))
            
            st.success("Router Network created successfully!")
            return True
            
        except Exception as e:
            st.error(f"Error creating router network: {str(e)}")
            return False
    
    return False

def prebuilt_network_ui():
    """UI section for prebuilt networks"""
    st.subheader("Prebuilt Networks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Create Basic Hub-Switch Network"):
            if create_prebuilt_network("basic_hub_switch"):
                st.rerun()
    
    with col2:
        if st.button("Create Router Network"):
            if create_prebuilt_network("router_network"):
                st.rerun()
    
    st.markdown("""
    **Prebuilt Network Options:**
    - **Basic Hub-Switch Network**: 2 hubs connected to a switch, each with 3 devices
    - **Router Network**: Router connected to a switch with 4 devices
    """)