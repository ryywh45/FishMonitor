import usb.core
import usb.util
from requests import post
from threading import Lock
from modules.fishled import FishLED

class Joystick():
    vendor_id = 0x046d
    product_id = 0xc21f
    all = []
    logger = None
    def __init__(self, id, bind_ids, ep, priority, enable, timeout=180, log=True, api=True, lock=Lock()):
        self.id = id
        self.bind_ids = bind_ids # ff is not support
        self.bind_fishs = []
        self._ep = ep
        self.priority = priority
        self.enable = enable
        self._timeout_count = 0
        self.timeout_limit = timeout # sec
        self._closed = False
        self.press_lhat = False
        self.log = log
        self.api = api
        self.enable_lock = lock

    def __repr__(self) -> str:
        return self.id
    
    #----------------------------------------------------------------#
    
    @classmethod
    def find(cls, joy_config, log, api):
        joys = [str(joy) for joy in cls.all]
        if log is True: cls.logger.info(f'Joystick - finding with vendor-id={hex(cls.vendor_id)}, product-id={hex(cls.product_id)}')
        devices = usb.core.find(
            idVendor = cls.vendor_id,
            idProduct = cls.product_id,
            find_all=True
            )
        try:
            for f710 in devices:
                id = usb.util.get_string(f710, f710.iSerialNumber)
                if id in joys: continue
                if f710.is_kernel_driver_active(0):
                    try:
                        f710.detach_kernel_driver(0)
                    except usb.core.USBError as e:
                        if log is True: cls.logger.warning(f"Joystick - Could not detatch kernel driver from interface({0}): {str(e)}")
                if id in joy_config:   
                    if log is True: cls.logger.info(f'Joystick - {id} found: {joy_config[id]}')
                    cls.all.append(Joystick(
                        id,
                        joy_config[id]['ids'],
                        f710.get_active_configuration()[(0,0)][0],
                        int(joy_config[id]['priority']),
                        list(joy_config[id]['enable'].values()),
                        int(joy_config[id]['timeout']),
                        log,
                        api
                    ))
                else:
                    print(f'Joystick - unknown device found: {id}')
                    if log is True: cls.logger.warning(f'Joystick - unknown device found: {id}')
        except Exception as error:
            print(f'Error: {error}')
            if log is True: cls.logger.warning(f'Error: {error}')

    #----------------------------------------------------------------#

    def read(self):
        try:
            data = list(self._ep.read(0x20, timeout=1000))
        except Exception as error:
            self._timeout_count += 1
            if self._timeout_count >= self.timeout_limit:
                self._timeout_count = 0
                if self.log is True and self._closed is False: 
                    self.logger.info(f'Joystick - {self.id} timeout')
                    return 0
            return None
        if self.api is True: 
            try: post('http://127.0.0.1:8000/api/led/joy/trig')
            except: pass
        self._timeout_count = 0
        try:
            lhat = data[2]
            d3 = data[3]
            mode = data[14]
        except:
            return None
        with self.enable_lock:
            # if mode == 188:
                if (lhat == 0 and self.press_lhat is True) or d3 == 4:
                    self.press_lhat = False
                    return 'X' # stop
                # LB
                elif d3 == 1 and self.enable[8] is True: 
                    return 'A' # auto
                # RB
                elif d3 == 2 and self.enable[9] is True: 
                    return 'a' # leave auto
                # Y button
                elif d3 == 128 and self.enable[3] is True: 
                    return 'U' # floating
                # A button
                elif d3 == 16 and self.enable[4] is True: 
                    return 'D' # diving
                # Lhat-up
                elif lhat == 1 and self.enable[0] is True:
                    self.press_lhat = True
                    return 'O' # forward
                # Lhat-left
                elif lhat == 4 and self.enable[1] is True:
                    self.press_lhat = True
                    return 'L' # left
                # Lhat-right
                elif lhat == 8 and self.enable[2] is True:
                    self.press_lhat = True
                    return 'R' # right
                # Lhat-down
                elif lhat == 2 and self.enable[5] is True:
                    self.press_lhat = True
                    return 'M' # middle
                # X button
                elif d3 == 64 and self.enable[6] is True:
                    return 'S' # switch mode
                # B button
                elif d3 == 32 and self.enable[7] is True:
                    return FishLED.next()
                else:
                    return 'other'
            # else:
            #     if self.log is True: self.logger.warning(f'Joystick - {self.id}: unexpexted mode {data[14]}')

    def read_to_queue(self, lora):
        while True:
            code = self.read()
            if code != None: # no data
                if self.log is True: self.logger.info(f'Joystick - from {self.id}: {code}')
                if code != 0:
                    if self._closed is True:
                        self._closed = False
                        if self.log is True: self.logger.info(f'Joystick - {self.id} back')
                    if code == 'other':
                        pass
                    else:
                        self._apply_ctrl_status(self.id)
                        for id in self.bind_ids:
                            lora.send(target=id, codes=code, channel=2, priority=self.priority)
                        if code == 'S': # stop after switch mode
                            for id in self.bind_ids:
                                lora.send(target=id, codes='X', channel=2, priority=self.priority)
                else: # timeout
                    self._apply_ctrl_status(None)
                    self._closed = True
            else:
                continue

    #----------------------------------------------------------------#

    def change_timeout(self, sec):
        self.timeout_limit = sec

    def _apply_ctrl_status(self, status):
        try:
            for fish in self.bind_fishs:
                fish.ctrl_by = status
        except: pass

    def test(self):
        from sys import stdout
        print(f'start test {self.id}')
        timeout_count = 0
        while True:
            #sleep(0.05)
            try:
                data = list(self._ep.read(0x20, timeout=1000))
            except:
                timeout_count += 1
                if timeout_count >= self.timeout_limit:
                    print(f'\n{self.id} timeout')
                    break
                continue
            timeout_count = 0
            print(f"\r{self.id}: {data}".ljust(70,' '), end='')
            stdout.flush()
            if data[3] == 1:
                print(f'\n{self.id} closed')
                break

if __name__ == '__main__':

    config = {
        "35139CDA":{"ids":["3049"], "priority":30, "timeout":180, "enable": {"forward": True,"left": True,"right": True,"floating": True,"diving": True,"middle": True,"switch mode": True,"led": True,"auto": True,"leave auto": True}}, #dead
        "0216FEDA":{"ids":["3049"], "priority":30, "timeout":180, "enable": {"forward": True,"left": True,"right": True,"floating": True,"diving": True,"middle": True,"switch mode": True,"led": True,"auto": True,"leave auto": True}},
        "BFF19B62":{"ids":["3036"], "priority":30, "timeout":180, "enable": {"forward": True,"left": True,"right": True,"floating": True,"diving": True,"middle": True,"switch mode": True,"led": True,"auto": True,"leave auto": True}},
        "9D099982":{"ids":["3049"], "priority":30, "timeout":180, "enable": {"forward": True,"left": True,"right": True,"floating": True,"diving": True,"middle": True,"switch mode": True,"led": True,"auto": True,"leave auto": True}},
        "65AD910B":{"ids":["3049"], "priority":30, "timeout":180, "enable": {"forward": True,"left": True,"right": True,"floating": True,"diving": True,"middle": True,"switch mode": True,"led": True,"auto": True,"leave auto": True}},
        "08149935":{"ids":["3049"], "priority":30, "timeout":180, "enable": {"forward": True,"left": True,"right": True,"floating": True,"diving": True,"middle": True,"switch mode": True,"led": True,"auto": True,"leave auto": True}},
        "DCF59BA0":{"ids":["3049"], "priority":30, "timeout":180, "enable": {"forward": True,"left": True,"right": True,"floating": True,"diving": True,"middle": True,"switch mode": True,"led": True,"auto": True,"leave auto": True}}
    }

    Joystick.find(config, False, False)

    for joy in Joystick.all:
        joy.test()

    for joy in Joystick.all:
        while True:
            print(joy.read())
