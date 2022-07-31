import math
from queue import Queue
import time
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
osc_port = 5000 # /udp

# Muse Variables
hsi = (4, 4, 4, 4)
last_hsi = (-1, -1, -1, -1)
abs_waves = [-1, -1, -1, -1, -1]
rel_waves = [-1, -1, -1, -1,-1]
publish_queue = Queue()

# Plot Array
plot_val_count = 200
plot_data = [[0],[0],[0],[0],[0]]

# Audio Data Queue
queue = []
start = time.time()

# Audio Variables
WINDOW_SIZE_SECONDS = 1
WINDOW_SIZE_SAMPLES = 800//3.1*WINDOW_SIZE_SECONDS
playing = False


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


# Raw EEG data handler
def eeg_handler(address: str, *args):
    return
    global queue, playing
    queue.append(sum(args) / len(args))
    if len(queue) == WINDOW_SIZE_SAMPLES + 1:
        print("Queue filled at time", time.time() - start)
        print(min(queue), max(queue))
        # Raw EEG data uses the unit μV, in the range of 0 to +2048
        # Most of the time, they are in the range of +600 to +900
        # The sound device accepts values in the range of -1 to +1
        # EEG data is in the frequency range of 1Hz to 100Hz
        # Sound data is in the frequency range of 100Hz to 10,000Hz
        # An example of an octave is the range of 440Hz to 880Hz

        # t = interp.interp1d([600, 1000], [-1, 1])(queue)
        t = (np.float32(queue) / 1000 - 0.7) * 20
        queue = [] # Clear the queue
        t = scipy.signal.resample(t, 44100//3) # Frequency range stretching
        t = np.fft.rfft(t) # Apply a real short-time fast Fourier transform
        t = np.roll(t, 200) # Shift the frequency range upwards
        t[:200] = 0 # Zero out the low frequencies
        t = np.fft.irfft(t) # Apply an inverse real short-time fast Fourier transform
        t = scipy.signal.resample(t, 44100) # Complete the frequency range stretching
        t = (t/2+0.5)*2-1 # Ensure that the sound is in the range of -1 to +1

        while playing == True: # Wait until the sound is finished playing
            pass

        playing = True
        sd.play(t, 44100//WINDOW_SIZE_SECONDS, blocking=True) # Play the sound
        playing = False



# Start EEG handler in separate thread
def eeg_handler_wrapper(address: str, *args):
    Thread(target=eeg_handler, args=(address, *args)).start()


# Update the plot data based on the EEG data
def update_plot_vars(wave):
    global plot_data, rel_waves, plot_val_count
    plot_data[wave].append(rel_waves[wave]) # Add the new value to the plot data
    plot_data[wave] = plot_data[wave][-plot_val_count:] # Update the plot data based on the EEG data


# Update the plot
def plot_update(_):
    global plot_data

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
    alertness = [(1 - (b / a) if abs(b) > 0.1 else 0.5) for a, b in zip(plot_data[3], plot_data[2])]
    plt.plot(range(len(plot_data[3])), alertness, color='green', label='Alertness & Concentration (Beta / Alpha)')

    # Plot the average of the attention and alertness ratios
    average = [(a + b) / 2 for a, b in zip(attention, alertness)]
    plt.plot(range(len(average)), average, color='black', label='Average Attention & Alertness')

    # Plot the activation threshold
    plt.plot([0, len(plot_data[0])], [0.5, 0.5], color='black', label='Activation Threshold', linestyle='dashed')

    # Publish the most recently-added plot data (ratio average)
    publish_value(average[-1])

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
                ws.send(value)
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


if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()

    # Horseshoe
    dispatcher.map("/muse/elements/horseshoe", hsi_handler)

    # Absolute waves
    dispatcher.map("/muse/eeg", eeg_handler_wrapper)
    
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

    if False:
        def random_data():
            import random
            while True:
                print("WARNING: Sending random data!")
                socketio.emit('plot', {"data": random.random()})
                time.sleep(1)
        Thread(target=random_data, daemon=True).start()
    
    print(f"Plot: Starting")
    init_plot()
