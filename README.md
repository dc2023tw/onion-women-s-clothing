# 洋蔥女裝 Discord Bot 

這是一個洋蔥女裝 Discord Bot

## 功能

*   `/洋蔥女裝`: 隨機發送一張洋蔥女裝圖片。
*   `/洋蔥語錄`: 隨機發送一則洋蔥語錄。

### 開發者專用功能

*   `/開發者面板`: 開啟一個多功能的開發者控制面板，包含以下功能：
    *   更改 Bot 名稱或活動狀態。
    *   更改 Bot 的線上狀態 (online, idle, dnd, invisible)。
    *   查看主機的系統資訊 (CPU, RAM, 磁碟使用率)。
    *   安全關機。
*   `/洋蔥封印`: 暫時禁止特定使用者使用 Bot 指令。
*   `/洋蔥解封`: 解除使用者的封印。

### 配置項

| 配置項                                  | 說明                                                                 |
| ----------------------------------------- | -------------------------------------------------------------------- |
| `DISCORD_TOKEN`                           | **(必要)** 您的 Discord Bot Token。                                  |
| `DISCORD_GUILD_ID`                        | **(選用)** 您的 Discord 伺服器 ID。如果設定，斜線指令將只會在這個伺服器中快速同步。 |
| `DISCORD_LOG_CHANNEL_ID`                  | **(選用)** 用於記錄指令使用情況的文字頻道 ID。                       |
| `DISCORD_DEVELOPER_IDS`                   | **(選用)** 開發者的 Discord 使用者 ID 列表，請填寫數字列表，例如 `[123456789, 987654321]`。    |
| `DISCORD_DEV_IDS`                         | **(選用)** 具有部分開發權限的使用者 ID 列表，請填寫數字列表。 |
| `DISCORD_IMMUNE_USERS`                    | **(選用)** 免受指令冷卻時間限制的使用者 ID 列表，請填寫數字列表。 |

### 執行

1.  安裝所需的 Python 套件：
    ```bash
    pip install -r requirements.txt
    ```
2.  編輯 
3.  執行 Bot：
    ```bash
    python bot.py
    ```

## 檔案結構

*   `bot.py`: 主要的 Bot 程式碼。
*   `images/`: 存放圖片的資料夾。
*   `usage_log.json`: 記錄使用者指令使用次數。
*   `onion_ban.json`: 儲存被封印使用者的資料。
## 必須
  
*   PRESENCE INTENT
*   SERVER MEMBERS INTENT
*   MESSAGE CONTENT INTENT

