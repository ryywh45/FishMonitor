from threading import Thread
from time import time, sleep
from dotenv import load_dotenv
from os import getenv
from requests import post
import json
import datetime

from modules.animals import Animal, Fish, Turtle
from modules.lora import Lora
from modules.mqtt import MQTT_Client
from modules.joystick import Joystick
from modules.line import lineNotify


class Monitor():
    def __init__(self):
        self.should_pub = False
        self.should_find = False
        self.logger = self._set_logger('monitor')
        Joystick.logger = self._set_logger('joystick')
        load_dotenv()
        self._auto_channel = int(getenv("AUTO_CHANNEL"))
        self._ctrl_channel = int(getenv("CTRL_CHANNEL"))
        self.line_token = getenv("LINE_TOKEN")
        with open('config.json', 'r') as f:
            config = json.load(f)
            self._location = config["location"]
            self._mqtt_flag = config["mqtt_flag"]
            self._cam_flag = config["cam_flag"]
            self._retry_limit = config["retry_limit"]
            self._pub_interval = config['pub_interval']
            self._find_interval = config['find_fish_interval']
            self._same_err_interval = config['same_err_interval']
            self.log = config["log"]
            self.api = config["api"]
            self.notify_interval = int(config["notify_interval"])
            Animal.lora = Lora(
                getenv("COMPORT1"),
                getenv("BAUD"),
                config["serial_timeout"],
                config["queue_limit"],
                self._set_logger('lora'),
                self.api
            )
            if config["monitor"]:
                self.mode = 'monitor'
            else:
                self.mode = 'transceiver'
            if self._mqtt_flag is True:
                self._mqtt_client = MQTT_Client(
                    self._location,
                    self._set_logger('mqtt'),
                    self.check_status,
                    self.check_config,
                    self.change_config,
                    Animal.lora,
                    self.log
                )
                self._mqtt_client.apply_location(
                    self._location,
                    config["status_topic"], config["get_status_topic"],
                    config["config_topic"], config["get_config_topic"], config["set_config_topic"],
                    config["info_topic"], config["alarm_topic"],
                    config["get_video_topic"],
                    config["control_ready_topic"], config["control_topics"]
                )
                try:
                    self._mqtt_client.start(
                        getenv("MQTT_HOST"),
                        int(getenv("MQTT_PORT")),
                        getenv("MQTT_USER"),
                        getenv("MQTT_PSW")
                    )
                except:
                    self.logger.warning("Monitor - could not start mqtt")
                    self._mqtt_flag = False
            self._find_joystick(config["joysticks"])
        self.status = self.check_status()

    def _setup(self):
        if self._cam_flag is True:
            self._cam.start()

        Animal.lora.send('FF', 'z', self._auto_channel)
        # Animal.lora.send('FF', 'z', self._ctrl_channel, read=False)
        # self._find(channel = self._ctrl_channel)
        self._find(channel=self._auto_channel)

        if self._mqtt_flag is True:
            Thread(target=self._pub_timer).start()
        Thread(target=self._find_timer).start()

    def _set_logger(self, name, level='debug'):
        import logging
        from logging.handlers import TimedRotatingFileHandler
        logger = logging.getLogger(name)
        log_handler = TimedRotatingFileHandler(
            f'./logs/{name}/{name}.log', when='midnight', interval=1, backupCount=60)
        if level == 'debug':
            logger.setLevel(logging.DEBUG)
            log_handler.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '[%(asctime)s] - %(levelname)s - %(message)s')
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        return logger

    # ----------------------------------------------------------------#

    def _find_joystick(self, joys: dict):
        self.logger.info(f'Monitor - finding joystick')
        retry_count = 0
        while retry_count < self._retry_limit:
            Joystick.find(joys, self.log, self.api)
            if len(Joystick.all) != len(joys):
                sleep(5)
                retry_count += 1
            else:
                break
        self.logger.info(f'Monitor - joystick list:{Joystick.all}')

    def check_status(self):
        import subprocess
        import re
        try:
            try:
                eth_out = subprocess.check_output(
                    ["ip", "addr", "show", "eth0"], universal_newlines=True)
                ip = re.findall(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', eth_out)
                eth_mac = re.findall(
                    r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b', eth_out)
            except:
                ip = []
                eth_mac = None
            wlan_out = subprocess.check_output(
                ["ip", "addr", "show", "wlan0"], universal_newlines=True)
            wlan_mac = re.findall(
                r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b', wlan_out)
            if ip == []:  # if eth0 is disconnected
                ip = re.findall(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', wlan_out)
            model = subprocess.check_output(
                ["cat", "/sys/firmware/devicetree/base/model"], universal_newlines=True)
            temp = int(
                open('/sys/class/thermal/thermal_zone0/temp', 'r').read()) / 1000
            ser_num = subprocess.check_output(
                ["cat", "/sys/firmware/devicetree/base/serial-number"], universal_newlines=True)

            status = {
                "location": self._location,
                "ip": ip[0],
                "eth_mac": eth_mac[0],
                "wlan_mac": wlan_mac[0],
                "serial_number": ser_num,
                "model": model[:-1],
                "cpu_temp": temp,
                "status": self.mode
            }
            return status
        except:
            return None

    def check_config(self) -> dict:
        with open('config.json', 'r') as f:
            self.logger.info('Monitor - checking config')
            return json.load(f)

    def change_config(self, new_config: dict) -> dict:
        if list(new_config.keys()) != ['joysticks']:  # special case
            self.logger.debug(f'Monitor - unexpected config')
            return

        self.logger.info(f'Monitor - changing config')
        with open('config.json', 'r') as f:
            config = json.load(f)
        config['joysticks'].update(new_config['joysticks'])
        # new_config['joysticks'] = config['joysticks'] # change other value
        # config.update(new_config)

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        # if 'joysticks' in conf.keys()
        self._reload_joy_conf(config['joysticks'])

        self.logger.info(
            f'Monitor - config has been changed to:\n{json.dumps(config, indent=2)}')
        return config

    def _reload_joy_conf(self, new_config: dict):
        joys_now = [str(joy) for joy in Joystick.all]
        for joyID in new_config:
            if joyID in joys_now:
                joy = Joystick.all[joys_now.index(joyID)]
                with joy.enable_lock:
                    joy.enable = list(new_config[joyID]['enable'].values())
                    joy.bind_ids = new_config[joyID]['ids']

    # ----------------------------------------------------------------#

    def _pub_timer(self):
        while True:
            sleep(self._pub_interval)
            self.should_pub = True

    def _find_timer(self):
        while True:
            sleep(self._find_interval)
            self.should_find = True

    def _scheduled_notify(self, start_hour, end_hour):
        while True:
            now = datetime.datetime.now()

            if start_hour <= now.hour < end_hour:
                try:
                    post('http://127.0.0.1:8000/api/led/stat/blink')
                except:
                    pass

                # init
                self._updateInfo(priority=50)
                msg = '\n' + now.strftime('%Y/%m/%d %H:%M:%S') + '\n'
                Animal.all = []
                Animal.lora.send('FF', 'z', self._auto_channel, priority=50)
                Animal.lora.send('FF', 'z', self._ctrl_channel, priority=50)

                # find and update info
                self._find(self._auto_channel, priority=50)
                self._find(self._ctrl_channel, priority=50)
                self._updateInfo(priority=50)
                self._pubInfo()

                # process msg and send line notify
                for fish in Animal.all:
                    msg += f'鯉魚{fish.id}：電量{fish.bc}%\n'
                try:
                    lineNotify(self.line_token, msg[:-1])
                except Exception as e:
                    self.logger.warning(
                        f"Monitor - could not send line notify: \n{e}")
                    print(f"Monitor - could not send line notify: \n{e}")

                try:
                    self._pubInfo()
                except:
                    pass

                for _ in range(3):        
                    try:
                        post('http://127.0.0.1:8000/api/led/stat/on')
                    except:
                        pass

                sleep(self.notify_interval)
            else:
                sleep(60)

    # ----------------------------------------------------------------#

    def _find(self, channel: int, priority=99):
        print(f'Monitor - finding in lora ch{channel}')
        self.logger.info(f'Monitor - finding in lora ch{channel}')

        retry_count = 0
        while retry_count < self._retry_limit:
            data = Animal.lora.send(
                'FF', 'v', channel, need_response=True, priority=priority)
            try:
                id = data[0].split(',')[1]
                ver = data[1].split(',')[1][:-1]
            except:
                retry_count += 1
                continue

            if id[0] == '3':
                Animal.all.append(Fish(id, ver, channel))
            elif id[0] == '6':
                Animal.all.append(Turtle(id, ver, channel))
            else:
                print(f'Monitor - unexpected id:{id}')
                self.logger.warning(f'Monitor - unexpected id:{id}')
                Animal.all.append(Fish(id, ver, channel))
            Animal.lora.send(f'{id}', 'Z', channel, priority=priority)
            retry_count = 0

        if channel == self._ctrl_channel:
            for joy in Joystick.all:
                for id in joy.bind_ids:
                    for fish in Animal.all:
                        if (fish.channel == self._ctrl_channel) and (fish not in joy.bind_fishs) and (fish.id == id):
                            joy.bind_fishs.append(fish)

        print(f'Monitor - animal list now: {Animal.all}')
        self.logger.info(f'Monitor - animal list now:{Animal.all}')

        # print(f'Monitor - lora transmission success rate:{Animal.lora.success_rate}')
        # self.logger.info(f'Monitor - lora transmission success rate:{Animal.lora.success_rate}')

    def _updateInfo(self, priority=99):
        on_err = False
        for animal in Animal.all.copy():
            # if animal.ctrl_by != None:
            #     continue
            previous_err = animal.err_code
            animal.collect_info(self._retry_limit, priority=priority)
            if animal.active == 0:
                self._alarm(animal.id, -1, int(time()), animal.info)
                if self._cam_flag is True:
                    self._cam.export_video()
                Animal.all.remove(animal)
            elif animal.err_code != 0:
                if (previous_err == animal.err_code and
                   animal.err_time != None and
                   int(time()) - animal.err_time < self._same_err_interval
                    ):
                    return
                on_err = True
                animal.err_time = int(time())
                self._alarm(animal.id, animal.err_code, animal.err_time)
        if on_err and self._cam_flag is True:
            self._cam.export_video()

    def _pubInfo(self):
        if Animal.all == []:
            return
        print('Monitor - publishing fish info')
        self.logger.info('Monitor - publishing fish info')
        payload = {"time": int(time())}
        for animal in Animal.all:
            payload.update(animal.info)
        self._mqtt_client.pubInfo(json.dumps(payload))

    def _alarm(self, id, status, time, info=None):
        print(f'Monitor - alarm: {id}->{status}')
        self.logger.warning(f'Monitor - alarm: {id}->{status}')
        payload = {
            id: status,
            "time": time,
            # "video_uid":self._location+f'{self._cam.curr_vid_id:02d}'
            "video_uid": self._location+'0'
        }
        if self._mqtt_flag is True:
            self._mqtt_client.alarm(json.dumps(payload))
            if info is not None:
                self._mqtt_client.pubInfo(json.dumps(info))

# --------------------------------------------------------------------- #

    def start_ctrl(self):
        sleep(5)
        for joy in Joystick.all:
            Thread(target=joy.read_to_queue, args=(Animal.lora,)).start()
        sleep(10)
        Thread(target=self._scheduled_notify, args=(9, 17)).start()

    def run(self):
        content = ''
        try:
            for key in self.status:
                content += f'-> {key}: {self.status[key]}\n'
        except:
            pass
        print(
            f'Monitor - Start:\n{content}-> mqtt-flag: {self._mqtt_flag}\n-> cam-flag: {self._cam_flag}')
        self.logger.info(
            f'Monitor - Start:\n{content}-> mqtt-flag: {self._mqtt_flag}\n-> cam-flag: {self._cam_flag}')

        self._setup()
        while True:
            if Animal.all == []:
                sleep(1)
            else:
                self._updateInfo()
            if self.should_pub:
                self._pubInfo()
                self.should_pub = False
            if self.should_find:
                # self._find(channel = self._ctrl_channel)
                self._find(channel=self._auto_channel)
                self.should_find = False


if __name__ == '__main__':
    sleep(10)
    monitor = Monitor()
    try:
        if monitor.mode == 'monitor':
            monitor.run()
        else:
            monitor.start_ctrl()
        if monitor.api is True:
            try:
                post('http://127.0.0.1:8000/api/led/stat/on')
            except:
                pass
    except Exception as error:
        sleep(3)
        try:
            post('http://127.0.0.1:8000/api/led/stat/blink')
        except:
            pass
        monitor.logger.warning(f"Error - {error}")
        print(f"Error - {error}")
