import math
import time
from threading import Thread

import matplotlib.pyplot as plt
import numpy as np
import scipy
import scipy.signal
import sounddevice as sd
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from matplotlib.animation import FuncAnimation
from playsound import playsound
from pythonosc import dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from scipy.interpolate import interp1d

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
CORS(app)


# Network Variables
ip = "0.0.0.0"
http_port = 8080 # /tcp
osc_port = 5000 # /udp

# Muse Variables
hsi = [4,4,4,4]
abs_waves = [-1,-1,-1,-1,-1]
rel_waves = [-1,-1,-1,-1,-1]

# Audio Variables
alpha_sound_threshold = 0.6
sound_file = "bell.mp3"

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
    global hsi
    hsi = args
    print(hsi)
    if hsi == (1.0, 1.0, 1.0, 1.0):
        print("Muse fit good")
    else:
        print("Muse fit bad:    " + '   '.join(["Left Ear", "Left Forehead", "Right Forehead", "Right Ear"][i] for i in range(len(hsi)) if hsi[i] != 1.0))


# Frequency band handler
def abs_handler(address: str, *args):
    global hsi, abs_waves, rel_waves
    wave = args[0][0]
    
    if any(hsi):
        if len(args) == 2:
            # OSC Stream Brainwaves = Average Onle
            # Single value for all sensors, already filtered for good data
            abs_waves[wave] = args[1]
        if (len(args)==5): #If OSC Stream Brainwaves = All Values
            sumVals=0
            countVals=0            
            for i in [0,1,2,3]:
                if hsi[i]==1: #Only use good sensors
                    countVals+=1
                    sumVals+=args[i+1]
            abs_waves[wave] = sumVals/countVals
            
        rel_waves[wave] = math.pow(10,abs_waves[wave]) / (math.pow(10,abs_waves[0]) + math.pow(10,abs_waves[1]) + math.pow(10,abs_waves[2]) + math.pow(10,abs_waves[3]) + math.pow(10,abs_waves[4]))
        update_plot_vars(wave)
        if (wave==2 and len(plot_data[0])>10): #Wait until we have at least 10 values to start testing
            test_alpha_relative()


# Raw EEG data handler
def eeg_handler(address: str, *args):
    global queue, playing
    queue.append(sum(args) / len(args))
    if len(queue) == WINDOW_SIZE_SAMPLES + 1:
        print("Queue filled at time", time.time() - start)
        print(min(queue), max(queue))
        # These numbers in the queue are in the range of 0 to +2048 (?)
        # However, most of the time they are in the range of +600 to +900
        # The following code is an example that generates random sound (white noise):
        # sd.play(np.float32([random.randint(1, 10)/10 for i in range(44100)]), 44100)
        # We need to convert the EEG data in the queue to a range of -1 to +1 for the sound device
        # t = np.float32(queue)
        # t = interp.interp1d([600, 1000], [-1, 1])(queue)
        # t = interp.interp1d(np.linspace(0, WINDOW_SIZE_SAMPLES, len(t)), t, kind='cubic')(np.linspace(0, WINDOW_SIZE_SAMPLES, 44100))
        # Furthermore, EEG data is in the frequency range of 1Hz to 100Hz
        # However, sound data is in the frequency range of 440Hz to 880Hz
        # To do this, we need to fourier-transform the EEG data and bring up the frequency range to 440Hz to 880Hz
        t = (np.float32(queue)/1000-0.7)*20
        queue=[]
        t = scipy.signal.resample(t, 44100//3)
        t = np.fft.rfft(t)
        t = np.roll(t, 4000//20)
        t[0:4000//20] = 0
        t = np.fft.irfft(t)
        t = scipy.signal.resample(t, 44100)
        # Ensure that the sound is in the range of -1 to +1
        t = (t/2+0.5)*2-1
        while playing == True:
            pass
        playing = True
        sd.play(t, 44100//WINDOW_SIZE_SECONDS, blocking=True)
        # sd.play(t, 44100)
        # print("playing", t.max(), t.min())
        playing = False

#Audio test
def test_alpha_relative():
    alpha_relative = rel_waves[2]
    if (alpha_relative>alpha_sound_threshold):
        print ("BEEP! Alpha Relative: "+str(alpha_relative))
        playsound(sound_file)        
    
#Live plot
def update_plot_vars(wave):
    global plot_data, rel_waves, plot_val_count
    plot_data[wave].append(rel_waves[wave])
    plot_data[wave] = plot_data[wave][-plot_val_count:]

def plot_update(i):
    global plot_data
    global alpha_sound_threshold
    if len(plot_data[0])<10:
        return
    plt.cla()
    for wave in [0,1,2,3,4]:
        if (wave==0):
            colorStr = 'red'
            waveLabel = 'Delta'
        if (wave==1):
            colorStr = 'purple'
            waveLabel = 'Theta'
        if (wave==2):
            colorStr = 'blue'
            waveLabel = 'Alpha'
        if (wave==3):
            colorStr = 'green'
            waveLabel = 'Beta'
        if (wave==4):
            colorStr = 'orange'
            waveLabel = 'Gamma'
        plt.plot(range(len(plot_data[wave])), plot_data[wave], color=colorStr, label=waveLabel+" {:.4f}".format(plot_data[wave][len(plot_data[wave])-1]))        

    # Plot the theta / alpha ratio, demonstrated to be highly correlated with visual and spatial attention
    attention = [((a / b) if b != 0 else -1) for a, b in zip(plot_data[1], plot_data[2])]
    # plt.plot(range(len(plot_data[1])), attention, color='red', label='Visual & Spatial Attention (Theta / Alpha)')
    # Plot the beta / alpha ratio, demonstrated to be highly correlated with alertness and concentration
    alertness = [(1 - (b / a) if b != 0 else -1) for a, b in zip(plot_data[3], plot_data[2])]
    # plt.plot(range(len(plot_data[3])), alertness, color='green', label='Alertness & Concentration (Beta / Alpha)')
    # Average the attention and alertness ratios
    average = [(a + b) / 2 for a, b in zip(attention, alertness)]
    # Smooth the average
    if len(average) > 50:
        pass
        #print("Interpolating")
        # Resample the average
        #average = np.array(average)
        #average = np.interp(np.linspace(0, len(average) - 1, plot_val_count), np.linspace(0, len(average) - 1, len(average)), average)
        #average = interp1d(range(len(average)), average, kind='cubic')(range(len(average)))

    plt.plot(range(len(average)), average, color='black', label='Average Attention & Alertness')
    plt.plot([0,len(plot_data[0])],[alpha_sound_threshold,alpha_sound_threshold],color='black', label='Alpha Sound Threshold',linestyle='dashed')
    socketio.emit('plot', {"data": average[-1]})
    plt.ylim([0,1])
    plt.xticks([])
    plt.title('Mind Monitor - Relative Waves')
    plt.legend(loc='upper left')

    
def init_plot():
    ani = FuncAnimation(plt.gcf(), plot_update, interval=100)
    plt.tight_layout()
    plt.show()


@app.route('/api/v1/muse/', methods=['GET'])
def get_muse_data():
    return jsonify({"hsi": hsi, "abs_waves": abs_waves, "rel_waves": rel_waves})


@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('interface/', path)


@app.route('/spectrogram/<path:path>')
def send_spectrogram(path):
    return send_from_directory('spectrogram/build/', path)


@socketio.on('connect')
def on_join(data):
    print('Client joined from ' + request.remote_addr)


@socketio.on('disconnect')
def on_leave(data):
    print('Client left from ' + request.remote_addr)


if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()

    # Horseshoe
    dispatcher.map("/muse/elements/horseshoe", hsi_handler)

    # Absolute waves
    dispatcher.map("/muse/eeg", eeg_handler)
    
    # Frequency bands
    dispatcher.map("/muse/elements/delta_absolute", abs_handler, 0)
    dispatcher.map("/muse/elements/theta_absolute", abs_handler, 1)
    dispatcher.map("/muse/elements/alpha_absolute", abs_handler, 2)
    dispatcher.map("/muse/elements/beta_absolute",  abs_handler, 3)
    dispatcher.map("/muse/elements/gamma_absolute", abs_handler, 4)

    osc_server = ThreadingOSCUDPServer((ip, http_port), dispatcher)

    print(f"OSC Server: Listening on UDP port {osc_port}")
    Thread(target=osc_server.serve_forever, daemon=True).start()

    print(f"HTTP Server: Listening on TCP port {http_port}")
    Thread(target=lambda: socketio.run(app, host=ip, port=http_port, debug=False, use_reloader=False, ssl_context=('cert.pem', 'key.pem')), daemon=True).start()
    
    print(f"Plot: Starting")
    init_plot()
