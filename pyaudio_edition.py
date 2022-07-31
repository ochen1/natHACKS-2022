"""
Mind Monitor - Minimal EEG OSC Receiver
Coded: James Clutterbuck (2021)
Requires: pip install python-osc
"""
import time
from datetime import datetime
from queue import Queue
from tkinter.tix import WINDOW

import numpy as np
import scipy.interpolate as interp
import scipy.signal
import pyaudio
from pythonosc import dispatcher, osc_server

ip = "0.0.0.0"
port = 5000


queue = []
outputqueue = np.zeros(0)

start = time.time()


WINDOW_SIZE_SECONDS = 1
WINDOW_SIZE_SAMPLES = int(800//3.2*WINDOW_SIZE_SECONDS)
# WINDOW_SIZE_SAMPLES = 800
playing = False


def callback(indata, frames, time, status):
    try:
        global outputqueue
        data = outputqueue[:frames * 4]
        outputqueue = outputqueue[frames * 4:]
        print("callback")
        return data, pyaudio.paContinue 
    except:
        pass

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True, frames_per_buffer=WINDOW_SIZE_SAMPLES, stream_callback=callback)
stream.start_stream()

def eeg_handler(address: str,*args):
    global outputqueue, queue, playing, start
    dateTimeObj = datetime.now()
    printStr = dateTimeObj.strftime("%Y-%m-%d %H:%M:%S.%f")
    for arg in args:
        printStr += ","+str(arg)
    #print(printStr)
    queue.append(sum(args)/len(args))
    if len(queue) >= WINDOW_SIZE_SAMPLES and playing == False:
        playing = True
        print(time.time()-start)
        start = time.time()
        # print("queue filled at time", time.time() - start)
        print(min(queue[:WINDOW_SIZE_SAMPLES]), max(queue[:WINDOW_SIZE_SAMPLES]))
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
        t = (np.float32(queue[:WINDOW_SIZE_SAMPLES])/1000-0.7)*20
        queue = queue[WINDOW_SIZE_SAMPLES:]
        playing = False
        t = scipy.signal.resample(t, 44100//3)
        t = np.fft.rfft(t)
        t = np.roll(t, 2000//20)
        t[0:2000//20] = 0
        t = np.fft.irfft(t)
        t = scipy.signal.resample(t, 44100)
        # Ensure that the sound is in the range of -1 to +1
        t = (t/2+0.5)*2-1
        # Play the sound
        # stream.write(t)
        outputqueue = np.concatenate((outputqueue, t))

    
if __name__ == "__main__":
    print("hi")
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/eeg", eeg_handler)

    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print("Listening on UDP port "+str(port))
    server.serve_forever()
