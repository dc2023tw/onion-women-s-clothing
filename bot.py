# 洋蔥女裝v6.0.0(2025.11.08)
import discord
from discord.ext import commands
from discord import app_commands
from discord import Embed
from discord import app_commands, Activity, ActivityType
import os
import random
import time
import json
import asyncio
import datetime
import psutil
import pytz  
import sys

# ----------------- CONFIG -----------------
TOKEN = os.getenv("DISCORD_TOKEN") or "YOUR TOKEN"
GUILD_ID = None 
LOCKED = False 
LOG_CHANNEL_ID = ID # 官方紀錄頻道 ID
DEVELOPER_IDS = [ID]  # 開發者 ID
DEV_IDS = [ID]
IMMUNE_USERS = [ID]   # 免冷卻用戶



IMAGE_FOLDER = "images"        # 圖片資料夾
USAGE_FILE = "usage_log.json"  # 使用次數紀錄
LOG_FILE = "onion_logs.json"   # 日誌紀錄
BAN_FILE = "onion_ban.json"   # 封印資料

MESSAGE_COOLDOWN = 5           # 冷卻（秒）
DELETE_DELAY = 180            # 圖片刪除延遲（秒）


last_sent_time = 0.0
tz = pytz.timezone("Asia/Taipei")  

# DEV
def dev_only():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message("🚫 只有開發者可以使用此指令。", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)






for filename, default in [(USAGE_FILE, {}), (LOG_FILE, {}), (BAN_FILE, {})]:
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def check_locked(ctx_or_interaction):
    global LOCKED
    user_id = getattr(ctx_or_interaction, "user", None)
    if user_id is None:  
        user_id = ctx_or_interaction.author.id
    else:
        user_id = ctx_or_interaction.user.id

    if LOCKED and user_id not in DEV_IDS:
        if hasattr(ctx_or_interaction, "response"):
            await ctx_or_interaction.response.send_message(
                "🚫 BOT 已鎖定，無法使用指令。", ephemeral=True
            )
        else:
            await ctx_or_interaction.send("🚫 BOT 已鎖定，無法使用指令。")
        return False
    return True


def is_dev(ctx):
    return ctx.author.id in DEV_IDS


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    ctx = await bot.get_context(message)
    if not await check_locked(ctx):
        return
    await bot.process_commands(message)



def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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
    now = datetime.datetime.now(tz).timestamp()
    new = {uid: ts for uid, ts in data.items() if ts > now}
    if len(new) != len(data):
        save_json(BAN_FILE, new)
    return new

def is_banned(user_id: int):
    data = prune_bans()
    return str(user_id) in data

def log_command(user: discord.User, command_name: str, guild_name: str | None):
    data = load_json(LOG_FILE)
    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
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

# --- /onion say --- 
@bot.tree.command(name="洋蔥語錄", description="隨機送你一句洋蔥語錄 🧅")
async def onion_quote(interaction: discord.Interaction):
    allowed = await onion_guard(interaction, "洋蔥語錄")
    if not allowed:
        return
    quotes = [
        "因為只有你是男娘",
        " .洋蔥女裝",
        "那一天的女裝女裝起來",
        "我看到的只有潛在的垃圾訊息發送者，Discord 已屏蔽該訊息。",
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





@bot.tree.command(name="洋蔥封印", description="封印某位使用者，使其無法使用洋蔥系列指令(縣開發者)")
@dev_only()
async def onion_ban(interaction: discord.Interaction, user: discord.User, minutes: int):
    if minutes <= 0:
        await interaction.response.send_message("❌ 請輸入大於 0 的分鐘數。", ephemeral=True)
        return

    data = load_json(BAN_FILE)
    end_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)).timestamp()
    data[str(user.id)] = end_time
    save_json(BAN_FILE, data)

    await interaction.response.send_message(f"✅ 已封印 {user.mention} {minutes} 分鐘。")


@bot.tree.command(name="洋蔥解封", description="解除某位使用者的洋蔥封印(限開發者)")
@dev_only()
async def onion_unban(interaction: discord.Interaction, user: discord.User):
    data = load_json(BAN_FILE)
    if str(user.id) in data:
        del data[str(user.id)]
        save_json(BAN_FILE, data)
        await interaction.response.send_message(f"✅ 已解除 {user.mention} 的洋蔥封印。")
    else:
        await interaction.response.send_message("⚠️ 該使用者目前未被封印。", ephemeral=True)


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
            "🖥️ **開發者**：[DEV]______"
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



@bot.tree.command(name="dev-bot", description="BotServer")
@dev_only()
async def dev_bot(interaction: discord.Interaction):
    if not bot.guilds:
        await interaction.response.send_message("Bot目前沒有加入任何伺服器。", ephemeral=True)
        return

    lines = []
    for g in bot.guilds:
        lines.append(f"🏷️ {g.name} (`{g.id}`) - 成員數: {g.member_count}")

    embed = discord.Embed(
        title=f"🤖 Bot 加入的伺服器（共 {len(bot.guilds)} 個）",
        description="\n".join(lines),
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


class DevPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="改名稱 / 活動文字", style=discord.ButtonStyle.green)
    async def name_or_activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message("🚫 只有開發者可以使用", ephemeral=True)
            return


        select = discord.ui.Select(
            placeholder="選擇要修改的項目",
            options=[
                discord.SelectOption(label="改名稱", description="修改 BOT 名稱"),
                discord.SelectOption(label="改活動", description="修改 BOT 正在玩的活動")
            ]
        )

        async def select_callback(select_interaction):
            choice = select.values[0]

            if choice == "改名稱":
                await select_interaction.response.send_message("請輸入 BOT 新名稱（2~32 字元）:", ephemeral=True)
                try:
                    msg = await interaction.client.wait_for(
                        "message",
                        check=lambda m: m.author.id in DEV_IDS,
                        timeout=30
                    )
                    if 2 <= len(msg.content) <= 32:
                        await interaction.client.user.edit(username=msg.content)
                        await select_interaction.followup.send(f"✅ 名稱已改為 {msg.content}", ephemeral=True)
                    else:
                        await select_interaction.followup.send("🚫 名稱長度必須介於 2~32 字元！", ephemeral=True)
                except asyncio.TimeoutError:
                    await select_interaction.followup.send("⏰ 時間到，操作取消", ephemeral=True)

            elif choice == "改活動":
                activity_select = discord.ui.Select(
                    placeholder="選擇活動類型",
                    options=[
                        discord.SelectOption(label="正在玩", value="playing"),
                        discord.SelectOption(label="正在聽", value="listening"),
                        discord.SelectOption(label="正在看", value="watching"),
                        discord.SelectOption(label="直播中", value="streaming"),
                    ]
                )

                async def activity_callback(act_interaction):
                    act_type = activity_select.values[0]
                    await act_interaction.response.send_message(f"請輸入活動文字（例如：LOL、音樂）:", ephemeral=True)
                    try:
                        msg = await interaction.client.wait_for(
                            "message",
                            check=lambda m: m.author.id in DEV_IDS,
                            timeout=30
                        )
                        text = msg.content
                        if act_type == "playing":
                            activity = discord.Game(name=text)
                        elif act_type == "listening":
                            activity = discord.Activity(type=discord.ActivityType.listening, name=text)
                        elif act_type == "watching":
                            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
                        elif act_type == "streaming":
                            activity = discord.Streaming(name=text, url="https://twitch.tv/yourchannel")
                        await interaction.client.change_presence(activity=activity)
                        await act_interaction.followup.send(f"✅ 活動已設為 {act_type} {text}", ephemeral=True)
                    except asyncio.TimeoutError:
                        await act_interaction.followup.send("⏰ 時間到，操作取消", ephemeral=True)

                activity_select.callback = activity_callback
                await interaction.followup.send("選擇活動類型:", view=discord.ui.View(timeout=None).add_item(activity_select), ephemeral=True)

        select.callback = select_callback
        await interaction.response.send_message("選擇要修改的項目:", view=discord.ui.View(timeout=None).add_item(select), ephemeral=True)

    @discord.ui.button(label="改狀態", style=discord.ButtonStyle.blurple)
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message("🚫 只有開發者可以使用", ephemeral=True)
            return

        await interaction.response.send_message("請輸入狀態 (online / idle / dnd / invisible):", ephemeral=True)
        try:
            msg = await bot.wait_for("message", check=lambda m: m.author.id in DEV_IDS, timeout=30)
            status_map = {"online": discord.Status.online, "idle": discord.Status.idle,
                          "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
            await bot.change_presence(status=status_map.get(msg.content.lower(), discord.Status.online))
            await interaction.followup.send(f"✅ 狀態已改為 {msg.content.lower()}", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ 時間到，操作取消", ephemeral=True)

    
    @discord.ui.button(label="系統資訊", style=discord.ButtonStyle.blurple)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message("🚫 只有開發者可以使用", ephemeral=True)
            return
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        await interaction.response.send_message(f"🖥️ CPU: {cpu}%\n💾 RAM: {ram}%\n📂 磁碟: {disk}%", ephemeral=True)

    @discord.ui.button(label="關機", style=discord.ButtonStyle.red)
    async def shutdown_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message("🚫 只有開發者可以使用", ephemeral=True)
            return
        await interaction.response.send_message("⚠️ BOT 即將關機...", ephemeral=True)
        await bot.close()

    @discord.ui.button(label="重啟", style=discord.ButtonStyle.red)
    async def restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in DEV_IDS:
            await interaction.response.send_message("🚫 只有開發者可以使用", ephemeral=True)
            return
        await interaction.response.send_message("🔄 BOT 即將重啟...", ephemeral=True)
        os.execv(sys.executable, ['python3'] + sys.argv)
        
@bot.tree.command(name="洋蔥日誌", description="查看洋蔥系列指令使用記錄（限開發者）")
async def onion_log(interaction: discord.Interaction):
    if interaction.user.id not in DEV_IDS:
        await interaction.response.send_message("🚫 只有開發者可以使用", ephemeral=True)
        return

    data = load_json(LOG_FILE)
    if not data:
        await interaction.response.send_message("目前沒有記錄。", ephemeral=True)
        return

    # 依時間排序（最新在前）
    entries = sorted(data.items(), key=lambda kv: int(kv[0]), reverse=True)[:10]

    embed = Embed(
        title="📜 最新使用記錄",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )

    for idx, (key, value) in enumerate(entries, start=1):
        embed.add_field(
            name=f"{idx}. {value['command']}",
            value=f"👤 使用者: {value['user']}\n"
                  f"🆔 ID: {value['id']}\n"
                  f"🕒 時間: {value['time']}\n"
                  f"🏠 伺服器: {value['guild']}",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command()
@commands.check(is_dev)
async def onion(ctx):
    view = DevPanel()
    embed = discord.Embed(title="🧅 洋蔥開發者面板", description="點擊下方按鈕操作", color=discord.Color.purple())
    await ctx.send(embed=embed, view=view)
    

@bot.tree.context_menu(name="Delete Message")
async def delete_message(interaction: discord.Interaction, message: discord.Message):
    if interaction.user.id == DEVELOPER_ID:
        await message.delete()
        await interaction.response.send_message("✅ 訊息已刪除", ephemeral=True)
    else:
        await interaction.response.send_message("❌ 你沒有權限刪除訊息", ephemeral=True)


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


if __name__ == "__main__":
    bot.run(TOKEN)
