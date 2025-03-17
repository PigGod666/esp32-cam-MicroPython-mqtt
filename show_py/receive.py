import paho.mqtt.client as mqtt
import time
import cv2
import numpy as np
import json


# MQTT配置
MQTT_BROKER_URL = 'www.xxx.com'
MQTT_BROKER_PORT = 1883
USERNAME = 'client'
PASSWORD = 'public'
TOPIC_DATA = "esp32/camera/data"
TOPIC_CMD = "esp32/camera/cmd"

# 初始化MQTT客户端
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)

frame_count = 0
start_time = time.time()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(TOPIC_DATA)

def on_message(client, userdata, msg):
    global frame_count, start_time
    nparr = np.frombuffer(msg.payload, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is not None:
        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time > 1.0:
            fps = frame_count / elapsed_time
            print(f"FPS: {fps:.2f}\t {image.shape}")
            frame_count = 0
            start_time = time.time()
        cv2.imshow('Received Image', image)
        cv2.waitKey(1)
    else:
        print("Failed to decode image.")


client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, 60)
client.loop_start()

if __name__ == '__main__':
    while True:
        # msg = input("Enter message: ")
        # result = client.publish(TOPIC_DATA, msg)
        # print("Send '{msg}' to topic_DATA '{topic_DATA}'".format(msg = msg, topic_DATA = TOPIC_DATA))
        # client.wait_msg()
        client.publish(TOPIC_CMD, json.dumps({"framenumber": 50}))
        time.sleep(3)
