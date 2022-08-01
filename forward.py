from socket import *

sin = socket(AF_INET, SOCK_DGRAM)
sout1 = socket(AF_INET, SOCK_DGRAM)
sout2 = socket(AF_INET, SOCK_DGRAM)

sin.bind(('0.0.0.0', 5000))

while True:
    data = sin.recv(1024)
    if not data:
        break
    sout1.sendto(data, ("127.0.0.1", 5001))
    sout2.sendto(data, ("127.0.0.1", 5002))
sin.close()
sout1.close()
sout2.close()
