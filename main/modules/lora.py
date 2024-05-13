from serial import Serial, SerialException
from queue import Queue, PriorityQueue
from dataclasses import dataclass, field
from time import sleep
from requests import post
from logging import Logger
from threading import Thread

class Lora:
    logger: Logger = None

    def __init__(self, port:str, baud:int, timeout:float, logger=None, enable_led=False):
        """ Open serial port and initialize message queue """
        Lora.logger = logger
        self._enable_led = enable_led
        try:
            self.ser = Serial(port, baud, timeout=timeout)
        except SerialException as errMsg:
            print(f"Lora - Serial port {port} not found: {errMsg}")
            if Lora.logger is not None: self.logger.error(f"Lora - Serial port {port} not found: {errMsg}")
            exit(1)
        self._msg_queue = PriorityQueue()
        self._res_queue = Queue()
        Thread(target=self._send_loop).start()

    def send(self, target:str, codes:str, channel=7, need_response=False, priority=99):
        """ Just call this function to send lora message """
        self._msg_queue.put(LoraMsg(priority, target, codes, channel, need_response))
        if need_response:
            # block until response is received
            return self._res_queue.get()
        else:
            return None

    def _send_loop(self):
        """ Send messages in queue with priority """
        while True:
            loraMsg: LoraMsg = self._msg_queue.get()
            self._send(loraMsg.target, loraMsg.codes, loraMsg.channel)
            if loraMsg.need_response:
                self._res_queue.put(self._receive())
            if self._enable_led:
                try: post('http://127.0.0.1:8000/api/led/lora/trig')
                except: pass
            sleep(0.25)

    def _send(self, target:str, codes:str, channel=int):
        """ Send directly without queue """
        payload = self._process_data(target, codes, channel)
        try:
            self.ser.write(payload)
        except Exception as e:
            if Lora.logger is not None: self.logger.warning(f'Lora - unable to write to serial: {e}')
            print(f'Lora - unable to write to serial: {e}')
        if Lora.logger is not None: self.logger.debug(f'Lora - send {codes} to {target} in ch{channel}')

    def _receive(self):
        """ Receive data from lora """
        data = str(self.ser.readline())[2:-2].split(",,")
        if Lora.logger is not None: self.logger.debug(f'Lora - received: {data}')
        return data
        # return str(self.ser.readline()).decode().strip().split(",,") *(need to test).
    
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