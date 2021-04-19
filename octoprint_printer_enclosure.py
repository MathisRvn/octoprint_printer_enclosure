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

# PIN configuration

PIN_RED = 17
PIN_GREEN = 22
PIN_BLUE = 24

FAN_PIN_IN = 20
FAN_PIN_OUT = 21

DHT11_PIN = 4

# Setting up the connection with octoprint
API_KEY = "12B5A5D8BD9F4F8CB3C91DC3E6752D47" # Can be found on the web interface > Settings > API
BASE_URL = "http://192.168.0.18:80/"

# default colors definition
# From 0 to 100%
starting_color = (0, 100, 0)
working_color = (0, 0, 0)
end_color = (100, 100, 100)
open_color = (100, 100, 100)
error_color = (100, 0, 0)
system_error = (100, 0, 100)

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




def readDht11():
    (humidity, temperature) = Adafruit_DHT.read_retry(temperature_sensor, DHT11_PIN)
    return (temperature, humidity)

def setLeds(color):
    print("COLOR : ", color)
    red_led.ChangeDutyCycle(color[0])
    green_led.ChangeDutyCycle(color[1])
    blue_led.ChangeDutyCycle(color[2])

def setAirFan(speed):
    fan_in.ChangeDutyCycle(speed)
    fan_out.ChangeDutyCycle(100-speed)

def request(path): # To send a get request
    url = BASE_URL + 'api/' + path
    headers = {'X-Api-Key': API_KEY}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        return None

def stop_all_operations():
    setAirFan(100)
    setLeds(error_color)
    request("pause")
    print("ALL OPERATION STOPPED")

def door_open(): # return true or false
    pass

def get_status(): # get information from octoprint and return { operational, paused, printing, cancelling, pausing, error, ready }
    r = request('printer')
    if r != None:
        return r["state"]["flags"]
    else:
        return None
    

if __name__ == "__main__":

    # Starting sequence
    setAirFan(100)
    setLeds(starting_color)
    time.sleep(2)
    setAirFan(0)
    setLeds(working_color)

    ok = True
    while(ok):

        (temperature, humidity) = readDht11()
        
        print("TEMPERATURE : " + str(temperature))

        if temperature != 0:

            status = get_status()
            print(status)

            if status != None and status["operational"] == True:

                print(temperature, humidity, status)

                if temperature > max_temperature:
                    stop_all_operations()
                    ok = False

                if status["printing"] == True:

                    # Adapting Airfans
                    if temperature > optimal_temperature:
                        setAirFan(100)
                    else:
                        setAirFan(30)

                    # Adapting leds
                    if door_open():
                        setLeds(open_color)
                    else:
                        setLeds(working_color)

                elif status["cancelling"] == True or status["error"] == True:
                    setAirFan(100)
                    if door_open():
                        setLeds(open_color)
                    else:
                        setLeds(error_color)

                else:

                    setAirFan(0)

                    if door_open():
                        setLeds(open_color)
                    else:
                        setLeds(working_color)
            else:

                setLeds(error_color)
                print("Error : cannot cant connect to octoprint. Check if your printer is on.")

        else:

            setLeds(error_color)
            print("Error : cannot read dht11")

        time.sleep(1)
