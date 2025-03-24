from core.csma_cd import Network, Node
import streamlit as st
import pandas as pd
import time
def csmaCD():
    st.title("CSMA/CD Protocol Simulation")
    
    st.header("Simulation Parameters")
    num_nodes = st.slider("Number of Nodes", 3, 10, 5)
    traffic_rate = st.slider("Traffic Generation Rate", 0.01, 0.3, 0.1)
    collision_probability = st.slider("Collision Probability", 0.0, 0.5, 0.1, 
                                      help="Probability of forcing additional collisions")
    simulation_speed = st.slider("Simulation Speed", 1, 10, 3)

    if 'network_csma' not in st.session_state or st.session_state.network_csma.collision_probability != collision_probability or len(st.session_state.network_csma.nodes) != num_nodes:
        st.session_state.network_csma = Network(num_nodes, collision_probability)
        st.session_state.step = 0
    
    if st.button("Reset Simulation"):
        st.session_state.network_csma = Network(num_nodes, collision_probability)
        st.session_state.step = 0
    
    if hasattr(st.session_state, 'network_csma'):
        st.session_state.network_csma.collision_probability = collision_probability
    
    col1, col2 = st.columns(2)
    collision_stats_placeholder = col1.empty()
    node_stats_placeholder = col2.empty()
    
    history_placeholder = st.empty()
    
    if st.button("Run Simulation Step"):
        st.session_state.network_csma.generate_random_traffic(traffic_rate)
        st.session_state.network_csma.update()
        st.session_state.step += 1
        
        
        collision_stats = st.session_state.network_csma.get_collision_statistics()
        collision_stats_placeholder.subheader("Network Statistics")
        collision_stats_placeholder.json(collision_stats)
        
        stats_df = {
            "Node ID": [],
            "Queue Length": [],
            "Collisions": [],
            "Successful Tms": [],
            "Tms Attempts": []
        }
        
        for node in st.session_state.network_csma.nodes:
            stats_df["Node ID"].append(node.node_id)
            stats_df["Queue Length"].append(len(node.transmission_queue))
            stats_df["Collisions"].append(node.collision_count)
            stats_df["Successful Tms"].append(node.successful_transmissions)
            stats_df["Tms Attempts"].append(node.transmission_attempts)
        
        node_stats_placeholder.subheader("Node Statistics")
        node_stats_placeholder.dataframe(pd.DataFrame(stats_df))
        
        st.subheader("Event Log")
        if hasattr(st.session_state, 'network_csma'):
            events = st.session_state.network_csma.history
            event_html = "<div style='height: 800px; overflow-y: scroll; background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>"
            
            for event in events:
                    if "Collision" in event:
                        event_html += f"<p style='color: red; margin: 5px 0;'>{event}</p>"
                    elif "successfully transmitted" in event:
                        event_html += f"<p style='color: green; margin: 5px 0;'>{event}</p>"
                    elif "generated packet" in event:
                        event_html += f"<p style='color: blue; margin: 5px 0;'>{event}</p>"
                    elif "changed state" in event:
                        event_html += f"<p style='color: purple; margin: 5px 0;'> {event}</p>"
                    elif "continuing transmission" in event:
                        event_html += f"<p style='color: orange; margin: 5px 0;'>{event}</p>"
                    elif "Transmission progress" in event:
                        event_html += f"<p style='color: teal; margin: 5px 0;'>{event}</p>"
                    elif "Channel state" in event:
                        event_html += f"<p style='color: gray; margin: 5px 0;'> {event}</p>"
                    elif "in BACKOFF state" in event:
                        event_html += f"<p style='color: brown; margin: 5px 0;'> {event}</p>"
                    elif event.startswith("---"):
                        event_html += f"<p style='color: black; margin: 10px 0; font-weight: bold; border-top: 1px solid #ccc;'>{event}</p>"
                    else:
                        event_html += f"<p style='color: black; margin: 5px 0;'>{event}</p>"
            
            event_html += "</div>"
            st.markdown(event_html, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    steps_to_run = col1.number_input("Number of steps to run", min_value=10, max_value=1000, value=100, step=10)
    
    if col2.button(f"Auto Run ({steps_to_run} steps)"):
        progress_bar = st.progress(0)
        
        for i in range(int(steps_to_run)):
            st.session_state.network_csma.generate_random_traffic(traffic_rate)
            st.session_state.network_csma.update()
            st.session_state.step += 1
            
            progress_bar.progress((i+1)/steps_to_run)
            
            time.sleep(0.1 / simulation_speed)
            
            if i % num_nodes == 0 or i == steps_to_run-1:
                
                collision_stats = st.session_state.network_csma.get_collision_statistics()
                collision_stats_placeholder.subheader("Network Statistics")
                collision_stats_placeholder.json(collision_stats)
                
                stats_df = {
                    "Node ID": [],
                    "Queue Length": [],
                    "Collisions": [],
                    "Successful Tms": [],
                    "Tms Attempts": []
                }
                
                for node in st.session_state.network_csma.nodes:
                    stats_df["Node ID"].append(node.node_id)
                    stats_df["Queue Length"].append(len(node.transmission_queue))
                    stats_df["Collisions"].append(node.collision_count)
                    stats_df["Successful Tms"].append(node.successful_transmissions)
                    stats_df["Tms Attempts"].append(node.transmission_attempts)
                
                node_stats_placeholder.subheader("Node Statistics")
                node_stats_placeholder.dataframe(pd.DataFrame(stats_df))
                
                events = st.session_state.network_csma.history
                event_html = "<div style='height: 800px; overflow-y: scroll; background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>"
                
                for event in events:
                    if "Collision" in event:
                        event_html += f"<p style='color: red; margin: 5px 0;'>{event}</p>"
                    elif "successfully transmitted" in event:
                        event_html += f"<p style='color: green; margin: 5px 0;'>{event}</p>"
                    elif "generated packet" in event:
                        event_html += f"<p style='color: blue; margin: 5px 0;'>{event}</p>"
                    elif "changed state" in event:
                        event_html += f"<p style='color: purple; margin: 5px 0;'> {event}</p>"
                    elif "continuing transmission" in event:
                        event_html += f"<p style='color: orange; margin: 5px 0;'>{event}</p>"
                    elif "Transmission progress" in event:
                        event_html += f"<p style='color: teal; margin: 5px 0;'>{event}</p>"
                    elif "Channel state" in event:
                        event_html += f"<p style='color: gray; margin: 5px 0;'> {event}</p>"
                    elif "in BACKOFF state" in event:
                        event_html += f"<p style='color: brown; margin: 5px 0;'> {event}</p>"
                    elif event.startswith("---"):
                        event_html += f"<p style='color: black; margin: 10px 0; font-weight: bold; border-top: 1px solid #ccc;'>{event}</p>"
                    else:
                        event_html += f"<p style='color: black; margin: 5px 0;'>{event}</p>"
                
                event_html += "</div>"
                history_placeholder.markdown(event_html, unsafe_allow_html=True)