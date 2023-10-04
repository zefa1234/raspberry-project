#!/usr/bin/python 
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#|R|a|s|p|b|e|r|r|y|P|i|.|c|o|m|.|t|w|
#+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# Copyright (c) 2016, raspberrypi.com.tw
# All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# move_car.py
# control car with argument [w=forward/a=left/s=backward/d=right]
# usage: sudo python move_car.py [w/a/s/d]
#
# Author : sosorry
# Date   : 08/01/2015

import RPi.GPIO as GPIO
import time
import readchar
import speech_recognition as sr
import bluetooth
import os
from gtts import gTTS
import threading
import requests
import random
import smbus
import struct
import base64
from camera_pi import Camera
bus = smbus.SMBus(1)
deviceID = bus.read_byte_data(0x53, 0x00)
print("Please connect Bluetooth rpi4-A20")

bus.write_byte_data(0x53, 0x2D, 0x00)
bus.write_byte_data(0x53, 0x2D, 0x08)
bus.write_byte_data(0x53, 0x31, 0x08)
time.sleep(0.5)
ENDPOINT = "things.ubidots.com"
DEVICE_LABEL = "yum"
VARIABLE_LABEL = "xx"
TOKEN = "BBFF-1VCFuGCXRBtjhNu1jvgw6uUJQDF1zJ"
DELAY = 0.1 # Delay in seconds

ENDPOINT2 = "industrial.api.ubidots.com"
DEVICE_LABEL2 = "yum"
VARIABLE_LABEL2 = "image"
TOKEN2 = "BBFF-PmzV4RJX7h2Av1KMZMOABAFeiu6oL1"

def post_var2(payload2, url=ENDPOINT2, device=DEVICE_LABEL2, token=TOKEN2):
    try:
        url = "http://{}/api/v1.6/devices/{}".format(url, device)
        headers = {"X-Auth-Token": token, "Content-Type": "application/json"}
        attempts = 0
        status_code = 400
        while status_code >= 400 and attempts < 5:
            req = requests.post(url=url, headers=headers,
                                json=payload2)
            status_code = req.status_code
            attempts += 1
            time.sleep(1)
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))

def capture(camera):
    img = camera.get_frame_b64()
    payload2 = {VARIABLE_LABEL2: {"value" : 1, "context" : {"img" : img}}}
# print(payload)
# Sends data
    post_var2(payload2)

def post_var(payload, url=ENDPOINT, device=DEVICE_LABEL, token=TOKEN):
	try:
		url = "http://{}/api/v1.6/devices/{}".format(url, device)
		headers = {"X-Auth-Token": token, "Content-Type": "application/json"}
		attempts = 0
		status_code = 400
		while status_code >= 400 and attempts < 5:
			req = requests.post(url=url, headers=headers,
					json=payload)
			status_code = req.status_code
			attempts += 1
			time.sleep(1)
	except Exception as e:
		print("[ERROR] Error posting, details: {}".format(e))
accel = {'x' : 0, 'y' : 0, 'z': 0}

server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
port = 1
server_socket.bind(("",port))
server_socket.listen(1)
client_socket,address = server_socket.accept()
print("Accepted connection from ",address)
#obtain audio from the microphone
r=sr.Recognizer()

BTN_PIN = 7
LED_PIN = 10
LED_PIN1 = 8
LED_PIN2 = 36
Motor_R1_Pin = 16
Motor_R2_Pin = 18
Motor_L1_Pin = 15
Motor_L2_Pin = 13
t = 0.5
WAIT_TIME = 0.2
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(LED_PIN1, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED_PIN2, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(Motor_R1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_R2_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L1_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor_L2_Pin, GPIO.OUT, initial=GPIO.LOW)

mic_mode = False
user = True
keep = False

print("Please wait. Calibrating microphone...")
with sr.Microphone(device_index = 2, sample_rate = 48000) as source:
        #listen for 1 seconds and create the ambient noise energy level
        r.adjust_for_ambient_noise(source, duration=5)


def stop():
    GPIO.output(Motor_R1_Pin, False)
    GPIO.output(Motor_R2_Pin, False)
    GPIO.output(Motor_L1_Pin, False)
    GPIO.output(Motor_L2_Pin, False)


def forward():
    GPIO.output(Motor_R1_Pin, True)
    GPIO.output(Motor_R2_Pin, False)
    GPIO.output(Motor_L1_Pin, True)
    GPIO.output(Motor_L2_Pin, False)
    time.sleep(t)
    stop()


def backward():
    GPIO.output(Motor_R1_Pin, False)
    GPIO.output(Motor_R2_Pin, True)
    GPIO.output(Motor_L1_Pin, False)
    GPIO.output(Motor_L2_Pin, True)
    time.sleep(t)
    stop()


def turnRight():
    GPIO.output(Motor_R1_Pin, False)
    GPIO.output(Motor_R2_Pin, False)
    GPIO.output(Motor_L1_Pin, True)
    GPIO.output(Motor_L2_Pin, False)
    time.sleep(t)
    stop()

def turnLeft():
    GPIO.output(Motor_R1_Pin, True)
    GPIO.output(Motor_R2_Pin, False)
    GPIO.output(Motor_L1_Pin, False)
    GPIO.output(Motor_L2_Pin, False)
    time.sleep(t)
    stop()

def job():
    previousStatus = None
    previousTime = time.time()
    currentTime = None
    while user == True:
        input = GPIO.input(BTN_PIN)
        currentTime = time.time()

        if input == GPIO.LOW and previousStatus == GPIO.HIGH and (currentTime - previousTime) > WAIT_TIME:
            previousTime = currentTime
            print("Button pressed @", time.ctime())
            GPIO.output(LED_PIN, GPIO.HIGH)
            #time.sleep(5)
            judge = True
            with sr.Microphone(device_index = 2, sample_rate = 48000) as source:
                #with sr.Microphone() as source:
                print("Say something!")
                #r.energy_threshold += 280
                audio=r.record(source,duration=5)
                #audio = r.record(source, duration=4)
            # recognize speech using Google Speech Recognition
            try:
                print("Google Speech Recognition thinks you said:")
                ch = r.recognize_google(audio, language='zh-TW')
                print(ch)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print("No response from Google Speech Recognition service: {0}".format(e))

            #os.system('arecord -d 5 -D plughw:2,0 -f cd hello.mp3 > /dev/null 2>&1')
        GPIO.output(LED_PIN, GPIO.LOW)
        previousStatus = input


def mic():

    while user ==  True:
        speak = input('想說些什麼:')
        if user == False:
            break
        if mic_mode == True:
            GPIO.output(LED_PIN1, GPIO.LOW)
            GPIO.output(LED_PIN2, GPIO.HIGH)
            time.sleep(1)
            tts = gTTS(text=speak, lang='zh-TW')
            tts.save('hello_tw.mp3')
            os.system('omxplayer -o local -p hello_tw.mp3 > /dev/null 2>&1')
            GPIO.output(LED_PIN1, GPIO.HIGH)
            GPIO.output(LED_PIN2, GPIO.LOW)
        else:
            print("speaker is not on!")
def main():
# Simulates sensor values
    sensor_value = accel['y']
# Builds Payload and topíc
    payload = {VARIABLE_LABEL: sensor_value}
# Sends data
    post_var(payload) 
def xyz():
    while user == True:
        data0 = bus.read_byte_data(0x53, 0x32)
        data1 = bus.read_byte_data(0x53, 0x33)
# Convert the data to 10-bits
        xAccl = struct.unpack('<h', bytes([data0, data1]))[0]
        accel['x'] = xAccl / 256

        data0 = bus.read_byte_data(0x53, 0x34)
        data1 = bus.read_byte_data(0x53, 0x35)

        yAccl = struct.unpack('<h', bytes([data0, data1]))[0]
        accel['y'] = yAccl / 256

        data0 = bus.read_byte_data(0x53, 0x36)
        data1 = bus.read_byte_data(0x53, 0x37)
# Convert the data to 10-bits
        zAccl = struct.unpack('<h', bytes([data0, data1]))[0]
        accel['z'] = zAccl / 256
# Output data to screen
#print ("Ax Ay Az: %.3f %.3f %.3f" % (accel['x'], accel['y'], accel['z']))
        time.sleep(0.1)
        main()
        time.sleep(DELAY)
'''
global variables
'''
ENDPOINT = "things.ubidots.com"
DEVICE_LABEL = "yum"
VARIABLE_LABEL = "xx"
TOKEN = "BBFF-1VCFuGCXRBtjhNu1jvgw6uUJQDF1zJ"
DELAY = 0.1 # Delay in seconds
def post_var(payload, url=ENDPOINT, device=DEVICE_LABEL, token=TOKEN):
	try:
		url = "http://{}/api/v1.6/devices/{}".format(url, device)
		headers = {"X-Auth-Token": token, "Content-Type": "application/json"}
		attempts = 0
		status_code = 400
		while status_code >= 400 and attempts < 5:
			req = requests.post(url=url, headers=headers,
					json=payload)
			status_code = req.status_code
			attempts += 1
			time.sleep(1)
	except Exception as e:
		print("[ERROR] Error posting, details: {}".format(e))
accel = {'x' : 0, 'y' : 0, 'z': 0}

def cam():
    capture(camera)
    print("Done")
    


if __name__ == "__main__":
    camera = Camera()
    print("Press start to quit...")
    m = threading.Thread(target = mic)
    j = threading.Thread(target = job)
    k = threading.Thread(target = xyz)


    j.start()
    m.start()
    k.start()

    while True:
        #ch = readchar.readkey()
        res = client_socket.recv(1024)
        client_socket.send(res)
        ch = res.decode('utf-8')

        if ch == 'm':
            if mic_mode == True:
                mic_mode = False
                print("speaker off")
            else:
                mic_mode = True
                print("speaker on")

        elif ch == 'w':
            print("forward")
            forward()

        elif ch == 's':
            print("backward")
            backward()

        elif ch == 'd':
            print("right")
            turnRight()

        elif ch == 'a':
            print("left")
            turnLeft()

        elif ch == 'c':
            c = threading.Thread(target = cam)
            print("Smile")
            c.start()
        elif ch == 'r':
            print("special mode")
            keep = True
            print("special mode off")

        if res.decode('utf-8') == 'q':
            user = False
            print ("Quit")
            j.join()
            k.join()
            print("please type anything in speaker to end process")
            m.join()
            GPIO.cleanup()
            client_socket.close()
            server_socket.close()
            quit()
            break

    time.sleep(2)

    quit()
