import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import dotenv

dotenv.load_dotenv()

BOT_TOKEN = str(os.environ.get("BOT_TOKEN"))

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())



with open("config.json", "r") as infile:
    config =  json.load(infile) or {}

def readdata():
    with open("data.json", "r") as infile:
        data = json.load(infile)
    return data

def writedata(data):
    with open("data.json", "w") as outfile:
        json.dump(data, outfile, indent=4)

def register(uid):
    uid = str(uid)
    data = readdata()
    if uid not in data:
        data[uid]["profile"] = {
            "aboutme": "",
            "reason": "",
            "slogan": "",
            "age": ""
        }
        writedata(data)

@bot.tree.command(name="profile", description="View your profile")
async def profile(interaction: discord.Interaction, user: discord.user):
    uid = str(user.id) or str(interaction.user.id)
    register(uid)
    data = readdata()
    embed = discord.Embed()

    aboutme = data[uid]["profile"]["aboutme"]
    reason = data[uid]["profile"]["reason"]
    slogan = data[uid]["profile"]["slogan"]
    age = data[uid]["profile"]["slogan"]

    embed.add_field(name="About me", value=aboutme)
    embed.add_field(name="Why you should vote for me", value=reason)
    embed.add_field(name="Slogan", value=slogan)
    embed.add_field(name="Age", value=age)

    await interaction.response.send_message(embed=embed)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

bot.run(BOT_TOKEN)