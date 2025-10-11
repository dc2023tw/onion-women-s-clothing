import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import json

TOKEN = 'TOKEN'
GUILD_ID = None
LOG_CHANNEL_ID = '頻道ID'

IMAGE_FOLDER = "images"
MESSAGE_COOLDOWN = 5      
DELETE_DELAY = 180        
USAGE_FILE = "usage_log.json"


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)



def load_usage_data():
    if not os.path.exists(USAGE_FILE):
        return {}
    with open(USAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_usage_data(data):
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



def get_images():
    valid_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    return [
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if os.path.splitext(f)[1].lower() in valid_extensions
    ]



@bot.tree.command(name="洋蔥女裝", description="送你洋蔥女裝圖片")
@app_commands.checks.cooldown(1, 5)
async def onion_cosplay(interaction: discord.Interaction):

    images = get_images()
    if not images:
        await interaction.response.send_message("資料夾裡沒有圖片！")
        return

    selected_image = random.choice(images)

    user_id_str = str(interaction.user.id)
    
    data = load_usage_data()
    if user_id_str not in data:
        data[user_id_str] = {"name": interaction.user.name, "count": 0}
    data[user_id_str]["count"] += 1
    save_usage_data(data)

    
    # await interaction.response.defer()
    await interaction.response.send_message(file=discord.File(selected_image), delete_after=DELETE_DELAY)


    guild_name = interaction.guild.name if interaction.guild else "私人訊息"
    embed = discord.Embed(
        title="🧅 洋蔥女裝使用紀錄",
        description=f"**{interaction.user.mention}** 使用了 `/洋蔥女裝`",
        color=discord.Color.green()
    )
    embed.add_field(name="使用次數", value=f"{data[user_id_str]['count']} 次", inline=True)
    embed.add_field(name="來源", value=guild_name, inline=True)
    embed.add_field(name="使用者ID", value=user_id_str, inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"圖片檔案：{os.path.basename(selected_image)}")

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)


@onion_cosplay.error
async def onion_cosplay_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
                f"⏳ 冷卻中！請 {error.retry_after:.1f} 秒後再試。",
                ephemeral=True
        )
    else:
        return

@bot.event
async def on_guild_join(guild: discord.Guild):
    embed = discord.Embed(
        title="💠 感謝邀請我進入伺服器！",
        description=(
            f"嗨！我是 **{bot.user.name}** 🤖\n"
            "以下是我的基本資訊與使用方式：\n\n"
            "📜 **功能簡介**\n"
            "・輸入 `/洋蔥女裝` 來獲取一張洋蔥女裝圖片 💃\n\n"
            "🛠️ **管理員提示**\n"
            "・可設定頻道權限避免洗版\n\n"
            "🖥️ **開發者**：[DEV]"
        ),
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text=f"伺服器：{guild.name}")

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(embed=embed)
            break

@bot.event
async def on_ready():
    print(f"✅ 已登入為 {bot.user}")
    try:
        if GUILD_ID:
            await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        else:
            await bot.tree.sync()
        print("✅ Slash 指令同步完成！")
    except Exception as e:
        print(f"❌ 指令同步失敗: {e}")


bot.run(TOKEN)
