import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!',intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} 成功連結至伺服器")

@bot.event
async def on_member_join(member):
    await member.send(f"歡迎 {member.name}")

bot.run(token, log_formatter=handler, log_level=logging.DEBUG)
