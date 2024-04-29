class Animal:
    lora = None
    all = []
    def __init__(self, id='0', version='', channel=0, bc=0, err_code=0, active=0):
        self.id = id
        self.version = version
        self.channel = channel
        self.bc = bc
        self.err_code = err_code
        self.active = active
        self.err_time = None

    def __repr__(self) -> str:
        return self.id

    def collect_info(self, retry_limit, timeout=1.5, priority=99):
        retry_count = 0
        while retry_count < retry_limit:
            info = self.lora.send(self.id, 'i', self.channel, need_response=True, priority=priority)
            if info[0] != '':
                # self.lora.success_count += 1
                self.active = 1
                for data in info:
                    data = data.split(',')
                    if data[0] == 'bc': 
                        try: self.bc = int(data[1])
                        except: pass
                    if data[0] == 'err':
                        try: self.err_code = int(data[1])
                        except: pass
                return retry_count + 1
            else:
                retry_count += 1
                continue
        self.active = 0
        self.lora.send(self.id, 'z', self.channel, priority=priority)
        return 0
    
    @property
    def info(self):
        return { self.id:{
                    "bc":self.bc,
                    "err":self.err_code,
                    "active":self.active,
                    "version":self.version }}
    
    
class Fish(Animal):
    def __init__(self, id, version=0, channel=0, bc=0, err_code=0, active=0):
        super().__init__(
            id, version, channel, bc, err_code, active
        )

class Turtle(Animal):
    def __init__(self, id, version=0, channel=0, bc=0, err_code=0, active=0):
        super().__init__(
            id, version, channel, bc, err_code, active
        )

if __name__ == '__main__':
    from serial import Serial
    ser = Serial('/dev/ttyUSB1', 9600)
    reg = False
    base = bytearray()
    base.append(0x00)
    base.append(0x00)
    base.append(0x07)
    while True:
        data = str(ser.readline())[2:-3]
        print(data)
        if data == 'Z':
            reg = True
        elif data == 'z':
            reg = False
        elif data == 'v' and reg is False:
            ser.write(base + b'id,3087,,sw_ver,8.7_test\n')
        elif data == 'i':
            ser.write(base + b'id,3087,,bc,100,,err,0,,\n')
