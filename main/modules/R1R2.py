class SendR1R2:
    message = ['R1','R2']
    now = 1
    @classmethod
    def next(cls):
        cls.now = cls.now + 1 
        if(cls.now > 1):cls.now = 0
        return cls.messsage[cls.now]