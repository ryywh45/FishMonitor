## 目錄
* [文件結構](#文件結構)
* [佈署](#佈署)
  * [安裝pm2](#1-安裝pm2)
  * [安裝python-libraries](#2-安裝python-libraries)
  * [更改配置檔](#3-更改配置檔)
  * [新增env檔](#4-新增env檔)
  * [啟動程式](#5-啟動程式)
  * [轉傳器額外設定](#6-轉傳器額外設定)
  * [設定開機啟動](#7-設定開機啟動)
  * [重開機](#8-重開機)
* [查看執行狀態](#查看執行狀態)
  * [即時查看log](#即時查看log)
  * [查看歷史log](#查看歷史log)
* [程式說明文檔](docs/code.md)
* [MQTT Topic](docs/topic.md)

## 文件結構
```
|--main
|    |--Monitor.py   // 主程式
|    |--config.json  // 配置檔案
|    |--requirements.txt  // dependencies
|    |--modules
|    |  |--animals.py   // 儲存魚資料的class
|    |  |--lora.py      // lora發送相關
|    |  |--fishled.py   // 切換led用
|    |  |--joystick.py  // 遙控器相關
|    |  |--mqtt.py      // mqtt相關
|    |  |--line.py      // 發送line notify
|    |  └--capCam.py    // 已停用
|    |--logs            // 存放各功能的log
|    |  |--monitor
|    |  |--mqtt
|    |  |--lora
|    |  └--joystick
└--docs
|    |--code.md   // 程式說明
|    └--topic.md  // mqtt主題說明
```

## 佈署
### 1. 安裝pm2
```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
```
在terminal打nvm看看，如果沒有，重開terminal
```
nvm install --lts node
npm install pm2 -g
```
### 2. 安裝python libraries
```
pip install -r requirements.txt
```
### 3. 更改[配置檔](main/config.json)
配置檔說明如下
(json檔裡面沒有註解，所以不要把底下的文字整個貼進config.json)
```
{
    "monitor":true,  // true=監控, false=轉傳器
    
    "location":"003001001",  // 水池編號，對應到網站上的水池  

    "mqtt_flag":true,  // 是否啟用mqtt
    "cam_flag":false,  // 是否啟用cam，維持在false，現在沒有對應功能
    "log":true,  // 是否啟用log
    "api":false,  // 是否開啟轉傳器led顯示功能

    // mqtt主題名稱定義
    "status_topic": "Monitor/status/<location>",
    "get_status_topic": "Monitor/status/<location>/get",
    "config_topic": "Monitor/config/<location>",
    "set_config_topic": "Monitor/config/<location>/set",
    "get_config_topic": "Monitor/config/<location>/get",
    "info_topic": "Fish/info/<location>",
    "alarm_topic": "Fish/alarm/<location>",
    "get_video_topic": "Fish/video/<location>/get",
    "control_ready_topic": "Fish/control/<location>/ready",
    "control_topics": [
        "Fish/control/<location>/require",
        "Fish/control/<location>/stop",
        "Fish/control/<location>/led",
        "Fish/control/<location>/motion",
        "Fish/control/<location>/mode"
    ],

    "pub_interval": 60,  // 上傳資料到網站的間隔，單位秒
    "same_err_interval": 3600,  // 偵測到相同錯誤碼時，在幾秒之內不重複警報

    "serial_timeout": 1.5,  // lora讀取資料的最大等待時間
    "retry_limit": 5,  // lora詢問無回應時的重問次數，同時也是搜尋遙控器的重試次數
    "find_fish_interval": 300,  // 找新魚的間隔，單位秒
    "queue_limit":10,  // 轉傳器指令保存上限，超過丟棄（小屁孩亂點抑制）
    
    "video_duration": 120,  // 已棄用
    "video_storage_limit": 10,  // 已棄用

    // 遙控器配置
    "joysticks":{
        "BFF19B62":{  // 遙控器id
            "ids":["3004"],  // 綁定的魚id
            "priority":30,  // 優先度
            "timeout":180,  // 超時，目前無作用
            "enable": {  // true=啟用功能, flase=關閉功能
                "forward": true,      // 前進 
                "left": true,         // 左轉
                "right": true,        // 右轉
                "floating": true,     // 上浮
                "diving": true,       // 下潛
                "middle": true,       // 平游
                "switch_mode": true,  // 切換游動模式
                "led": true,          // 更改led
                "auto": false,        // 進自動
                "leave_auto": false   // 退出自動
            }
        },
        "9D099982":{
            "ids":["FF"],  // 廣播的遙控器
            "priority":30,
            "timeout":180,
            "enable": {
                "forward": true,
                "left": true,
                "right": true,
                "floating": true,
                "diving": true,
                "middle": true,
                "switch_mode": true,
                "led": true,
                "auto": false,
                "leave_auto": false
            }
        },
    }
}
```
### 4. 新增env檔

在main資料夾底下，執行
```
sudo nano .env
```
複製以下文字，貼上後存檔退出
```
COMPORT1=/dev/ttyUSB0
COMPORT2=/dev/ttyUSB1
BAUD=9600

AUTO_CHANNEL=7
CTRL_CHANNEL=2

MQTT_HOST=
MQTT_PORT=
MQTT_USER=
MQTT_PSW=
```
### 5. 啟動程式
```
pm2 start Monitor.py --interperter=python3
```
### 6. 轉傳器額外設定
轉傳器才要做這段設定
```
pip install "fastapi[all]"
pip install gpiozero
pm2 start localapi.py --interperter=python3
```
*如果轉傳器要離線運行，mqtt_flag可為true，重新連上網路後重開機即可
### 7. 設定開機啟動
```
pm2 starup
```
pm2會輸出一行指令讓你複製貼上，如下，以實際輸出為準
```
sudo su -c "env PATH=$PATH:/home/unitech/.nvm/versions/node/v14.3/bin pm2 startup <distribution> -u <user> --hp <home-path>
```
```
pm2 save
```
### 8. 重開機
```
sudo reboot
```
## 查看執行狀態
logs資料夾下有四個分類，分別是不同功能的log。
### 即時查看log
在logs資料夾下，執行
```
tail -f monitor/monitor.log lora/lora.log joystick/joystick.log mqtt/mqtt.log
```
不需要看哪個部分就刪掉上面指令的對應部分就好
### 查看歷史log
```
sudo nano monitor/monitor.log.2023-10-30
```
