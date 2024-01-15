if __name__ == '__main__':
    def lora_test():
        from lora import Lora
        lora = Lora('/dev/ttyUSB0', 9600, 2.0, False)
        channel = int(input('Enter channel:'))
        print('==========================================')
        while(True):
            payload = input('input id,code: ').split(',')
            if payload == 'exit': return
            print(lora.send(payload[0], payload[1], channel))
            print()
    
    def mqtt_test():
        import paho.mqtt.client as mqtt
        import json

        new_conf = {
            "joysticks":{
                "BFF19B62":{
                    "ids":["3004"],
                    "priority":30,
                    "timeout":180,
                    "enable": {
                        "forward": True,
                        "left": True,
                        "right": True,
                        "floating": True,
                        "diving": True,
                        "middle": True,
                        "switch mode": True,
                        "led": True,
                        "auto": False,
                        "leave auto": False
                    }
                },
                "9D099982":{
                    "ids":["3006"],
                    "priority":30,
                    "timeout":180,
                    "enable": {
                        "forward": True,
                        "left": True,
                        "right": True,
                        "floating": True,
                        "diving": True,
                        "middle": True,
                        "switch mode": True,
                        "led": True,
                        "auto": False,
                        "leave auto": False
                    }
                },
                "08149935": {
                    "ids": [
                        "3049"
                    ],
                    "priority": 30,
                    "timeout": 180,
                    "enable": {
                        "forward": True,
                        "left": True,
                        "right": True,
                        "floating": True,
                        "diving": True,
                        "middle": True,
                        "switch mode": True,
                        "led": False,
                        "auto": True,
                        "leave auto": True 
                    }
                }
            }
        }   
        client = mqtt.Client()
        client.username_pw_set('lab314', 'lab314fish')
        client.connect('20.89.131.34', 1884)
        #client.publish('Monitor/config/999001001/set', json.dumps(new_conf))
        client.publish('Monitor/status/999001001/get', 'nothing')

    test = int(input('choose test: 1->lora, 2->mqtt: '))
    if test == 1:
        lora_test()
    elif test == 2:
        try: mqtt_test()
        except Exception as e: print(e)