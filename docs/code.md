# 程式說明文檔
## 目錄
* [主程式](#主程式)
* [Lora](#lora)
* [animal class](#animal-class)
* [MQTT](#mqtt)
* [Joystick](#joystick)

## 主程式
### Monitor.py
```
class Monitor()
    def __init__(self):
        // 讀取config和env
        // 啟動mqtt client
        // 搜尋joystick
        // 檢查裝置狀態

    // 監控啟動初始化
    def _setup(self):
        // 所有魚解除註冊
        // 廣播找魚
        // 啟動pub,find的計時器

    // logger初始化
    def _set_logger(self, name, level='debug'):
        // 檔名為name.log
        // 一天存檔一次，最多存60天

    #----------------------------------------------------------------#

    def _find_joystick(self, joys: dict):
        // joys: config中的joystick設定檔(config["joysticks"])
        // 搜尋遙控器，最多重試config["retry_limit"]次

    def check_status(self):
        // 檢查裝置狀態: location, ip, mac, 樹莓派序列號, 樹莓派型號, cpu溫度 

    def check_config(self) -> dict:
        // 回傳config.json的內容

    def change_config(self, new_config: dict) -> dict:
        // new_config: 新的config["josticks"]
        // 更改config.json的內容
        // *只支援更改config["josticks"]

    def _reload_joy_conf(self, new_config):
        // new_config: 新的config["josticks"]
        // 動態更改遙控器設定

    #----------------------------------------------------------------#

    def _pub_timer(self):
        // timer for mqtt publish fish info

    def _find_timer(self):
        // timer for monitor find fish

    def _scheduled_notify(self, start_hour, end_hour):
        // 轉傳器模式的時候，在每天的9～17點之間每一段時間發出電量通報
        
    #----------------------------------------------------------------#

    def _find(self, channel:int):
        // 找新的魚
        // 廣播小v，有收到回傳就傳大Z註冊

    def _updateInfo(self):
        // 輪循更新魚的資訊
        // 問超過retry_limit次 -> 警報
        // 發現錯誤且上次錯誤時間減現在時間大於same_err_interval -> 警報

    def _pubInfo(self):
        // pub魚的最新資訊

    def _alarm(self, id, status, time, info=None):
        // 發出警報

    #----------------------------------------------------------------#

    def start_ctrl(self):
        // 啟動lora send loop
        // 開始接收遙控器資料

    def run(self):
        // 監控主邏輯

```
## Lora
### lora.py
```
class Lora():
    """Basic class that send code to the fish, also read response by default."""

    def __init__(self, port, baud, timeout, log=True, api=False):
        // 變數定義
        // serial初始化
    
    def send(self, target:str, codes:str, channel=7, need_response=False, priority=99):
        """ Just call this function to send lora message """
        // 傳送codes至target
        // channel: 預設7
        // need_response: 是否等待回傳
        // priority: 優先順序，越小越優先
        // 實際的行為是將LoraMsg放入lora_queue中排隊

    def send_loop(self):
        """ Send messages in queue with priority """

    def _send(self, target:str, codes:str, channel=int):
        """ Send directly without queue """
        // serial write

    def _receive(self):
        """ Receive data from lora """
        // 讀取serial收到的資料，處理後回傳

    def _process_data(self, target:str, codes:str, channel=int):
        """ Process data to send """
        // 處理要放進serial的資料

@dataclass(order=True)
class LoraMsg():
    """Message format of lora"""

```
## Animal class
### animals.py
```
// 通用class
class Animal:
    def __init__(self, id='0', version='', channel=0, bc=0, err_code=0, active=0):
        // 變數定義

    def collect_info(self, retry_limit, timeout=1.5):
        // lora傳送i獲取資訊

// 預留
class Fish(Animal):
    // 目前fish沒有特殊的屬性

//預留
class Turtle(Animal):
    // 目前turtle沒有特殊的屬性

```
## MQTT
### mqtt.py
```
class MQTT_Client():
    def __init__(self, location, logger, check_status, check_config, change_config, lora_queue, lora_msg, log=True):
        // 變數定義

    def apply_location(
            self, 
            location,
            status_topic, get_status_topic,
            config_topic, get_config_topic, set_config_topic,
            info_topic, alarm_topic, 
            vid_topic, 
            ctrl_ready_topic, control_topics
            ):
        // 將實際的location替換進topic

    def _on_connect(self, client, userdata, flags, rc):
        // 連上mqtt broker時的行為:
        // 訂閱所有topic並pub裝置狀態

    def _on_message(self, client, userdata, msg):
        // 收到mqtt消息時的行為:

    #-------------------------------------------------#

    def ctrl_ready(self):
        // 已停用

    def gen_ctrl_content(self, msg):
        // 已停用
    
    def pubStatus(self, status):
        // pub裝置資訊

    def pubConfig(self, config:dict):
        // pub config.json的內容

    def pubInfo(self, payload):
        // pub 魚的最新資訊

    def alarm(self, payload):
        // 發出警報

    #-------------------------------------------------#

    def start(self, host, port, user, psw):
        // 啟動mqtt client，連線至broker
```
## Joystick
### joystick.py
```
class Joystick():
    def __init__(self, id, bind_ids, ep, priority, enable, timeout=180, log=True, api=True, lock=Lock()):
        //變數定義
    
    #----------------------------------------------------------------#
    
    @classmethod
    def find(cls, joy_config, log, api):
        // 透過vendor_id及product_id搜尋遙控器的usb接收器
        // 取出遙控器id並根據傳入的joy_config建立Joystick instance

    #----------------------------------------------------------------#

    def read(self):
        // 讀取遙控器資料，回傳相應的control code

    def read_to_queue(self, lora_queue, LoraMsg):
        // 讀取遙控器資料進lora queue

    #----------------------------------------------------------------#

    def change_timeout(self, sec):
        // 暫時無用

    def _apply_ctrl_status(self, status):
        // 暫時無用

    def test(self):
        // 測試遙控器功能
```
### fishled.py
```
// 一個按鍵輪流發送所有led訊號
class FishLED:
    // ['退出顏色設定','紅','白','綠','藍','紫']
    @classmethod
    def next(cls):
        // 回傳下個顏色
```