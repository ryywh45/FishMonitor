from fastapi import FastAPI
from gpiozero import LED

app = FastAPI()
joy_led = LED(26) # 23 24 25
lora_led = LED(6)
stat_led = LED(5)

joy_led.off()
lora_led.off()
stat_led.blink()


@app.get("/")
def nothing():
    return

@app.post("/api/led/stat/on")
def stat_on():
    stat_led.on()
    return

@app.post("/api/led/stat/blink")
def stat_blink():
    stat_led.blink()
    return

@app.post("/api/led/stat/off")
def stat_off():
    stat_led.off()
    return

@app.post("/api/led/lora/on")
def lora_on():
    lora_led.on()
    return

@app.post("/api/led/lora/off")
def lora_off():
    lora_led.off()
    return

@app.post("/api/led/lora/trig")
def lora_trig():
    lora_led.blink(0.05, 0.05, 1)
    return

@app.post("/api/led/joy/on")
def joy_on():
    joy_led.on()
    return

@app.post("/api/led/joy/off")
def joy_off():
    joy_led.off()
    return

@app.post("/api/led/joy/trig")
def joy_trig():
    joy_led.blink(0.05, 0.05, 1)
    return


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)
