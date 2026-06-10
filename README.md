# Tello_drone

This project was created using the Tello Drone in conjunction with one's own computer. The setup is a little bit more complicated than what is necessary as this project uses Ubuntu rather than the prefered/recommened Windows. The reason why occurred is because Robomaster wasn't avaiable at the time nor did the WIndow operating system have Anaconda (necessary to use in the most simple way possible). 

So in simple terms the path is as follows:

Drone
  |
  |
  V
Windows OS
  |
  |
  V
WSL2: Ubuntu 22.04

Now to run run the final code (which most are probualy most interested about), we must have our Windows powershell and VS open. In the terminal of the powershell the following cmd must be ran: ffmpeg -loglevel warning -i "udp://0.0.0.0:11111" -c copy -f mpegts udp://127.0.0.1:12345

As for the Visual Studio terminal: run follower_.py
