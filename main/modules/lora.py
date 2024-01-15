import serial
from queue import PriorityQueue
from dataclasses import dataclass, field
from typing import Any
from requests import post
from time import sleep

class Lora():
    """Basic class that send code to the fish, also read response by default."""

    logger = None
    def __init__(self, port, baud, timeout, log=True, api=False):
        self._port = port
        self._baud = baud
        self._timeout = timeout
        self._send_count = 0
        self.ser = serial.Serial(self._port, self._baud, timeout=timeout)
        self.success_count = 0
        self.log = log
        self.api = api
    
    def open(self):
        if self.ser.is_open is False:
            self.ser = serial.Serial(self._port, self._baud, timeout=timeout)

    def close(self):
        if self.ser.is_open is True:
            self.ser.close()

    def send(self, target:str, codes:str, channel=7, timeout=None, read=True):
        if self.api is True: 
            try: post('http://127.0.0.1:8000/api/led/lora/trig')
            except: pass
        if codes == 'a': channel = 7
        if self.log is True: self.logger.debug(f'Lora - send {codes} to {target} in ch{channel}')
        if timeout == None: timeout = self._timeout
        payload = bytearray()
        data = ''
        if target == 'ff' or target == 'FF': # Brocast
            payload.append(0xFF)
            payload.append(0xFF)
        else: # Send code to specific fish
            id = int(target)
            payload.append(int(id / 256))
            payload.append(int(id % 256))
        payload.append(channel)
        for code in codes:
            payload.append(ord(code))
        payload.append(ord('\n'))
        #ser = serial.Serial(self._port, self._baud, timeout=timeout)
        ser = self.ser
        ser.write(payload)
        if read is True:
            data = ser.readline()    
        #ser.close()
        self._send_count += 1

        # Format of data: "b'id,1,,bc,30,,err,0,,version,1.6.6,,*'\n"
        return str(data)[2:-2].split(",,")
    
    @property
    def success_rate(self):
        if self._send_count == 0 : return "There's no lora msg sent before"  
        return f'{round(self.success_count / self._send_count * 100, 2)}% ({self.success_count}/{self._send_count})'

@dataclass(order=True)
class LoraMsg():
    """Message format of lora (conctrolling only)"""

    priority: int
    target: Any=field(compare=False)
    code: Any=field(compare=False)

class LoraQueue(PriorityQueue):
    """A priority queue that handle lora sending (conctrolling only)"""

    def setup_lora(self, port, baud, timeout, log, api):
        self.lora = Lora(port, baud, timeout, log, api)

    def _send(self, channel):
        msg = self.get()
        try: self.lora.send(msg.target, msg.code, channel, read=False)
        except Exception as error:
            self.lora.logger.warning(f"Error - {error}")
            print(f"Error - {error}") 

    def send_loop(self, channel):
        while True:
            self._send(channel)
            sleep(0.25)

if __name__ == '__main__':
    #test success rate of each fish
    from datetime import datetime
    from animals import Animal, Fish, Turtle
    import sys
    
    args = sys.argv
    try: timeout = float(args[1])
    except: timeout = 2.0
    try: times = int(args[2])
    except: times = 30
    for i in range(3, len(args)):
        try:
            id = args[i]
            if id[0] == '3': Fish(id)
            elif id[0] == '6': Turtle(id)
        except: pass

    Animal.lora = Lora('/dev/ttyUSB0', 9600, timeout, log=False)
    print('\n'+'Test Start:')
    start_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print(start_time)
    print('==============================================')
    result = []
    for animal in Animal.all.copy():
        Animal.lora._send_count = 0
        Animal.lora.success_count = 0
        for _ in range(times):
            info = Animal.lora.send(animal.id, 'i', 2)
            if info[0] != '':
                Animal.lora.success_count += 1
            print(f'[{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}]: Send:[{animal.id},i] -> Receive:{info}')
        result.append(f'{animal.id}: {Animal.lora.success_rate}')
    print('==============================================')
    print(f"{start_time} - > {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
    print(f'Lora 443 test, timeout:{timeout}')
    for _ in result:
        print(_)
