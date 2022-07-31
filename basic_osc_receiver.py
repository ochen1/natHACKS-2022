"""
Mind Monitor - EEG OSC Receiver
Requires: pip install python-osc
"""
from datetime import datetime
from pythonosc import dispatcher
from pythonosc import osc_server

ip = "0.0.0.0"
port = 5000
path = f"muse_{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}.csv"
recording = False
f = open(path, 'w+')
f.write('TimeStamp,RAW_TP9,RAW_AF7,RAW_AF8,RAW_TP10,AUX,Marker\n')
# Muse S with 2 AUX Channels:
# f.write('TimeStamp,RAW_TP9,RAW_AF7,RAW_AF8,RAW_TP10,AUX_R,AUX_L,Marker\n')


def eeg_handler(address, *args):
    if recording:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + ",")
        f.write(",".join(args))
        f.write("\n")

    
def marker_handler(address, i):
    global recording
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    f.write(f"{now},,,,,,/Marker/{address[-1]}\n")
    # Muse S with 2 AUX Channels:
    f.write(f"{now},,,,,,,/Marker/{address[-1]}\n")
    if address[-1] == "1":
        recording = True
        print("Recording started.")
    if address[-1] == "2":
        f.close()
        server.shutdown()
        print("Recording stopped.")


if __name__ == "__main__":
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/muse/eeg", eeg_handler)
    dispatcher.map("/Marker/*", marker_handler)

    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print(f"Listening on UDP port {str(port)}")
    print("Send Marker 1 to Start recording and Marker 2 to Stop Recording.")
    server.serve_forever()

