# octoprint_printer_enclosure
External python script for octoprint running on raspberrypi which can manage an enclosure (leds, fans and DHT_11)

The script run on Python3 on a raspberrypi with ocotprint installed on it

# Installation :
run following commands :

`cd ~`

`git clone https://github.com/MathisRvn/octoprint_printer_enclosure.git`

`cd octoprint_printer_enclosure`

Make sure you have the needed python modules installed (requests, Adafruit_DHT)
If not install them using
`pip install requests` and `pip install Adafruit_DHT`

`python3 octoprint_printer_enclosure.py`

### You also have to auto start the program when your ocotprint start. Maybe using /etc/rc.local
