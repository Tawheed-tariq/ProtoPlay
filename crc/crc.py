import streamlit as st 
import random

class CRC:
    def __init__(self):
        self.input_data = ""
        self.divisor = ""
        self.divident = ""
        self.result = ""
        self.len_divident = 0
        self.len_gen = 0
        self.len_inp = 0

    def fun_xor(self, a, b):
        """Performs XOR operation between two binary strings"""
        if a[0] == '0':
            return a[1:]
        else:
            return "".join('0' if a[i] == b[i] else '1' for i in range(self.len_gen))[1:]

    def modulo_div(self):
        """Performs the CRC division to get the remainder"""
        temp_div = self.divisor
        temp_divident = self.divident[:self.len_gen]
        j = self.len_gen

        while j < self.len_divident:
            temp_divident = self.fun_xor(temp_divident, temp_div)
            temp_divident += self.divident[j]
            j += 1

        self.result = self.input_data + self.fun_xor(temp_divident, temp_div)

    def getdata(self, input_data, divisor):
        """Takes input data and generator polynomial"""
        self.input_data = input_data
        self.divisor = divisor
        self.len_gen = len(self.divisor)
        self.len_inp = len(self.input_data)
        self.divident = self.input_data + '0' * (self.len_gen - 1)
        self.len_divident = len(self.divident)
        self.modulo_div()

    def receiver_side(self, data_rec):
        """Simulates the receiver side for CRC error detection"""
        temp_div = self.divisor
        temp_divident = data_rec[:self.len_gen]
        j = self.len_gen

        while j < len(data_rec):
            temp_divident = self.fun_xor(temp_divident, temp_div)
            temp_divident += data_rec[j]
            j += 1

        error = self.fun_xor(temp_divident, temp_div)
        return error, error == '0' * (self.len_gen - 1)

def introduce_noise(data, probability=0.1):
    """Randomly flips bits in the data based on probability"""
    data_list = list(data)
    for i in range(len(data_list)):
        if random.random() < probability:
            data_list[i] = '1' if data_list[i] == '0' else '0'
    return "".join(data_list)

def crc_error_detection():
    st.title("CRC Error Detection ")

    st.subheader("Sender Side")
    input_data = st.text_input("Enter Input Data (Binary)")
    divisor = st.text_input("Enter Generator Polynomial (Binary)")

    if st.button("Generate Codeword"):
        if input_data and divisor:
            crc = CRC()
            crc.getdata(input_data, divisor)
            st.success(f"Data to Send (with CRC): {crc.result}")
            st.session_state["codeword"] = crc.result
        else:
            st.error("Please enter both Input Data and Generator Polynomial")

    # Collapsible CRC Detection Section
    detection_section = st.expander("CRC Detection Section", expanded=False)
    with detection_section:
        use_generated_data = st.checkbox("Use Generated Codeword as Received Data")
        
        if use_generated_data and "codeword" in st.session_state:
            data_received = st.session_state["codeword"]
        else:
            data_received = st.text_input("Enter Received Data (Binary)")
        
        add_noise = st.checkbox("Add Noise to Received Data")
        if add_noise and data_received:
            noise_probability = st.slider("Select Noise Probability", 0.0, 0.5, 0.1, 0.05)
            data_received = introduce_noise(data_received, probability=noise_probability)
            st.warning(f"Noisy Data Received: {data_received}")
        
        if st.button("Check for Errors"):
            if data_received and divisor:
                crc = CRC()
                crc.getdata(input_data, divisor)
                error, is_correct = crc.receiver_side(data_received)
                st.info(f"Remainder: {error}")
                if is_correct:
                    st.success("Correct Data Received Without Any Error")
                else:
                    st.error("Data Received Contains Errors")
            else:
                st.error("Please enter both Received Data and Generator Polynomial")
