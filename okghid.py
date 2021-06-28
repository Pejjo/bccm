#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
"""
Handling raw data inputs example
"""
from time import sleep
from msvcrt import kbhit

import pywinusb.hid as hid

import ctypes

import datetime
import sys
import getopt
import paho.mqtt.client as mqtt

c_uint8 = ctypes.c_uint8

    
LCD_WIDTH=23

gBaro=0
gVhus=0
gUte=0 

def print_string(hid, dta):
  # Send string to display

    buffer = [0x00]*26
    buffer[1] = 1
    for i in range(0,14):
        buffer[2+i]=dta[i]
    
    print (buffer);
    hid.set_raw_data(buffer)
    hid.send()

  # Send string to display
def bootload(hid):

    buffer = [0x00]*26
    buffer[1]=0xFE
    buffer[2]=0xED
    buffer[3]=0xC0
    buffer[4]=0xDE

    hid.set_raw_data(buffer)
    hid.send()
    
def clearled(hid):
  # Send string to display

    buffer = [0x00]*26
    buffer[1]=0xCD
    buffer[2]=0x01

    hid.set_raw_data(buffer)
    hid.send()
    
def testled(hid):
  # Send string to display

    buffer = [0x00]*26
    buffer[1]=0xCD
    buffer[2]=0x02

    hid.set_raw_data(buffer)
    hid.send()

def format_dig(value, length, decimal):

    if length==4:
      if decimal==1:
        dec=0x02
        value=int(value*10)
      elif decimal==2:
        dec=0x04
        value=int(value*100)
      else:
        dec=0x00
        value=int(value)
      str = "{:04d}".format(value)[4::-1]
    else:
      if decimal==1:
        dec=0x02
        value=int(value*10)
      elif decimal==2:
        dec=0x04
        value=int(value*100)
      else:
        dec=0x00
        value=int(value)
      str = "{:03d}".format(value)[3::-1]
    
    digits=list(map(int, str))
    print (digits)
    pos=0
    while dec>0:
      if dec&0x01:
        digits[pos]|=0x80
      dec=dec>>1
      pos+=1
    return digits

def set_digits(hid, diga, digb, digc, digd):
    digits=[]
    digits.extend(format_dig(diga, 4,2))
    digits.extend(format_dig(digb, 4,0))
    digits.extend(format_dig(digc, 3,1))
    digits.extend(format_dig(digd, 3,1))
    print_string(hid, digits)

    
def sample_handler(data):
    print("Raw data: {0}".format(data))
#   print( "AVIR12: %i" % btn.BR1.AVIR_12)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe([("sensors/nodehub/ps/baro",0),("sensors/maren1/Land/Temperature",0),("sensors/maren1/Sensor0/Temperature",0)]) 

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global gBaro
    global gVhus
    global gUte 
    print(msg.topic+" "+str(msg.payload))
    if msg.topic == "sensors/nodehub/ps/baro":
       gBaro=float(msg.payload)
    if msg.topic == "sensors/maren1/Land/Temperature":
       gVhus=float(msg.payload)
    if msg.topic == "sensors/maren1/Sensor0/Temperature":
       gUte=float(msg.payload)


def raw_test(argv, client):
    global gBaro
    global gVhus
    global gUte
    cmd=0
    dta=0
    try:
        opts, args = getopt.getopt(argv,"hbtc",["reset","boot"])
    except getopt.GetoptError:
        print ('test.py -c -b [--boot] -r [--reset]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-b", "--boot"):
            cmd = 1
            
        elif opt in ("-t", "--test"):
            cmd = 2
        elif opt in ("-c"):
            cmd = 3
            dta = arg

    run=True
    dtime=0
    retry=30
    # simple test
    # browse devices...
    try:
        while (run and retry>0):
            hid.HidDeviceFilter(vendor_id = 0x03EB)
            all_hids = hid.HidDeviceFilter(vendor_id=0x03EB, product_id = 0x204F).get_devices()
            
            print(all_hids)
            if all_hids:
                device = all_hids[0]
            try:
                device.open()


                #set custom raw data handler
                device.set_raw_data_handler(sample_handler)
            
                report = device.find_output_reports()

                print(report)
                print(report[0])

                if cmd==1:
                    bootload(report[0])
                elif cmd==2:
                    testled(report[0])
                elif cmd==3:
                    clearled(report[0])

                sleep(1)
                x=0
        # Go!       
                print("\nWaiting for data...\nPress any (system keyboard) key to stop...")
                while device.is_plugged():
                    client.loop()
                    ltime=datetime.datetime.now().timetuple()
                    ctime=ltime.tm_hour+(ltime.tm_min/100.0)
                    print(ctime)
                    #just keep the device opened to receive events
                    
                    sleep(0.01)
                    if dtime!=ltime.tm_sec:
                        dtime=ltime.tm_sec
                        set_digits(report[0], ctime, gBaro, gUte, gVhus)
                        sleep(0.5)
        # TOPICS
        ###         print_string(report[0],str(datetime.datetime.now().time()),0)
                    sleep(0.01)
                    if kbhit():
                        run=False
        #           print_string(report[0],"GB.UK",2)
        #           sleep(0.01)

            except Exception as e:
                print("USB Disconnect")
                try:
                    device.close()
                except Exception as e:
                    print("HID Close", e)
                    pass
                sleep(1)
                retry-=1
                pass

    except Exception as e:
        print("Not connected", e)
        sleep(1)
        retry-=1
        pass
        
    finally:
        try:
            device.close()
        except:
            pass
#    else:
#        print("There's not any non system HID class device available")
#
if __name__ == '__main__':
    # first be kind with local encodings
    import sys
    if sys.version_info >= (3,):
        # as is, don't handle unicodes
        unicode = str
        raw_input = input
    else:
        # allow to show encoded strings
        import codecs
        sys.stdout = codecs.getwriter('mbcs')(sys.stdout)
    # The callback for when the client receives a CONNACK response from the server.

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("extra.hoj.nu", 1883, 60)

    raw_test(sys.argv[1:],client)

