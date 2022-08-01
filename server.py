import json
import math
import time
from queue import Queue
from threading import Thread

import matplotlib.pyplot as plt
import numpy as np
import scipy
import scipy.signal
import sounddevice as sd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sock import Sock
from matplotlib.animation import FuncAnimation
from pythonosc import dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
sock = Sock(app)
CORS(app)


# Network Variables
ip = "0.0.0.0"
http_port = 8080 # /tcp
osc_port = 5001 # /udp

# Muse Variables
hsi = (4, 4, 4, 4)
last_hsi = (-1, -1, -1, -1)
abs_waves = [-1, -1, -1, -1, -1]
rel_waves = [-1, -1, -1, -1,-1]
publish_queue = Queue()
attention = []
alertness = []
average = []

# Plot Array
plot_val_count = 200
plot_data = [[0],[0],[0],[0],[0]]

# Audio Data Queue
start = time.time()


# Horseshoe handler
def hsi_handler(address: str, *args):
    global hsi, last_hsi
    hsi = args
    if hsi == last_hsi:
        return
    if hsi == (1, 1, 1, 1):
        print("Muse fit good")
    else:
        print("Muse fit bad:    " + '   '.join(["Left Ear", "Left Forehead", "Right Forehead", "Right Ear"][i] for i in range(len(hsi)) if hsi[i] != 1.0))
    last_hsi = hsi


# Frequency band handler
def abs_handler(address: str, *args):
    global hsi, abs_waves, rel_waves

    """
    Waves:
    0: Delta (δ): 1-4Hz
    1: Theta (θ): 4-8Hz
    2: Alpha (α): 7.5-13Hz
    3: Beta (β): 13-30Hz
    4: Gamma (γ): 30-44Hz
    """
    wave = args[0][0]
    good_sensor_count = sum(1 for v in hsi if v == 1)
    
    if good_sensor_count:
        if len(args) == 2:
            # OSC Stream Brainwaves = Average Only
            # Single value for all sensors, already filtered for good data
            abs_waves[wave] = args[1]
        if len(args) == 5:
            # OSC Stream Brainwaves = All Sensors
            # Value for each sensor, already filtered for good data
            abs_waves[wave] = sum(v for i, v in enumerate(args[1:]) if hsi[i] == 1) / good_sensor_count
        rel_waves[wave] = math.pow(10,abs_waves[wave]) / (math.pow(10,abs_waves[0]) + math.pow(10,abs_waves[1]) + math.pow(10,abs_waves[2]) + math.pow(10,abs_waves[3]) + math.pow(10,abs_waves[4]))

        update_plot_vars(wave)


# Update the plot data based on the EEG data
def update_plot_vars(wave):
    global plot_data, rel_waves, plot_val_count
    plot_data[wave].append(rel_waves[wave]) # Add the new value to the plot data
    plot_data[wave] = plot_data[wave][-plot_val_count:] # Update the plot data based on the EEG data


# Update the plot
def plot_update(_):
    global plot_data, attention, alertness, average

    if len(plot_data[0]) < 10:
        return # Refuse to plot with less than 10 data points

    plt.cla() # Clear the plot

    for wave in [0, 1, 2, 3, 4]:
        color, wave_name = [("red", "Delta"), ("purple", "Theta"), ("blue", "Alpha"), ("green", "Beta"), ("orange", "Gamma")][wave]
        # plt.plot(range(len(plot_data[wave])), plot_data[wave], color=color, label=f"{wave_name} {plot_data[wave][len(plot_data[wave])-1]:.4f}")

    # Plot the theta / alpha ratio, demonstrated to be highly correlated with visual and spatial attention
    attention = [((a / b) if abs(b) > 0.1 else 0.5) for a, b in zip(plot_data[1], plot_data[2])]
    plt.plot(range(len(plot_data[1])), attention, color='red', label='Visual & Spatial Attention (Theta / Alpha)')

    # Plot the beta / alpha ratio, demonstrated to be highly correlated with alertness and concentration
    alertness = [((a / b) if abs(a) > 0.1 else 0.5) for a, b in zip(plot_data[3], plot_data[2])]
    plt.plot(range(len(plot_data[3])), alertness, color='green', label='Alertness & Concentration (Beta / Alpha)')

    # Plot the average of the attention and alertness ratios
    average = [((a + b) / 2) for a, b in zip(attention, alertness)]
    plt.plot(range(len(average)), average, color='black', label='Average Attention & Alertness')

    # Plot the activation threshold
    plt.plot([0, len(plot_data[0])], [0.5, 0.5], color='black', label='Activation Threshold', linestyle='dashed')

    # Publish the most recently-added plot data (ratio average)
    publish_value((attention[-1], alertness[-1], 0 if len(alertness) < 200 else sum(alertness) / len(alertness)))

    # Set the y-axis range
    plt.ylim(-1, 2)
    # Set the x-axis ticks
    plt.xticks([])

    # Set the plot title
    plt.title('Flowmodoro | All Metrics')

    # Set the plot legend location
    plt.legend(loc='upper left')


# Start the plot
def init_plot():
    ani = FuncAnimation(plt.gcf(), plot_update, interval=100) # Update the plot every 100ms
    plt.tight_layout() # Set the plot layout
    plt.show() # Show the plot


@app.route('/api/v1/muse/', methods=['GET'])
def get_muse_data():
    return jsonify({"hsi": hsi, "abs_waves": abs_waves, "rel_waves": rel_waves})


@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('interface/', path)


@app.route('/spectrogram/<path:path>')
def send_spectrogram(path):
    return send_from_directory('spectrogram/build/', path)


listening_clients = []


@sock.route('/ws')
def listen(ws):
    print("Client connected from", request.remote_addr)
    listening_clients.append(ws)
    while True:
        message = ws.receive()
        if message is None:
            break
        print("Received message:", message)
        for client in listening_clients:
            client.send(message)
    print("Client disconnected from", request.remote_addr)
    listening_clients.remove(ws)



def publish_value(value):
    # socketio.emit('plot', {'data': value})
    publish_queue.put(value)


def publish_value_task():
    while True:
        value = publish_queue.get()
        print("Publishing value", value)
        for ws in listening_clients:
            try:
                ws.send(json.dumps(value))
            except Exception as e:
                print("Error sending value to client:", e)
                listening_clients.remove(ws)


def blink_handler(address: str, *args):
    print('blink', args)


def jaw_clench_handler(address: str, *args):
    print('jaw', args)


address_list = set()
def default_handler(address: str, *args):
    address_list.add(address)
    # print(address_list)


@app.route('/api/v1/muse/eeg/is_attentive', methods=['GET'])
def is_attentive():
    return jsonify({
        "is_attentive": None if len(alertness) < 200 else sum(alertness) / len(alertness) > 1.6,
        "specific_value": None if len(alertness) < 200 else sum(alertness) / len(alertness),
    })


if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()

    # Horseshoe
    dispatcher.map("/muse/elements/horseshoe", hsi_handler)

    # Frequency bands
    dispatcher.map("/muse/elements/delta_absolute", abs_handler, 0)
    dispatcher.map("/muse/elements/theta_absolute", abs_handler, 1)
    dispatcher.map("/muse/elements/alpha_absolute", abs_handler, 2)
    dispatcher.map("/muse/elements/beta_absolute",  abs_handler, 3)
    dispatcher.map("/muse/elements/gamma_absolute", abs_handler, 4)

    # Muse Algorithms
    dispatcher.map("/muse/elements/blink", blink_handler)
    dispatcher.map("/muse/elements/jaw_clench", jaw_clench_handler)
    dispatcher.set_default_handler(default_handler)

    osc_server = ThreadingOSCUDPServer((ip, osc_port), dispatcher)

    print(f"OSC Server: Listening on UDP port {osc_port}")
    Thread(target=osc_server.serve_forever, daemon=True).start()

    print(f"HTTP Server: Listening on TCP port {http_port}")
    Thread(target=lambda: app.run(host=ip, port=http_port, debug=False, use_reloader=False), daemon=True).start()

    Thread(target=publish_value_task, daemon=True).start()

    if True:
        def random_data():
            import random
            while True:
                print("WARNING: Sending random data!")
                publish_value((random.random(), random.random(), random.random()))
                time.sleep(0.1)
        Thread(target=random_data, daemon=True).start()
    
    print(f"Plot: Starting")
    init_plot()
