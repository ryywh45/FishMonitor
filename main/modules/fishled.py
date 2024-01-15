class FishLED:
    color = ['K0','K1','K2','K3','K4','K5']
    now = 0
    @classmethod
    def next(cls):
        cls.now = cls.now + 1 if cls.now < len(cls.color)-1 else 0
        return cls.color[cls.now]