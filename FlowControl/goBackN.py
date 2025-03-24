import streamlit as st
import time
import random

class SlidingWindowProtocol:
    def __init__(self, window_size):
        self.window_size = window_size
        self.frames = [None] * 100  # Pre-allocate for potential frames
        self.acknowledged = [False] * 100  # Pre-allocate acknowledgment status
        self.base = 0  
        self.next_seq_num = 0  

    def send_frame(self, frame_num):
        if self.next_seq_num < self.base + self.window_size:
            self.frames[frame_num] = f"Frame {frame_num}"
            self.next_seq_num += 1
            return True
        return False

    def receive_ack(self, ack_num):
        if ack_num < self.base or ack_num >= self.next_seq_num:
            return False  
    
        for i in range(self.base, ack_num + 1):
            self.acknowledged[i] = True

        while self.base < self.next_seq_num and self.acknowledged[self.base]:
            self.base += 1

        return True

    def get_window(self):
        window_frames = []
        window_acks = []
        for i in range(self.base, min(self.base + self.window_size, self.next_seq_num)):
            window_frames.append(self.frames[i])
            window_acks.append(self.acknowledged[i])
        return window_frames, window_acks


def go_back_n():
    st.title("Go-Back-N Protocol Simulation")

    window_size = st.slider("Window Size", min_value=1, max_value=10, value=4)
    num_frames = st.slider("Number of Frames to Send", min_value=1, max_value=50, value=10)
    packet_loss_prob = st.slider("Packet Loss Probability", min_value=0.0, max_value=1.0, value=0.1)
    ack_loss_prob = st.slider("ACK Loss Probability", min_value=0.0, max_value=1.0, value=0.1)
    timeout_interval = st.slider("Timeout Interval (seconds)", min_value=0.1, max_value=5.0, value=2.0)
    transmission_delay = st.slider("Transmission Delay (seconds)", min_value=1.0, max_value=3.0, value=2.0)
    start_simulation = st.button("Start Simulation")

    if start_simulation:
        protocol = SlidingWindowProtocol(window_size)

        st.write(f"Sending {num_frames} frames with a window size of {window_size}.")

        events = []
        timeouts = {}
        current_time = time.time()
        
        expected_seq_num = 0  

        simulation_placeholder = st.empty()
        log_area = st.empty()
        progress_bar = st.progress(0)
        window_display = st.empty()

        while protocol.base < num_frames:
            current_time = time.time()
            
            for frame_id in range(protocol.base, protocol.next_seq_num):
                if frame_id in timeouts and current_time >= timeouts[frame_id] and not protocol.acknowledged[frame_id]:
                    events.append(f" Timeout: Frame {frame_id} lost, retransmitting all frames from {protocol.base}")
                    protocol.next_seq_num = protocol.base
                    for f in range(protocol.base, min(protocol.base + window_size, num_frames)):
                        timeouts.pop(f, None)
                    break
            
            while protocol.next_seq_num < num_frames and protocol.next_seq_num < protocol.base + window_size:
                frame_num = protocol.next_seq_num
                if protocol.send_frame(frame_num):
                    frame_lost = random.random() <= packet_loss_prob
                    if not frame_lost:
                        events.append(f"****** Sending Frame {frame_num}")
                        timeouts[frame_num] = current_time + timeout_interval
                        
                        if frame_num == expected_seq_num:
                            ack_lost = random.random() <= ack_loss_prob
                            if not ack_lost:
                                if protocol.receive_ack(frame_num):
                                    events.append(f"-----> Received Acknowledgment for Frame {frame_num}")
                                    timeouts.pop(frame_num, None)
                                    expected_seq_num = frame_num + 1
                            else:
                                events.append(f" ACK for Frame {frame_num} lost, waiting for timeout")
                        else:
                            events.append(f" Frame {frame_num} received out of order, discarding (expected {expected_seq_num})")
                    else:
                        events.append(f"xxxxxx Frame {frame_num} lost during transmission")
                else:
                    break
            
            progress = min(protocol.base / num_frames, 1.0)
            progress_bar.progress(progress)

            window_status = f"""
                <div style='background-color: rgba(30, 144, 255, 0.2); padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px solid rgba(30, 144, 255, 0.4);'>
                    <h3 style='color: #1e90ff;'>Current Window Status:</h3>
                    <p><strong>Base (First unacknowledged):</strong> {protocol.base}</p>
                    <p><strong>Next sequence number:</strong> {protocol.next_seq_num}</p>
                    <p><strong>Window size:</strong> {window_size}</p>
                    <p><strong>Receiver's expected sequence number:</strong> {expected_seq_num}</p>
                    <div style='display: flex; flex-wrap: wrap;'>
            """

            for i in range(max(0, protocol.base - 2), min(num_frames, protocol.base + window_size + 2)):
                if i < protocol.base:
                    window_status += f"<div style='margin: 5px; padding: 10px; background-color: rgba(40, 167, 69, 0.7); color: white; border-radius: 5px; border: 1px solid #28a745;'>Frame {i} ✓</div>"
                elif i >= protocol.base and i < min(protocol.next_seq_num, protocol.base + window_size):
                    if protocol.acknowledged[i]:
                        window_status += f"<div style='margin: 5px; padding: 10px; background-color: rgba(40, 167, 69, 0.7); color: white; border-radius: 5px; border: 1px solid #28a745;'>Frame {i} ✓</div>"
                    else:
                        window_status += f"<div style='margin: 5px; padding: 10px; background-color: rgba(0, 123, 255, 0.7); color: white; border-radius: 5px; border: 1px solid #007bff;'>Frame {i} 📤</div>"
                elif i >= protocol.next_seq_num and i < protocol.base + window_size:
                    window_status += f"<div style='margin: 5px; padding: 10px; background-color: rgba(108, 117, 125, 0.3); border-radius: 5px; border: 1px dashed #6c757d;'>Frame {i} 🔲</div>"
                else:
                    window_status += f"<div style='margin: 5px; padding: 10px; background-color: rgba(108, 117, 125, 0.1); border-radius: 5px; opacity: 0.6; border: 1px dotted #6c757d;'>Frame {i}</div>"

            window_status += "</div></div>"
            window_display.markdown(window_status, unsafe_allow_html=True)

            event_html = "<div style='height: 300px; overflow-y: scroll; background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>"
            
            for event in events:  
                if "xxxxxx" in event:
                    clean_event = event.replace("xxxxxx ", "")
                    event_html += f"<p style='color: red; margin: 5px 0;'>{clean_event}</p>"
                elif "----->" in event:
                    clean_event = event.replace("-----> ", "")
                    event_html += f"<p style='color: green; margin: 5px 0;'>{clean_event}</p>"
                elif "Timeout" in event:
                    event_html += f"<p style='color: orange; margin: 5px 0;'>{event}</p>"
                elif "Sending Frame" in event:
                    event_html += f"<p style='color: blue; margin: 5px 0;'>{event.replace('****** ', '')}</p>"
                else:
                    event_html += f"<p style='color: gray; margin: 5px 0;'>{event}</p>"
            
            event_html += "</div>"
            log_area.markdown(event_html, unsafe_allow_html=True)
            
            time.sleep(transmission_delay)

        st.success("All frames sent and acknowledged!")