#!/usr/bin/env python3

import json
import subprocess
import time
import random
import re
from influxdb import InfluxDBClient
import serial
ser = serial.Serial('/dev/ttyACM0', 115200)

payload_mac = "00:16:3e:2f:ba:b7"
##############################################################################################################
client_wb = InfluxDBClient(host="ec2-3-141-152-206.us-east-2.compute.amazonaws.com", port=8086, database="waveboost")
dataFormat = 3#payload["data_format"] if ('data_format' in payload) else None
fields = {}
#payload["pressure"] if ('pressure' in payload) else None
fields["accelerationX"]             = 4#payload["acceleration_x"]/1000.0 if ('acceleration_x' in payload) else None
fields["accelerationY"]             = 5#payload["acceleration_y"]/1000.0 if ('acceleration_y' in payload) else None
fields["accelerationZ"]             = 6#payload["acceleration_z"]/1000.0 if ('acceleration_z' in payload) else None
fields["batteryVoltage"]            = 7#payload["battery"]/1000.0 if ('battery' in payload) else None
fields["v_cap"]             = 8#payload["v_cap"]/1000.0 if ('v_cap' in payload) else None
fields["p_rssi"]            = 9#payload["p_rssi"]/1000.0 if ('p_rssi' in payload) else None
fields["txPower"]                   = 10#payload["tx_power"] if ('tx_power' in payload) else None
fields["movementCounter"]           = 11#payload["movement_counter"] if ('movement_counter' in payload) else None
fields["measurementSequenceNumber"] = 12#payload["measurement_sequence_number"] if ('measurement_sequence_number' in payload) else None
fields["light"]                     = 13#payload["tagID"] if ('tagID' in payload) else None
fields["rssi"]                      = 14#payload["rssi"] if ('rssi' in payload) else None

##############################################################################################################	
def get_temperature(data):
	'''Return temperature in celsius'''
	temp = (data[2] & ~(1 << 7)) + (data[3] / 100)
	sign = (data[2] >> 7) & 1
	if sign == 0:
		return round(temp, 2)
	return round(-1 * temp, 2)

def get_humidity(data):
	'''Return humidity %'''
	return data[1] * 0.5

def get_pressure(data):
	'''Return air pressure hPa'''
	pres = (data[4] << 8) + data[5] + 50000
	return pres / 100

def get_light(data):
	return (data[12] << 8) + data[13]
	
def get_Rec1adc(data):
	return ((data[6] << 8) + data[7])
	
def get_Rec2adc(data):
	return ((data[8] << 8) + data[9])
	
def get_PMadc(data):
	return ((data[10] << 8) + data[11])
	
def get_SuperCap(data):
	return ((data[14] << 8) + data[15])	
	
while True:
	#data = ser.readline().decode("utf-8")
	data = ser.readline().decode()
	if data:
		payload_start = data.index("ff990403") + 6
		print(data)
		#print(data[payload_start:])
		payload_end = data[payload_start:].index("-")
		byte_data = bytearray.fromhex(data[payload_start:(payload_start+payload_end)])
		#print(data[payload_start:(payload_end+payload_start)])
		payload_mac = data[(payload_start+payload_end+1):]
		#payload_mac = "00:16:3e:2f:ba:11"
		mac = payload_mac[1:3]+":"+payload_mac[3:5]+":"+payload_mac[5:7]+":"+payload_mac[7:9]+":"+payload_mac[9:11]+":"+payload_mac[11:]
		mac = mac.strip()
		print(mac)
		#payload_mac = payload_mac.strip('\n')
		
		fields["temperature"] 		= int(get_temperature(byte_data))
		fields["humidity"]              = int(get_humidity(byte_data))
		fields["pressure"]              = int(get_pressure(byte_data))
		fields["light"]			= int(get_light(byte_data)/10)
		fields["Rec1"]			= (get_Rec1adc(byte_data))
		fields["Rec2"]			= (get_Rec2adc(byte_data))
		fields["PM"]			= (get_PMadc(byte_data))
		fields["SuperCap"]              = (get_SuperCap(byte_data))
		fields["CPU_temp"]		= int(subprocess.getoutput("cat /sys/class/thermal/thermal_zone0/temp"))
		json_body = [{
		"measurement": "wb_measurements",
		"tags": {
        "mac": mac,
        "dataFormat": dataFormat
		},
		"fields": fields
		}
		]
		#print(get_light(byte_data))
		try:
			client_wb.write_points(json_body)
			print("sent to server")
		except Exception as e:
			print("error send to server")
			pass
	
	
		
