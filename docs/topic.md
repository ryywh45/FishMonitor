## MQTT-Topics
| Topic | Content |
|----|----|
| [Monitor/status/`<location>`](#topic--monitorstatuslocation) | 回傳監控站的狀態 |
| [Monitor/status/`<location>`/get](#topic--monitorstatuslocationget) | 要求回傳監控狀態 |
| [Monitor/config/`<location>`](#topic--monitorconfiglocation) | 回傳監控站的設定檔 |
| [Monitor/config/`<location>`/get](#topic--monitorconfiglocationget) | 要求回傳監控設定檔 |
| [Monitor/config/`<location>`/set](#topic--monitorconfiglocationset) | 更改監控的設定檔 |
| [Fish/info/`<location>`](#topic--fishinfolocation) | 定時回傳魚的資料 |
| [Fish/alarm/`<location>`](#topic--fishalarmlocation) | 通報單隻魚的狀態 |
| [Fish/control/`<location>`/require](#topic--fishcontrollocationrequire停用) | 要求控制(停用) |
| [Fish/control/`<location>`/ready](#topic--fishcontrollocationready停用) | 可以開始控制(停用) |
| [Fish/control/`<location>`/stop](#topic--fishcontrollocationstop停用) | 停止控制(停用) |
| [Fish/control/`<location>`/led](#topic--fishcontrollocationled) | 魚led的顏色 |
| [Fish/control/`<location>`/motion](#topic--fishcontrollocationmotion-未完成) | 魚的游動方向(未完成) |
| [Fish/control/`<location>`/mode](#topic--fishcontrollocationmode-未完成) | 魚的游動模式(未完成) |
| [Fish/video/`<location>`/get](#topic--fishvideolocationget停用) | 要求影片(停用) |


### Topic : `Monitor/status/<location>`
訂閱這個，接收狀態用
```
{
  "location":str
  "ip":str,
  "mac":str,
  "model":str,
  "cpu_temp":float,
  "status":str
}
```
| `<status>` | 狀態 | 
|----|----|
| monitor | 監控器 |
| transceiver | 轉傳器 |
--------------------------------------------
### Topic : `Monitor/status/<location>/get`
主動要求monitor status的方法
```
"nothing"
```
--------------------------------------------
### Topic : `Monitor/config/<location>`
訂閱這個，用來接收設定檔用，完整設定檔如下：
```
{
  "location":"002001001",

  "mqtt_flag":false,
  "cam_flag":false,
  "log":true,
  "api":false,

  "status_topic": "Monitor/status/<location>",
  "get_status_topic": "Monitor/status/<location>/get",
  "config_topic": "Monitor/config",
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

  "pub_interval": 60,
  "same_err_interval": 3600,

  "serial_timeout": 1.5,
  "retry_limit": 5,
  "find_fish_interval": 300,
  "queue_limit":10,
  
  "video_duration": 120,
  "video_storage_limit": 10,

  "joysticks":{
    "BFF19B62":{
      "ids":["3004"],
      "priority":30,
      "timeout":180,
      "enable": {
          "forward": true,
          "left": true,
          "right": true,
          "floating": true,
          "diving": true,
          "middle": true,
          "switch mode": true,
          "led": true,
          "auto": false,
          "leave auto": false
      }
    },
    "9D099982":{
      "ids":["3006"],
      "priority":30,
      "timeout":180,
      "enable": {
          "forward": true,
          "left": true,
          "right": true,
          "floating": true,
          "diving": true,
          "middle": true,
          "switch mode": true,
          "led": true,
          "auto": false,
          "leave auto": false
      }
    }
  }
}
```
--------------------------------------------
### Topic : `Monitor/config/<location>/get`
要求監控回傳完整的設定檔
```
"nothing"
```
--------------------------------------------
### Topic : `Monitor/config/<location>/set`
只傳送要更改的部分就好。
修改完後，會回傳一次當前設定。
```
{
  "joysticks":{
    "BFF19B62":{
      "ids":["3004"],
      "priority":30,
      "timeout":180,
      "enable": {
        "forward": true,
        "left": true,
        "right": true,
        "floating": true,
        "diving": true,
        "middle": true,
        "switch mode": true,
        "led": true,
        "auto": false,
        "leave auto": false
      }
    }
  }
}
```
以上的資料的意思是更新BFF19B62這支遙控器的設定檔，沒有的話就新增上去。
--------------------------------------------
### Topic : `Fish/info/<location>`
```
{
  "time":<unix_time>,
  "<id>":{"bc":<bc>,"err":<err>,"active":<active>,"version":<version>},
  "3024":{"bc":"98","err":"0","active":1,"version":"1.7.2"},
  "28":{"bc":"20","err":null,"active":0,"version":"1.7.2_test"}
}
```
| 參數 | 說明 | 資料型態 |
|----|----|----|
| `<id>` | 魚的id | str |
| `<bc>`  | 魚的電量 | int |
| `<err>` | 魚的err_code | int |
| `<active>` | 開關機狀態 | int |
| `<version>` | 魚的版本 | str |
| `<unix_time>` | pub時的時間 | int |

| `<active>` | 開關機狀態 |
|----|----|
| 0 | 關機 |
| 1 | 開機 |
--------------------------------------------
### Topic : `Fish/alarm/<location>`
偵測到魚關機或錯誤時會發出提醒，並存下影片
```
{
  <id>:<status>,
  "time":<unix_time>,
  "video_uid":<location><local_id>
}
```
| 參數 | 說明 | 資料型態 |
|----|----|----|
| `<id>` | 魚的id | str |
| `<status>` | 魚的狀態，關機或錯誤 | int |
| `<unix_time>` | 錯誤or關機時間 | int |
| `<area_code>` | 地區編號 | str |
| `<local_id>` | 影片編號 | str |

| `<status>` | 狀態 |.| `<location>` | 地區 |
|----|----|----|----|----|
| -1 | 關機 |.| 002001001 | 北科CSL水池 |
| err_code | 錯誤 |.| |  | 

`"video_uid"`範例: "002001001003", "002001001010"

--------------------------------------------
### Topic : `Fish/video/<location>/get`（停用）
取得特定時間軸的影片，可以要求多支影片
```
{
  "video_uids":<video_uids>
}
```
| 參數 | 說明 | 資料型態 |
|----|----|----|
| `<video_uids>` | 影片的uid | str |

`<video_uids>` : 
| 一支 | 多支 | 全部 |
|----|----|----|
| "00306" | "00203, 00210" | "ALL" | 

--------------------------------------------
### Topic : `Fish/control/<location>/require`（停用）
要控制時，須要先往這個主題發送任意資料
```
"nothing"
```
--------------------------------------------
### Topic : `Fish/control/<location>/ready`（停用）
接收到這個主題的消息時代表可以開始控制
```
"nothing"
```
--------------------------------------------
### Topic : `Fish/control/<location>/stop`（停用）
停止控制，一樣發送任意資料
```
"nothing"
```
--------------------------------------------
### Topic : `Fish/control/<location>/led`
| 指令 | K0 | K1 | K2 | K3 | K4 | K5 |
|----|----|----|----|----|----|----|
| 顏色 | 退出顏色設定 | 紅 | 白 | 綠 | 藍 | 紫 |
```
{
  "3024":"K1",
  "3333":"K3",
  "FF":"K0"
}
```
--------------------------------------------
### Topic : `Fish/control/<location>/motion` (未完成)
控制魚的游動方向
可以控制一隻或多隻魚，或是廣播
```
{
  "id":<ids>,
  "motion":<montion>
}
```
`<ids>` : 
| 一隻 | 多隻 | 廣播 |
|----|----|----|
| "46" | "32,2044,87" | "FF" | 

`<montion>`:
| 停止 | 前進 | 往左 | 往右 | 上升 | 下潛 | 平衡 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| "X" | "O" | "L" | "R" | "U" | "D" | "M" |
--------------------------------------------
### Topic : `Fish/control/<location>/mode` (未完成)
更改魚的游動模式
可以控制一隻或多隻魚，或是廣播
```
{
  "id":<ids>,
  "mode":<mode>
}
```
`<ids>` : 同上

`<mode>`:
| 一般 | 編號 | 手勢 | 編號 |
|:-:|:-:|:-:|:-:|
| 自動 | "A" | 停止 | "TBD" |
| 退出自動 | "a" | 快速游動 | "TBD" |
| 沿牆 | "W" | 原地轉圈 | "TBD" |
| 退出沿牆 | "w" | 水底快速游動 | "TBD" |
| 切換模式 | S | 召喚至目標點 | "TBD" |
|...|| 閃爍不同的燈 | "TBD" |
|...|| 繞牆 | "TBD" | 

切換模式是輪流切換(活潑/悠遊/睡眠)
