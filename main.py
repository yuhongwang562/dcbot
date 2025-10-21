import asyncio
import discord
from discord.ext import commands
import yt_dlp
import logging
from dotenv import load_dotenv
import os

import random
import re

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
FFMPEG_PATH = os.getenv('FFMPEG_PATH')

if not os.path.exists(FFMPEG_PATH):
    print("請確認 ffmpeg.exe 路徑是否正確")
    exit(1)

yt_dlp.utils.BUG_REPORT_URL = None
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

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

badword = re.compile(
    r"(?:\bfuck\b|\bshit\b|\bass\b|幹|靠)",
    re.IGNORECASE)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    content = message.content.lower()

    if badword.search(content):
        try:
            await message.delete()
        except Exception:
            pass
        await message.channel.send(f"{message.author.mention} - 請文明發言")
        return
    
    ch_helloword = ["嗨","哈囉"]
    en_helloword = ["hello","hi","Ciallo～(∠・ω< )⌒☆"]

    ch_replypool = ["嗨","哈囉"]
    en_replypool = ["hello","hi","Ciallo～(∠・ω< )⌒☆"]

    if any(w in content for w in ch_helloword):
        await message.channel.send(random.choice(ch_replypool))
    if any(w in content for w in en_helloword):
        await message.channel.send(random.choice(en_replypool))

    await bot.process_commands(message)

roleemoji = {
    "🐒":1419980875264823306,
    "🐂":1419981658718994442,
}

reaction_role_message_ids = set()

@bot.command()
async def roles(ctx):
    msg = await ctx.send(
        "請按表情領取身分組:\n"
        "🐒 AAA\n"
        "🐂 BBB\n"
    )
    reaction_role_message_ids.add(msg.id)
    for emoji in roleemoji.keys():
        await msg.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return    
    if payload.message_id not in reaction_role_message_ids:
        return
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    try:
        member = await guild.fetch_member(payload.user_id)
    except Exception:
        return
    
    emoji = str(payload.emoji)
    role_id = roleemoji.get(emoji)
    if not role_id:
        return
    
    role = guild.get_role(role_id)
    if role:
        try:
            await member.add_roles(role, reason="身分組領取")
            try:
                user = await bot.fetch_user(payload.user_id)
                await user.send(f"已為 {user.mention} 賦予 **{role.name}** 身分組")
                
            except Exception:
                pass
        except Exception as e:
            print("add_roles 失敗:", e)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return    
    if payload.message_id not in reaction_role_message_ids:
        return
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    try:
        member = await guild.fetch_member(payload.user_id)
    except Exception:
        return
    
    emoji = str(payload.emoji)
    role_id = roleemoji.get(emoji)
    if not role_id:
        return
    
    role = guild.get_role(role_id)
    if role:
        try:
            await member.remove_roles(role, reason="身分組移除")
            try:
                user = await bot.fetch_user(payload.user_id)
                await user.send(f"已為 {user.mention} 移除 **{role.name}** 身分組")
                
            except Exception:
                pass
        except Exception as e:
            print("add_roles 失敗:", e)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        ffmpeg_opts = {
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }

        source = discord.FFmpegPCMAudio(filename, **ffmpeg_opts, executable=FFMPEG_PATH)
        return cls(source, data=data)

    @bot.command()
    async def play(ctx, *, url):
        if not ctx.message.author.voice:
            await ctx.send("你不在語音頻道")
            return

        target_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        try:
            if voice_client is None:
                await ctx.send(f"正在連接至語音頻道: {target_channel}")
                voice_client = await target_channel.connect(timeout=60)
            elif voice_client.channel != target_channel:
                await ctx.send(f"正在切換至語音頻道: {target_channel}")
                await voice_client.move_to(target_channel)
        except discord.errors.ClientException as e:
            await ctx.send(f"連線錯誤: {str(e)}")
            return
        except asyncio.TimeoutError:
            await ctx.send("連接語音頻道逾時")
            return
        except Exception as e:
            await ctx.send(f"連線錯誤: {str(e)}")
            return

        try:
            await ctx.send("正在搜尋或載入:'{url}'")
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            voice_client.play(player, after=lambda e: print(f'播放錯誤: {e}') if e else None)
            await ctx.send(f"正在播放: {player.title}")
        except yt_dlp.utils.DownloadError as e:
            await ctx.send(f"找不到該影片或URL失效: {str(e)}")
            if voice_client:
                await voice_client.disconnect()
        except Exception as e:
            await ctx.send(f"播放錯誤: {str(e)}")
            if voice_client:
                await voice_client.disconnect()

    @bot.command(name='stop', aliases=['s'])
    async def stop(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("已停止播放並離開語音頻道")
        elif ctx.voice_client:
            await ctx.send("沒有正在播放的音樂")
        else:
            await ctx.send("我目前沒有連線到任何語音頻道")

    @bot.command(name='leave', aliases=['l', 'dc'])
    async def leave(ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("已離開語音頻道")
        else:
            await ctx.send("我目前沒有連線到任何語音頻道")      
bot.run(token)
