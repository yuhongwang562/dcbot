import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

import random
import re

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

bot.run(token, log_formatter=handler, log_level=logging.DEBUG)
