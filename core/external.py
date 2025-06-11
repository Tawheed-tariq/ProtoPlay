import streamlit as st
from core.devices import EndDevice, Hub, Switch, Bridge, Router, http_handler, dns_handler, ftp_handler
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
        try:
            switch = Switch("Switch1")
            st.session_state.switches["Switch1"] = switch
            st.session_state.network.add_switch(switch)
            
            hub1 = Hub("Hub1")
            hub2 = Hub("Hub2")
            st.session_state.hubs["Hub1"] = hub1
            st.session_state.hubs["Hub2"] = hub2
            st.session_state.network.add_hub(hub1)
            st.session_state.network.add_hub(hub2)
            
            switch.connect(hub1)
            switch.connect(hub2)
            st.session_state.connections.extend([(switch, hub1), (switch, hub2)])
            
            for i in range(1, 4):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{i:02d}"
                ip = f"192.168.1.{i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                hub1.connect(device)
                st.session_state.connections.append((hub1, device))
            
            for i in range(4, 7):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{i:02d}"
                ip = f"192.168.1.{i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                device.assign_port(80, 'tcp', 'http', http_handler)
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
        try:
            router = Router("Router1")
            st.session_state.routers["Router1"] = router
            st.session_state.network.add_router(router)
            
            router.add_interface("eth0", "192.168.1.1", "00:1A:2B:3C:4D:01", "255.255.255.0")
            router.add_interface("eth1", "192.168.2.1", "00:1A:2B:3C:4D:02", "255.255.255.0")
            
            switch = Switch("Switch1")
            st.session_state.switches["Switch1"] = switch
            st.session_state.network.add_switch(switch)

            router.connect(switch, "eth0")
            switch.port_table[router] = len(switch.port_table)
            switch.set_port_vlan(router, 1)
            st.session_state.connections.append((router, switch))
                        
            for i in range(1, 5):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{10+i:02d}"
                ip = f"192.168.1.{10+i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                device.set_gateway("192.168.1.1")  
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                switch.connect(device)
                st.session_state.connections.append((switch, device))

            
            switch2 = Switch("Switch2")
            st.session_state.switches["Switch2"] = switch2
            st.session_state.network.add_switch(switch2)

            router.connect(switch2, "eth1")
            switch2.port_table[router] = len(switch2.port_table)
            switch2.set_port_vlan(router, 1)
            st.session_state.connections.append((router, switch2))
                        
            for i in range(5, 10):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{10+i:02d}"
                ip = f"192.168.2.{10+i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                device.set_gateway("192.168.2.1")  
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                switch2.connect(device)
                st.session_state.connections.append((switch2, device))
            
            st.success("Router Network created successfully!")
            return True
            
        except Exception as e:
            st.error(f"Error creating router network: {str(e)}")
            return False
    elif network_type == "hop_router_network":
        try:
            router1 = Router("Router1")
            st.session_state.routers["Router1"] = router1
            st.session_state.network.add_router(router1)
            
            router1.add_interface("fa0/0", "10.0.0.3", "00:1A:2B:3C:4D:01", "255.255.255.0")
            router1.add_interface("se1/1", "20.0.0.1", "00:1A:2B:3C:4D:02", "255.255.255.0")
            
            router2 = Router("Router2")
            st.session_state.routers["Router2"] = router2
            st.session_state.network.add_router(router2)
            router2.add_interface("se1/1", "30.0.0.1", "00:1A:2B:3C:4D:03", "255.255.255.0")
            router2.add_interface("fa0/0", "40.0.0.3", "00:1A:2B:3C:4D:04", "255.255.255.0")
            
            router3 = Router("Router3")
            st.session_state.routers["Router3"] = router3
            st.session_state.network.add_router(router3)
            router3.add_interface("se1/1", "20.0.0.2", "00:1A:2B:3C:4D:05", "255.255.255.0")
            router3.add_interface("se1/0", "30.0.0.2", "00:1A:2B:3C:4D:06", "255.255.255.0")
            
            router3.connect(router2, "se1/0", "se1/1")
            router3.connect(router1, "se1/1", "se1/1")

            # router1.connect(router3, "se1/1")
            # router2.connect(router3, "se1/0")
            
            router3.add_route("10.0.0.0", "255.255.255.0", "20.0.0.1", "se1/1")
            router3.add_route("40.0.0.0", "255.255.255.0", "30.0.0.1", "se1/0")
            
            router1.add_route("40.0.0.0", "255.255.255.0", "20.0.0.2", "se1/1")
            router1.add_route("30.0.0.0", "255.255.255.0", "20.0.0.2", "se1/1")
            
            router2.add_route("10.0.0.0", "255.255.255.0", "30.0.0.2", "se1/1")
            router2.add_route("20.0.0.0", "255.255.255.0", "30.0.0.2", "se1/1")

            st.session_state.connections.append((router1, router3))
            st.session_state.connections.append((router2, router3))
            
            switch1 = Switch("Switch1")
            st.session_state.switches["Switch1"] = switch1
            st.session_state.network.add_switch(switch1)

            router1.connect(switch1, "fa0/0")
            switch1.port_table[router1] = len(switch1.port_table)
            switch1.set_port_vlan(router1, 1)
            st.session_state.connections.append((router1, switch1))
                        
            for i in range(1, 3):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{10+i:02d}"
                ip = f"10.0.0.{i}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                device.set_gateway("10.0.0.3")  
                st.session_state.devices[device_id] = device
                st.session_state.network.add_device(device)
                switch1.connect(device)
                st.session_state.connections.append((switch1, device))
            
            switch2 = Switch("Switch2")
            st.session_state.switches["Switch2"] = switch2
            st.session_state.network.add_switch(switch2)

            router2.connect(switch2, "fa0/0")
            switch2.port_table[router2] = len(switch2.port_table)
            switch2.set_port_vlan(router2, 1)
            st.session_state.connections.append((router2, switch2))

            for i in range(3, 5):
                device_id = f"PC{i}"
                mac = f"00:1A:2B:3C:4D:{10+i:02d}"
                ip = f"40.0.0.{i-2}"
                device = EndDevice(device_id, mac, ip, "255.255.255.0")
                device.set_gateway("40.0.0.3")
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
        if st.button("Hop Router Netwrok"):
            if create_prebuilt_network("hop_router_network"):
                st.rerun()
    
    with col2:
        if st.button("Create Router Network"):
            if create_prebuilt_network("router_network"):
                st.rerun()
    
    
    st.markdown("""
    **Prebuilt Network Options:**
    - **Basic Hub-Switch Network**: 2 hubs connected to a switch, each with 3 devices
    - **Router Network**: Router connected to a switch with 4 devices
    - **Hop Router Network**: 3 Routers Connected to each other and two end routers connected to switches and each swithc connected to 2 devices.
    """)