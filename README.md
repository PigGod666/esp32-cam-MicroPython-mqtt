# 介绍
使用 esp32cam + MicroPython 实现的远程摄像头。摄像头使用mqtt向外发送数据、接受控制指令。并用web、python实现了摄像头画面的展示，使用web实现了摄像头的远程控制。  如果要支持新硬件，应该只需要修改`cam_esp32\mqtt_camera.py`文件中的`camera_init`函数即可。摄像头默认情况下不会向mqtt发送数据，只有当你查看时才会向mqtt发送数据，具体实现请看源码。  
支持的硬件有如下两款，

<img src="doc\esp32cam.png" alt="图片描述" width="50%">
<img src="doc\esp32cam-wrover.png" alt="图片描述" width="40%">

# 使用教程
## esp32发送图片
固件在[这里](https://github.com/lemariva/micropython-camera-driver/blob/master/firmware/micropython_v1.21.0_camera_no_ble.bin)
1. 将`cam_esp32`文件夹里的内容拷贝到esp32cam的根目录下；
2. 修改`mqtt_camera.py`文件里 mqtt 相关的参数;
3. 修改`WiFi.py`文件里WiFi的账号密码，重启esp32cam。

注意：只要把文件拷贝过去就可以了，不要带文件夹，3个文件都放在esp32cam的根目录下。如果你运行程序后发现多了个`camera_init.json`文件，不要担心，他是用来保存你设置的参数的。
## 接收图片
### 使用python脚本获取图片并显示
python脚本只支持简单的查看，不支持修改参数。
- 安装依赖包
```bash
pip install paho-mqtt
```
- 修改`receive.py`文件里 mqtt 相关的参数;
- 运行`receive.py`文件
### 使用web获取图片并显示
web方式除了可以查看图片，也支持修改摄像头参数，但请注意，这里mqtt连接的brokerUrl是默认端口为8083的WebSocket接口。
- 使用python搭建一个web服务，打开页面后配置好mqtt相关参数，即可开始访问摄像头。
```bash
cd ./show_web
python -m http.server
```
### mqtt broker
如果你没有可用的mqtt broker，可以尝试自己搭建一个。我这里用的是 ubuntu + docker 部署的mqtt。可以参考下面的命令搭建,-v 命令是把宿主机的配置文件挂载到docker容器里，覆盖原有的配置文件。
```bash
docker run -itd \
    --name nanomq \
    --restart=always \
    -v /config/path/nanomq.conf:/etc/nanomq.conf \
    -p 1883:1883 \
    -p 8083:8083 \
    -p 8883:8883  \
    emqx/nanomq:latest
```
配置文件可参考下面的，下面的配置，是我拷贝出来的默认配置。
```txt
# NanoMQ Configuration 0.18.0

# #============================================================
# # NanoMQ Broker
# #============================================================

mqtt {
    property_size = 32
    max_packet_size = 260MB
    max_mqueue_len = 2048
    retry_interval = 10s
    keepalive_multiplier = 1.25

    # Three of below, unsupported now
    max_inflight_window = 2048
    max_awaiting_rel = 10s
    await_rel_timeout = 10s
}

listeners.tcp {
    bind = "0.0.0.0:1883"
}

# listeners.ssl {
#       bind = "0.0.0.0:8883"
#       keyfile = "/etc/certs/key.pem"
#       certfile = "/etc/certs/cert.pem"
#       cacertfile = "/etc/certs/cacert.pem"
#       verify_peer = false
#       fail_if_no_peer_cert = false
# }

listeners.ws {
    bind = "0.0.0.0:8083/mqtt"
}

http_server {
    port = 8081
    limit_conn = 2
    username = admin
    password = public
    auth_type = basic
    jwt {
        public.keyfile = "/etc/certs/jwt/jwtRS256.key.pub"
    }
}

log {
    to = [file, console]
    level = warn
    dir = "/tmp"
    file = "nanomq.log"
    rotation {
        size = 10MB
        count = 5
    }
}

auth {
    allow_anonymous = false
    no_match = allow
    deny_action = ignore

    cache = {
        max_size = 32
        ttl = 1m
    }

    # password = {include "/etc/nanomq_pwd.conf"}
    # acl = {include "/etc/nanomq_acl.conf"}
password {
        admin = public
        client = public
    }
}
```