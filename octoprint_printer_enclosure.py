'''
Author : Mathis Revenu
Date : 04.2021
'''

# importing dependencies
import requests # pip install requests
import Adafruit_DHT
import time
import signal
import sys
import os
import RPi.GPIO as GPIO
import datetime
import traceback

from pathlib import Path
dir_path = str(Path(__file__).parent.resolve())


# PIN configuration

PIN_RED = 17
PIN_GREEN = 22
PIN_BLUE = 24

FAN_PIN_IN = 20
FAN_PIN_OUT = 21

DOOR_PIN = 19

AIR_FAN_MAX = 100
AIR_FAN_MIN = 0

DHT11_PIN = 4

# Setting up the connection with octoprint
API_KEY = "12B5A5D8BD9F4F8CB3C91DC3E6752D47" # Can be found on the web interface > Settings > API
BASE_URL = "http://192.168.0.18:80/"

# default colors definition
# From 0 to 100%
starting_color = (0, 100, 0)
working_color = (0, 0, 0)
open_color = (100, 100, 100)
error_color = (100, 0, 0)

# Temperature configuration
min_temperature = 30
optimal_temperature = 40
max_temperature = 50

temperature_sensor = Adafruit_DHT.DHT11 # Setting up dht11 sensor

# Setting up all pwm output : 2 for the fans and 3 for the 3 colors of the leds

PWM_FREQ = 200

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(FAN_PIN_IN, GPIO.OUT, initial=GPIO.LOW)
fan_in = GPIO.PWM(FAN_PIN_IN,PWM_FREQ)
fan_in.start(0)

GPIO.setup(FAN_PIN_OUT, GPIO.OUT, initial=GPIO.LOW)
fan_out = GPIO.PWM(FAN_PIN_OUT,PWM_FREQ)
fan_out.start(0)

GPIO.setup(PIN_RED, GPIO.OUT, initial=GPIO.LOW)
red_led = GPIO.PWM(PIN_RED,PWM_FREQ)
red_led.start(0)

GPIO.setup(PIN_GREEN, GPIO.OUT, initial=GPIO.LOW)
green_led = GPIO.PWM(PIN_GREEN,PWM_FREQ)
green_led.start(0)

GPIO.setup(PIN_BLUE, GPIO.OUT, initial=GPIO.LOW)
blue_led = GPIO.PWM(PIN_BLUE,PWM_FREQ)
blue_led.start(0)

# setting up the endstop of the door
GPIO.setmode(GPIO.BCM)
GPIO.setup(DOOR_PIN,GPIO.IN)


def readDht11():
    try:
        (humidity, temperature) = Adafruit_DHT.read_retry(temperature_sensor, DHT11_PIN)
        if temperature >= 0:
            return (temperature, humidity)
        else:
            raise Exception
    except Exception:
        return (0, 0)


def setLeds(color):
    red_led.ChangeDutyCycle(color[0])
    green_led.ChangeDutyCycle(color[1])
    blue_led.ChangeDutyCycle(color[2])


def setAirFan(speed):
    fan_in.ChangeDutyCycle(speed)
    fan_out.ChangeDutyCycle(speed)


def request(path, json = {}, method='get'): # To send a get request

    url = BASE_URL + 'api/' + path
    headers = {'X-Api-Key': API_KEY}
    resp = None

    if method == 'get':
        resp = requests.get(url, headers=headers, json=json)
    elif method == 'post':
        resp = requests.post(url, headers=headers, json=json)

    if resp.status_code == 200:
        return resp.json()
    else:
        return None


def door_open(): # return true or false
    if GPIO.input(DOOR_PIN):
        return False
    else:
        return True


def get_status(): # get information from octoprint and return { operational, paused, printing, cancelling, pausing, error, ready }
    r = request('printer')
    if r != None:
        return r["state"]["flags"]
    else:
        return None


def setAirfanUsingTemperature (temperature):
    if temperature > optimal_temperature:
        setAirFan(AIR_FAN_MAX)
    else:
        setAirFan(AIR_FAN_MIN)

def error (err):
    (temperature, humidity) = readDht11()
    txt = str(datetime.datetime.now()) + '     ' + str(temperature) + '°C      Door opened ? ' + door_open() + '     error : ' + err
    print(txt)
    f = open(dir_path + '/log.txt', 'a')
    f.write(txt+"\n")
    f.close()

def main ():

    # Starting sequence
    setAirFan(100)
    setLeds(starting_color)
    time.sleep(3)

    while(True):

        try:

            (temperature, humidity) = readDht11()
            status = get_status()
            door_status = door_open()

            print("temperature : " + temperature + '°C    door : ' + door_status)

            if temperature == 0:
                error("Error : cannot connect to DHT11")
                setLeds(error_color)

            elif status == None or status["operational"] != True:
                error("Error : cannot connect to Octoprint")
                setLeds(error_color)

            elif temperature > max_temperature:
                error("Error: max temperature reached")
                setLeds(error_color)
                setAirFan(AIR_FAN_MAX)
                request("job", json = {"command": "pause", "action": "pause"}, method='post')

            else:

                if door_status:
                    setAirfanUsingTemperature (temperature)
                    setLeds(open_color)

                elif status['ready'] == True:
                    setAirFan(AIR_FAN_MAX)
                    setLeds(starting_color)

                elif status["cancelling"] == True or status["error"] == True:
                    error("Problem with the printer : status = cancelling ou status == error")
                    setAirFan(AIR_FAN_MAX)
                    setLeds(error_color)

                else:
                    setAirfanUsingTemperature (temperature)
                    setLeds(working_color)

            time.sleep(0.5)

        except Exception:
            traceback.print_exc()


def run ():
    try:
        main()
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    while 1:
        run()
