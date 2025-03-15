import streamlit as st
import matplotlib.pyplot as plt
import time
import random


def add_log(message, type="info"):
    if type == "success":
        st.session_state.log.append(f"-----> {message}")
    elif type == "error":
        st.session_state.log.append(f"xxxxxx {message}")
    else:
        st.session_state.log.append(f"****** {message}")

def draw_frame(frame,plot_area, status="sending"):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    
    # Draw sender and receiver
    ax.text(2, 5, "Sender", fontsize=14, ha='center', color='blue', weight='bold')
    ax.text(8, 5, "Receiver", fontsize=14, ha='center', color='green', weight='bold')
    
    # Draw sender and receiver boxes
    sender_box = plt.Rectangle((1, 4), 2, 2, fill=False, edgecolor='blue', linewidth=2)
    receiver_box = plt.Rectangle((7, 4), 2, 2, fill=False, edgecolor='green', linewidth=2)
    ax.add_patch(sender_box)
    ax.add_patch(receiver_box)
    
    # Draw frame moving based on status
    if status == "sending":
        position = 3 + (5 * 0.5)  # Halfway between sender and receiver
        color = 'black'
        ax.arrow(3, 5, position-3, 0, head_width=0.3, head_length=0.3, fc=color, ec=color, linewidth=2)
        ax.text(position, 5.5, f"Frame {frame}", fontsize=12, ha='center', color=color, weight='bold')
    elif status == "delivered":
        color = 'black'
        ax.arrow(3, 5, 4, 0, head_width=0.3, head_length=0.3, fc=color, ec=color, linewidth=2)
        ax.text(5, 5.5, f"Frame {frame}", fontsize=12, ha='center', color=color, weight='bold')
    elif status == "timeout":
        color = 'red'
        ax.arrow(3, 5, 2, 0, head_width=0.3, head_length=0.3, fc=color, ec=color, linewidth=2, linestyle='dashed')
        ax.text(4, 5.5, f"Frame {frame} (Lost)", fontsize=12, ha='center', color=color, weight='bold')
    elif status == "ack_sending":
        color = 'green'
        position = 7 - (4 * 0.5)  # Halfway between receiver and sender
        ax.arrow(7, 4.5, position-7, 0, head_width=0.3, head_length=0.3, fc=color, ec=color, linewidth=2)
        ax.text(position, 4, f"ACK {frame}", fontsize=12, ha='center', color=color, weight='bold')
    elif status == "ack_received":
        color = 'green'
        ax.arrow(7, 4.5, -4, 0, head_width=0.3, head_length=0.3, fc=color, ec=color, linewidth=2)
        ax.text(5, 4, f"ACK {frame}", fontsize=12, ha='center', color=color, weight='bold')
    elif status == "ack_lost":
        color = 'red'
        ax.arrow(7, 4.5, -2, 0, head_width=0.3, head_length=0.3, fc=color, ec=color, linewidth=2, linestyle='dashed')
        ax.text(6, 4, f"ACK {frame} (Lost)", fontsize=12, ha='center', color=color, weight='bold')
    
    ax.axis('off')
    plot_area.pyplot(fig)

def send_frame(frame,plot_area, frame_loss_prob, animation_speed):
    add_log(f"Sender: Sending Frame {frame}", "success")
    draw_frame(frame, plot_area, "sending")
    time.sleep(1/animation_speed)
    
    if random.random() > frame_loss_prob:  
        draw_frame(frame, plot_area, "delivered")
        add_log(f"Receiver: Frame {frame} received correctly", "success")
        time.sleep(1/animation_speed)
        return True
    else:
        draw_frame(frame,plot_area, "timeout")
        add_log(f"Receiver: Frame {frame} lost in transmission", "error")
        time.sleep(1/animation_speed)
        return False

def send_ack(frame,plot_area, ack_loss_prob, animation_speed):
    add_log(f"Receiver: Sending ACK {frame}", "success")
    draw_frame(frame,plot_area, "ack_sending")
    time.sleep(1/animation_speed)
    if random.random() > ack_loss_prob:  
        draw_frame(frame,plot_area, "ack_received")
        time.sleep(1/animation_speed)
        return True
    else:
        add_log(f"Receiver: ACK {frame} lost in transmission", "error")
        draw_frame(frame,plot_area, "ack_lost")
        time.sleep(1/animation_speed)
        return False

def run_simulation(frame_count, plot_area, status_area, log_area, timeout, ack_loss_prob, animation_speed, frame_loss_prob):
    st.session_state.simulation_running = True
    st.session_state.log = []
    st.session_state.current_frame = 0
    st.session_state.expected_frame = 0
    st.session_state.retransmissions = 0
    
    add_log("Starting simulation...\n")
    
    while st.session_state.current_frame < frame_count:
        current_frame = st.session_state.current_frame
        
        frame_delivered = send_frame(current_frame, plot_area,frame_loss_prob, animation_speed)
        
        if frame_delivered:
            ack_received = send_ack(current_frame, plot_area, ack_loss_prob, animation_speed)
            
            if ack_received:
                add_log(f"Sender: ACK {current_frame} received successfully", "success")
                st.session_state.current_frame += 1
            else:
                add_log(f"Sender: Timeout waiting for ACK {current_frame}", "error")
                st.session_state.retransmissions += 1
        else:
            add_log(f"Sender: Timeout", "error")
            st.session_state.retransmissions += 1
            
        progress = (st.session_state.current_frame / frame_count) * 100
        status_area.progress(int(progress))
        
        log_area.text_area("Simulation Log", "\n".join(st.session_state.log), height=300)
        
        if not frame_delivered or not ack_received:
            add_log(f"Waiting for timeout ({timeout} seconds)...")
            time.sleep(timeout/animation_speed)
    
    add_log(f"Simulation complete! Total frames: {frame_count}, Retransmissions: {st.session_state.retransmissions}")
    st.session_state.simulation_complete = True
    st.session_state.simulation_running = False

def stopAndWait():
    st.title("Stop-and-Wait ARQ Simulation")
    st.write("This simulation demonstrates the Stop-and-Wait ARQ protocol with customizable parameters.")

    st.header("Simulation Parameters")
    timeout = st.slider("Timeout (seconds)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    ack_loss_prob = st.slider("ACK Loss Probability", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
    frame_loss_prob = st.slider("Frame Loss Probability", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
    animation_speed = st.slider("Animation Speed", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
    frame_count = st.slider("Number of Frames to Send", min_value=1, max_value=20, value=5, step=1)

    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
        st.session_state.simulation_complete = False
        st.session_state.log = []
        st.session_state.current_frame = 0
        st.session_state.expected_frame = 0
        st.session_state.retransmissions = 0

    plot_area = st.empty()
    status_area = st.empty()
    log_area = st.empty()

    if st.button("Start Simulation", disabled=st.session_state.simulation_running):
        run_simulation(frame_count, plot_area, status_area, log_area, timeout, ack_loss_prob, animation_speed, frame_loss_prob)

    if st.session_state.simulation_complete:
        st.subheader("Simulation Results")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Frames", frame_count)
        with col2:
            st.metric("Retransmissions", st.session_state.retransmissions)
        with col3:
            efficiency = ((frame_count) / (frame_count + st.session_state.retransmissions)) * 100
            st.metric("Protocol Efficiency", f"{efficiency:.1f}%")
        
        if st.button("Reset Simulation"):
            st.session_state.simulation_complete = False
            st.rerun()