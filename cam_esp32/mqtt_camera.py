import json
import random
import time
import wifi
import camera
import machine
import os

from umqtt.simple import MQTTClient

# 需要修改的参数
SERVER = "www.xxx.com"
PORT = 1883
CLIENT_ID = 'micropython-client-{id}'.format(id = random.getrandbits(8))
USERNAME = 'client'
PASSWORD = 'public'
TOPIC_DATA = "esp32/camera/data"
TOPIC_CMD = "esp32/camera/cmd"

# 不需要修改的全局变量
framenumber = 0
camera_init_data = dict()
camera_init_json_path = "camera_init.json"
# 这个是一个字典，用来定义摄像头参数，包括key和value值的范围。
camera_params = {
    "flip": [0, 1],
    "mirror": [0, 1],
    "framesize": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21],
    "speffect": [0,1,2,3,4,5,6],
    "whitebalance": [0,1,2,3,4],
    "saturation": [-2.0,2.0],
    "brightness": [-2.0,2.0],
    "contrast": [-2.0,2.0],
    "quality": [10,63]
    }


def read_json(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        data = {}
    return data


def set_camera_data(param, val, camera_init_data=dict()):
    if not camera_init_data:
        camera_init_data = read_json(camera_init_json_path)
    camera_init_data.update({param: val})
    return camera_init_data


def camera_init():
    """ 初始化相机，兼容“ https://blog.csdn.net/weixin_45537132/article/details/141495676 ”这里提到的两款开发板。 """
    global camera_init_data
    try:
        camera.init(0, format=camera.JPEG, framesize=camera.FRAME_SXGA, xclk_freq=camera.XCLK_20MHz,
                fb_location=camera.PSRAM)
    except Exception as e:
        # 初始化摄像头		ESP32-WROVER-DEV
        camera.init(0, d0=4, d1=5, d2=18, d3=19, d4=36, d5=39, d6=34, d7=35,
                format=camera.JPEG, framesize=camera.FRAME_SXGA, xclk_freq=camera.XCLK_20MHz,
                href=23, vsync=25, reset=-1, sioc=27, siod=26, xclk=21, pclk=22, fb_location=camera.PSRAM)
    # 根据本地文件设置相机参数。
    camera_init_data = read_json(camera_init_json_path)
    for key, val in camera_init_data.items():
        eval(f"camera.{key}({val})")
    camera_init_data = dict()
    return camera


def on_message(topic, msg):
    """ 处理接收到的消息，可用于改变相机参数、控制是否继续发布图片、重启设备。 """
    global framenumber, camera_init_data
    framenumber = 1 if (framenumber <= 0) else framenumber
    camera_init_data = dict()
    try:
        payload = json.loads(msg.decode())
        if "framenumber" in payload:
            framenumber = max(1, min(payload.get("framenumber", 1), 300))
        # 解析收到的参数，验证参数是否合法
        for key, val in payload.items():
            if key in camera_params:
                if key in ["saturation", "brightness", "contrast"]:
                    if (camera_params[key][0] <= val <= camera_params[key][1]):
                        camera_init_data = set_camera_data(key, val, camera_init_data)
                elif key in ["quality"]:
                    if (camera_params[key][0] <= int(val) <= camera_params[key][1]):
                        val = int(val)
                        camera_init_data = set_camera_data(key, val, camera_init_data)
                else:
                    if val in camera_params[key]:
                        camera_init_data = set_camera_data(key, val, camera_init_data)
        if camera_init_data:
            # 如果有有效的设置，将设置写入文件，设备重启时可读取配置。
            with open(camera_init_json_path, "w") as f:
                json.dump(camera_init_data, f)
        if "reboot" in payload:
            machine.reset()
    except Exception as e:
        print("error: ", e, msg.decode())
        framenumber = 1
        pass


def connect():
    client = MQTTClient(CLIENT_ID, SERVER, PORT, USERNAME, PASSWORD)
    client.connect()
    print('Connected to MQTT Broker "{server}"'.format(server = SERVER))
    return client


def subscribe(client):
    client.set_callback(on_message)
    client.subscribe(TOPIC_CMD)
    print(f"订阅主题：{TOPIC_CMD}")


def loop_publish(client, camera):
    global framenumber, camera_init_data
    print("start")
    t_init = time.time()
    while True:
        print(framenumber)
        t_start = time.time()
        # 每隔一段时间ping一下，不然服务端会认为已经离线，报错。
        # 如果没把ping写在这个if里面，ping的太快，网络会卡死的。
        if (t_start - t_init) >= 2:
            t_init = time.time()
            client.ping()
        # 检查一下是否有收到数据。
        client.check_msg()
        # framenumber 是防止相机在没有人查看的情况下也工作。
        if framenumber <= 0:
            time.sleep(1)
            continue
        if camera_init_data:
            # 将相机参数设置到摄像头中。
            for key, val in camera_init_data.items():
                eval(f"camera.{key}({val})")
            # 清空参数
            camera_init_data = dict()
        # 从摄像头获取一帧图片。
        buf = camera.capture()
        # with open("第一张图片.png", "wb") as f:
        #     f.write(buf)  # buf中的数据就是图片的数据，所以直接写入到文件就行了
        # 将图片发送出去。
        result = client.publish(TOPIC_DATA, buf)
        framenumber -= 1


def mqtt_camera():
    # 初始化摄像头
    camera = camera_init()
    wifi.connect()
    client = connect()
    subscribe(client)
    loop_publish(client, camera)


if __name__ == "__main__":
    try:
        mqtt_camera()
    except Exception as e:
        print(e)
        machine.reset()
