# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import machine
from mqtt_camera import mqtt_camera

if __name__ == "__main__":
    try:
        mqtt_camera()
    except Exception as e:
        print(e)
        machine.reset()