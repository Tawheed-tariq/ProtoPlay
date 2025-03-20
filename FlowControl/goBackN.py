import streamlit as st
import time
import random

class SlidingWindowProtocol:
    def __init__(self, window_size):
        self.window_size = window_size
        self.frames = []
        self.acknowledged = []
        self.base = 0
        self.next_seq_num = 0

    def send_frame(self, frame):
        if self.next_seq_num < self.base + self.window_size:
            self.frames.append(frame)
            self.acknowledged.append(False)
            self.next_seq_num += 1
            return True
        return False

    def receive_ack(self, ack_num):
        if ack_num >= self.base:
            for i in range(self.base, ack_num + 1):
                self.acknowledged[i] = True
            self.base = ack_num + 1

    def get_window(self):
        return self.frames[self.base:self.base + self.window_size], self.acknowledged[self.base:self.base + self.window_size]


def go_back_n():
    st.title("Sliding Window Protocol Simulation")

    window_size = st.slider("Window Size", min_value=1, max_value=10, value=4)
    num_frames = st.slider("Number of Frames to Send", min_value=1, max_value=50, value=10)
    packet_loss_prob = st.slider("Packet Loss Probability", min_value=0.0, max_value=1.0, value=0.1)
    ack_loss_prob = st.slider("ACK Loss Probability", min_value=0.0, max_value=1.0, value=0.1)
    timeout_interval = st.slider("Timeout Interval (seconds)", min_value=0.1, max_value=5.0, value=2.0)
    start_simulation = st.button("Start Simulation")

    if start_simulation:
        protocol = SlidingWindowProtocol(window_size)

        st.write(f"Sending {num_frames} frames with a window size of {window_size}.")

        frame_num = 0
        ack_num = 0
        events = []
        timeouts = {}

        simulation_placeholder = st.empty()
        log_area = st.empty()
        progress_bar = st.progress(0)

        while frame_num < num_frames or protocol.base < num_frames:
            current_time = time.time()

            if frame_num < num_frames:
                if random.random() > packet_loss_prob:  
                    sent = protocol.send_frame(f"Frame {frame_num}")
                    if sent:
                        events.append(f"****** Sending Frame {frame_num}")
                        timeouts[frame_num] = current_time + timeout_interval
                        frame_num += 1
                else:
                    events.append(f"xxxxxx Frame {frame_num} lost during transmission")

            for frame_id, timeout_time in list(timeouts.items()):
                if current_time >= timeout_time and not protocol.acknowledged[frame_id]:
                    events.append(f"Timeout: Frame {frame_id} retransmitted")
                    timeouts[frame_id] = current_time + timeout_interval

            if random.random() > ack_loss_prob:  
                if ack_num < frame_num and not protocol.acknowledged[ack_num]:
                    protocol.receive_ack(ack_num)
                    events.append(f"-----> Received Acknowledgment for Frame {ack_num}")
                    timeouts.pop(ack_num, None)
                    ack_num += 1
            else:
                events.append(f"xxxxxx Acknowledgment for Frame {ack_num} lost")

            time.sleep(0.5)

            progress = min(protocol.base / num_frames, 1.0)
            progress_bar.progress(progress)

            event_html = "<div style='height: 500px; overflow-y: scroll; background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>"

            for event in events:
                if "xxxxxx" in event:
                    clean_event = event.replace("xxxxxx ", "")
                    event_html += f"<p style='color: red; margin: 5px 0;'>❌ {clean_event}</p>"
                elif "----->" in event:
                    clean_event = event.replace("-----> ", "")
                    event_html += f"<p style='color: green; margin: 5px 0;'>✓ {clean_event}</p>"
                elif "Timeout" in event:
                    event_html += f"<p style='color: orange; margin: 5px 0;'>⏱️ {event}</p>"
                elif "Sending Frame" in event:
                    event_html += f"<p style='color: blue; margin: 5px 0;'>📦 {event.replace('****** ', '')}</p>"
                else:
                    event_html += f"<p style='color: gray; margin: 5px 0;'>ℹ️ {event}</p>"

            event_html += "</div>"
            log_area.markdown(event_html, unsafe_allow_html=True)

        st.success("All frames sent and acknowledged.")

