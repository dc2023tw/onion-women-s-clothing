# 洋蔥女裝v5(2025.10.11)
import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import time
import json
import asyncio
import datetime

# ----------------- CONFIG -----------------
TOKEN = os.getenv("DISCORD_TOKEN") or "你的Token"
GUILD_ID = None  
LOG_CHANNEL_ID = [id]  # 官方紀錄頻道 ID

IMAGE_FOLDER = "images"        # 圖片資料夾
USAGE_FILE = "usage_log.json"  # 使用次數紀錄
LOG_FILE = "onion_logs.json"   # 日誌紀錄
BAN_FILE = "onion_bans.json"   # 封印資料

MESSAGE_COOLDOWN = 5           # 冷卻（秒）
DELETE_DELAY = 180             # 圖片刪除延遲（秒）
IMMUNE_USERS = [id]  # 免冷卻用戶

last_sent_time = 0.0

# JSON
for filename, default in [(USAGE_FILE, {}), (LOG_FILE, {}), (BAN_FILE, {})]:
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

# ----------------- Bot Init -----------------
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- Helper Functions -----------------
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_images():
    if not os.path.exists(IMAGE_FOLDER):
        return []
    valid_ext = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    return [os.path.join(IMAGE_FOLDER, fn) for fn in os.listdir(IMAGE_FOLDER)
            if os.path.splitext(fn)[1].lower() in valid_ext]

def prune_bans():
    data = load_json(BAN_FILE)
    now = datetime.datetime.now().timestamp()
    new = {uid: ts for uid, ts in data.items() if ts > now}
    if len(new) != len(data):
        save_json(BAN_FILE, new)
    return new

def is_banned(user_id: int):
    data = prune_bans()
    return str(user_id) in data

def log_command(user: discord.User, command_name: str, guild_name: str | None):
    data = load_json(LOG_FILE)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "user": f"{user.name}#{user.discriminator}",
        "id": user.id,
        "command": command_name,
        "time": now,
        "guild": guild_name or "私人訊息"
    }
    idx = str(int(max(data.keys(), default="0")) + 1) if data else "1"
    data[idx] = entry
    save_json(LOG_FILE, data)

async def onion_guard(interaction: discord.Interaction, command_name: str):
    if is_banned(interaction.user.id):
        await interaction.response.send_message(
            "🚫 你已被洋蔥封印，暫時無法使用洋蔥系列指令 😈",
            ephemeral=True
        )
        return False
    guild_name = interaction.guild.name if interaction.guild else "私人訊息"
    log_command(interaction.user, command_name, guild_name)
    return True

# ----------------- Commands -----------------
@bot.tree.command(name="洋蔥女裝", description="送你洋蔥女裝圖片（非 NSFW）")
async def onion_cosplay(interaction: discord.Interaction):
    global last_sent_time
    allowed = await onion_guard(interaction, "洋蔥女裝")
    if not allowed:
        return
    user_id = interaction.user.id
    now = time.time()

    if user_id not in IMMUNE_USERS and (now - last_sent_time < MESSAGE_COOLDOWN):
        remaining = round(MESSAGE_COOLDOWN - (now - last_sent_time), 1)
        await interaction.response.send_message(f"🕒 請稍等 {remaining} 秒後再試！", ephemeral=True)
        return

    images = get_images()
    if not images:
        await interaction.response.send_message("❌ 找不到圖片，請確認 images/ 資料夾內有圖檔。", ephemeral=True)
        return

    selected = random.choice(images)
    usage = load_json(USAGE_FILE)
    uid_str = str(user_id)
    if uid_str not in usage:
        usage[uid_str] = {"name": interaction.user.name, "count": 0}
    usage[uid_str]["count"] += 1
    save_json(USAGE_FILE, usage)

    await interaction.response.defer()
    try:
        sent = await interaction.followup.send(file=discord.File(selected))
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ 發送圖片失敗：{e}", ephemeral=True)
        return

    if user_id not in IMMUNE_USERS:
        last_sent_time = now

    async def delayed_delete(msg: discord.Message):
        await asyncio.sleep(DELETE_DELAY)
        try:
            await msg.delete()
        except Exception:
            pass

    asyncio.create_task(delayed_delete(sent))

    guild_name = interaction.guild.name if interaction.guild else "私人訊息"
    embed = discord.Embed(
        title="🧅 洋蔥女裝使用紀錄",
        description=f"**{interaction.user.mention}** 使用了 `/洋蔥女裝`",
        color=discord.Color.green()
    )
    embed.add_field(name="使用次數", value=f"{usage[uid_str]['count']} 次", inline=True)
    embed.add_field(name="來源", value=guild_name, inline=True)
    embed.add_field(name="使用者ID", value=str(user_id), inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"圖片檔案：{os.path.basename(selected)}")

    try:
        log_ch = bot.get_channel(LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(embed=embed)
    except Exception:
        pass

@bot.tree.command(name="洋蔥語錄", description="隨機送你一句洋蔥語錄 🧅")
async def onion_quote(interaction: discord.Interaction):
    allowed = await onion_guard(interaction, "洋蔥語錄")
    if not allowed:
        return
    quotes = [
        "因為只有你是男娘",
        " .洋蔥女裝",
        "那一天的女裝女裝起來",
        "我純愛戰士",
        "敲碗洋蔥女裝full ver. ",
        "太棒了不要跟他們同流合污",
        "為什麼妳的屁股會長痘痘？4個步驟重獲光滑美臀！",
        "我的 pigue 開始報 error 了",
        "鈔怎麼甚至還有 user install",
        "總有一天的排程會輪到我婆的"
    ]
    selected = random.choice(quotes)
    embed = discord.Embed(title="🧅 洋蔥語錄", description=selected, color=discord.Color.purple())
    embed.set_footer(text="洋蔥智慧 · Onion Wisdom")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="洋蔥日誌", description="查看洋蔥系列指令使用記錄（限管理員）")
@app_commands.checks.has_permissions(administrator=True)
async def onion_log(interaction: discord.Interaction):
    data = load_json(LOG_FILE)
    if not data:
        await interaction.response.send_message("目前沒有洋蔥指令使用記錄。", ephemeral=True)
        return
    entries = sorted(data.items(), key=lambda kv: kv[0], reverse=True)[:10]
    lines = []
    for _k, v in entries:
        lines.append(f"👤 {v['user']} (`{v['id']}`) 在 `{v['guild']}` 使用 `{v['command']}` 於 {v['time']}")
    embed = discord.Embed(title="🧅 洋蔥日誌（最近10筆）", description="\n".join(lines), color=discord.Color.dark_purple())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="洋蔥封印", description="封印某位使用者，使其無法使用洋蔥系列指令（分鐘）")
@app_commands.checks.has_permissions(administrator=True)
async def onion_ban(interaction: discord.Interaction, user: discord.User, minutes: int):
    if minutes <= 0:
        await interaction.response.send_message("請輸入大於 0 的分鐘數。", ephemeral=True)
        return
    data = load_json(BAN_FILE)
    end_ts = datetime.datetime.now().timestamp() + minutes * 60
    data[str(user.id)] = end_ts
    save_json(BAN_FILE, data)
    await interaction.response.send_message(f"✅ 成功封印 {user.mention} {minutes} 分鐘！")
    log_command(interaction.user, f"封印 {user.id} {minutes} 分鐘", interaction.guild.name if interaction.guild else "私人訊息")

# ----------------- Welcome -----------------
@bot.event
async def on_guild_join(guild: discord.Guild):
    embed = discord.Embed(
        title="💠 感謝邀請我進入伺服器！",
        description=(
            f"嗨！我是 **{bot.user.name}** 🤖\n"
            "以下是我的基本資訊與使用方式：\n\n"
            "📜 **功能簡介**\n"
            "・輸入 `/洋蔥女裝`（非 NSFW，可用於任何頻道）\n"
            "・輸入 `/洋蔥語錄` 來獲取一句語錄\n\n"
            "🛠️ **管理員提示**\n"
            "・可設定頻道權限避免洗版\n\n"
            "🖥️ **開發者**：[DEV]"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"伺服器：{guild.name}")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else discord.Embed.Empty)
    for ch in guild.text_channels:
        if ch.permissions_for(guild.me).send_messages:
            try:
                await ch.send(embed=embed)
            except Exception:
                pass
            break

# ----------------- on_ready -----------------
@bot.event
async def on_ready():
    print(f"✅ 已登入為 {bot.user} (ID: {bot.user.id})")
    try:
        if GUILD_ID:
            await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        else:
            await bot.tree.sync()
        print("✅ Slash 指令同步完成！")
    except Exception as e:
        print("❌ 指令同步失敗:", e)

# ----------------- Run -----------------
if __name__ == "__main__":
    bot.run(TOKEN)
