import network
import time

def connect():
	# WiFi 账号
	ssid = 'xxx'
	# Wifi 密码
	password = 'xxx'
	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	wlan.connect(ssid, password)
	while wlan.isconnected() == False:
		print('Waiting for connection...')
		time.sleep(1)
	print('Connected on {ip}'.format(ip = wlan.ifconfig()[0]))
