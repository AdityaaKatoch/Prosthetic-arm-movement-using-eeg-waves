# Copyright (c) 2024 Umang Bansal
# 
# This software is the property of Umang Bansal. All rights reserved.
# Unauthorized copying of this file, via any medium, is strictly prohibited.
# Licensed under the MIT License. See the LICENSE file for details.

import serial
import numpy as np
from scipy import signal
import pandas as pd
import time
import pickle

from collections import deque

# Suppress sklearn warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

def setup_filters(sampling_rate):
    b_notch, a_notch = signal.iirnotch(50.0 / (0.5 * sampling_rate), 30.0)
    b_bandpass, a_bandpass = signal.butter(4, [0.5 / (0.5 * sampling_rate), 30.0 / (0.5 * sampling_rate)], 'band')
    return b_notch, a_notch, b_bandpass, a_bandpass

def process_eeg_data(data, b_notch, a_notch, b_bandpass, a_bandpass):
    data = signal.filtfilt(b_notch, a_notch, data)
    data = signal.filtfilt(b_bandpass, a_bandpass, data)
    return data

def calculate_psd_features(segment, sampling_rate):
    f, psd_values = signal.welch(segment, fs=sampling_rate, nperseg=len(segment))
    bands = {'alpha': (8, 13), 'beta': (14, 30), 'theta': (4, 7), 'delta': (0.5, 3)}
    features = {}
    for band, (low, high) in bands.items():
        idx = np.where((f >= low) & (f <= high))
        features[f'E_{band}'] = np.sum(psd_values[idx])
    features['alpha_beta_ratio'] = features['E_alpha'] / features['E_beta'] if features['E_beta'] > 0 else 0
    return features

def calculate_additional_features(segment, sampling_rate):
    f, psd = signal.welch(segment, fs=sampling_rate, nperseg=len(segment))
    peak_frequency = f[np.argmax(psd)]
    spectral_centroid = np.sum(f * psd) / np.sum(psd)
    log_f = np.log(f[1:])
    log_psd = np.log(psd[1:])
    spectral_slope = np.polyfit(log_f, log_psd, 1)[0]
    return {'peak_frequency': peak_frequency, 'spectral_centroid': spectral_centroid, 'spectral_slope': spectral_slope}

def load_model_and_scaler():
    with open('model.pkl', 'rb') as f:
        clf = pickle.load(f)
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    return clf, scaler

def main():
    ser_eeg = serial.Serial('COM9', 115200, timeout=1)  # Serial port for EEG data
    ser_servo = serial.Serial('COM10', 9600, timeout=1)  # Serial port for servo control (can be different)
    1
    clf, scaler = load_model_and_scaler()
    b_notch, a_notch, b_bandpass, a_bandpass = setup_filters(512)
    buffer = deque(maxlen=512)  # Buffer for EEG data

    while True:
        try:
            # Reading EEG data from the serial port (e.g., from EXG Pill or other EEG device)
            raw_data = ser_eeg.readline().decode('latin-1').strip()
            if raw_data:
                eeg_value = float(raw_data)
                buffer.append(eeg_value)

                if len(buffer) == 512:
                    buffer_array = np.array(buffer)
                    processed_data = process_eeg_data(buffer_array, b_notch, a_notch, b_bandpass, a_bandpass)
                    psd_features = calculate_psd_features(processed_data, 512)
                    additional_features = calculate_additional_features(processed_data, 512)
                    features = {**psd_features, **additional_features}

                    df = pd.DataFrame([features])
                    X_scaled = scaler.transform(df)
                    prediction = clf.predict(X_scaled)
                    print(f"Predicted Class: {prediction}")
                    buffer.clear()

                    # Output: Sending command to the servo based on prediction
                    if prediction == 0:
                        ser_servo.write(b'0')  # Send command to move the servo to position 0
                        print("Moving servo to position 0")
                    elif prediction == 1:
                        ser_servo.write(b'1')  # Send command to move the servo to position 1
                        print("Moving servo to position 1")

        except Exception as e:
            print(f'Error: {e}')
            continue

if __name__ == '__main__':
    main()
