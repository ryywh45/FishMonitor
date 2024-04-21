import serial
from queue import Queue, PriorityQueue
from dataclasses import dataclass, field
from time import sleep
from requests import post

class Lora:
    logger = None

    def __init__(self, port, baud, timeout, enable_logging=True, api=False):
        """ Open serial port and initialize message queue """
        try:
            self.ser = serial.Serial(port, baud, timeout=timeout)
        except serial.SerialException as e:
            print(f"Serial port {port} not found. {e}")
            if enable_logging: self.logger.error(f"Serial port {port} not found. {e}")
            exit()
        self.msg_queue = PriorityQueue()
        self.res_queue = Queue()
        self.enable_logging = enable_logging
        self.api = api

    def send(self, target:str, codes:str, channel=7, need_response=False, priority=99):
        """ Just call this function to send lora message """
        self.msg_queue.put(LoraMsg(priority, target, codes, channel, need_response))
        if need_response:
            # block until response is received
            return self.res_queue.get()
        else:
            return None
        
    def send_loop(self):
        """ Send messages in queue with priority """
        # Create a thread to run this function
        while True:
            loraMsg: LoraMsg = self.msg_queue.get()
            self._send(loraMsg.target, loraMsg.codes, loraMsg.channel)
            if loraMsg.need_response:
                res = self._receive()
                self.res_queue.put(res)
            if self.api is True: 
                try: post('http://127.0.0.1:8000/api/led/lora/trig')
                except: pass
            sleep(0.25)

    def _send(self, target:str, codes:str, channel=int):
        """ Send directly without queue """
        if self.enable_logging: self.logger.debug(f'Lora - send {codes} to {target} in ch{channel}')
        try:
            payload = self._process_data(target, codes, channel)
            self.ser.write(payload)
        except Exception as e:
            if self.enable_logging: self.logger.error(f'Lora - {e}')
            print(f'Lora - {e}')

    def _receive(self):
        """ Receive data from lora """
        data = self.ser.readline()
        return str(data)[2:-2].split(",,")
        # return data.decode().strip().split(",,") *(need to test).
    
    def _process_data(self, target:str, codes:str, channel=int):
        """ Process data to send """
        payload = bytearray()
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
        
        return payload
    

@dataclass(order=True)
class LoraMsg():
    """ Message format of lora """
    priority: int
    target: str = field(compare=False)
    codes: str = field(compare=False)
    channel: int = field(compare=False)
    need_response: bool = field(compare=False)