import paho.mqtt.client as mqtt
import json

class MQTT_Client():
    def __init__(self, location, logger, check_status, check_config, change_config, lora, log=True):
        self.client = None
        self._location = location
        #self._post_url = post_url
        #self._vid_storage_limit = vid_storage_limit
        self.logger = logger
        self.check_monitor_status = check_status
        self.check_monitor_config = check_config
        self.change_monitor_config = change_config
        self.log = log
        self.lora = lora

    def apply_location(
            self, 
            location,
            status_topic, get_status_topic,
            config_topic, get_config_topic, set_config_topic,
            info_topic, alarm_topic, 
            vid_topic, 
            ctrl_ready_topic, control_topics
            ):
        self.status_topic = status_topic.replace('<location>', location)
        self.get_status_topic = get_status_topic.replace('<location>', location)
        self.config_topic = config_topic.replace('<location>', location)
        self.get_config_topic = get_config_topic.replace('<location>', location)
        self.set_config_topic = set_config_topic.replace('<location>', location)
        self.info_topic = info_topic.replace('<location>', location)
        self.alarm_topic = alarm_topic.replace('<location>', location)
        self.vid_topic = vid_topic.replace('<location>', location)
        self.ctrl_ready_topic = ctrl_ready_topic.replace('<location>', location)
        self.control_topics = []
        for i in range(len(control_topics)):
            self.control_topics.append(control_topics[i].replace('<location>', location))

    def _on_connect(self, client, userdata, flags, rc):
        if rc==0:
            if self.log is True: self.logger.info(f'MQTT - connected OK Returned code {rc}')
        else:
            if self.log is True: self.logger.info(f'MQTT - Bad connection Returned code {rc}')
        topics = [(self.vid_topic,0),
                  (self.get_status_topic,0),
                  (self.get_config_topic,0),
                  (self.set_config_topic,0)]
        for topic in self.control_topics:
            topics.append((topic,0))
        if self.log is True: self.logger.info(f'MQTT - subscribe: {topics}')
        client.subscribe(topics)
        self.pubStatus(self.check_monitor_status())

    def _on_message(self, client, userdata, msg):
        #print(f'recieved msg from {msg.topic}')
        if self.log is True: self.logger.info(f'MQTT - recieved msg from {msg.topic}')
        if msg.topic == self.get_status_topic: # return status
            self.pubStatus(self.check_monitor_status())
        elif msg.topic == self.get_config_topic: # return config
            self.pubConfig(self.check_monitor_config())
        elif msg.topic == self.set_config_topic: # write to config.json
            changed_config = self.change_monitor_config(json.loads(msg.payload))
            self.pubConfig(changed_config)
        elif msg.topic == self.control_topics[0]: # control require
            pass
            # if self.ctrl['status'] == 'normal':
            #     self.ctrl['should-control'] = True
        elif msg.topic == self.control_topics[1]: # control stop
            pass
            # if self.ctrl['status'] == 'controlling':
            #     print('stopping ctrl')
            #     self.ctrl['should-control'] = False
            #     self.ctrl['event'].set()
        elif msg.topic == self.control_topics[2]: # control led
            payload = json.loads(msg.payload)
            for id in payload:
                self.lora.send(target=id, codes=payload[id], channel=2)
        elif msg.topic == self.control_topics[3]: # control motion
            payload = json.loads(msg.payload)
            for id in payload['id'].split(','):
                self.lora.send(target=id, codes=payload['motion'], channel=2)
        elif msg.topic == self.control_topics[4]:  # control mode
            pass
            # if self.ctrl['status'] == 'controlling':
            #     payload = json.loads(msg.payload)
            #     self.ctrl_content = {
            #         'id':payload['id'],
            #         'code':payload['mode']
            #     }
            #     self.ctrl['event'].set()

    #-------------------------------------------------#

    def ctrl_ready(self):
        self.client.publish(self.ctrl_ready_topic, 'nothing')

    def gen_ctrl_content(self, msg):
        self.ctrl_content = '123'
    
    def pubStatus(self, status):
        if self.log is True: self.logger.info((f'MQTT - publish to {self.status_topic}'))
        self.client.publish(self.status_topic, json.dumps(status))

    def pubConfig(self, config:dict):
        if self.log is True: self.logger.info((f'MQTT - publish to {self.config_topic}'))
        self.client.publish(self.config_topic, json.dumps(config))

    def pubInfo(self, payload):
        if self.log is True: self.logger.info((f'MQTT - publish to {self.info_topic}'))
        self.client.publish(self.info_topic, payload)

    def alarm(self, payload):
        if self.log is True: self.logger.info((f'MQTT - publish to {self.alarm_topic}'))
        self.client.publish(self.alarm_topic, payload)

    #-------------------------------------------------#

    def start(self, host, port, user, psw):
        self.client = mqtt.Client()
        self.client.username_pw_set(user, psw)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(host, port)
        self.client.loop_start()
        if self.log is True: self.logger.info('MQTT - mqtt client start')

if __name__ == '__main__':
    pass