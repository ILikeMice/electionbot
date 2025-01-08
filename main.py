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
        data[uid] = {}
        data[uid]["profile"] = {
            "aboutme": "",
            "reason": "",
            "age": ""
        }
        writedata(data)

@bot.tree.command(name="profile", description="View your profile")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    try:
        uid = str(user.id)
    except:
        uid = str(interaction.user.id)
    register(uid)
    data = readdata()
    embed = discord.Embed()

    aboutme = data[uid]["profile"]["aboutme"]
    reason = data[uid]["profile"]["reason"]
    age = data[uid]["profile"]["age"]

    embed.add_field(name="Name", value=interaction.user.name)
    embed.add_field(name="Age", value=age)
    embed.add_field(name="About me", value=aboutme)
    embed.add_field(name="Why you should vote for me", value=reason)

    embed.set_thumbnail(url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

class profilemodal(discord.ui.Modal, title="Profile"):
    age = discord.ui.TextInput(
        label="Age",
        placeholder="Your Age here...",
        required=False,
        max_length=2
    )
    aboutme = discord.ui.TextInput(
        label="About Me",
        style=discord.TextStyle.long,
        placeholder="Short Introduction of yourself...",
        required=True,
        min_length=40,
        max_length=120    
    )
    reason = discord.ui.TextInput(
        label="Why should you be voted?",
        style=discord.TextStyle.long,
        placeholder="Why should people vote for you?",
        required=True,
        min_length=50,
        max_length=200    
    )

    async def on_submit(self, interaction: discord.Interaction):
        data = readdata()
        uid = str(interaction.user.id)
        print(self.age.value, self.aboutme.value, self.reason.value)
        data[uid]["profile"]["age"] = self.age.value.strip()
        data[uid]["profile"]["aboutme"] = self.aboutme.value.strip()
        data[uid]["profile"]["reason"] = self.reason.value.strip()

        writedata(data)
        await interaction.response.send_message("Profile Saved!", ephemeral=True)

@bot.tree.command(name="list", description="List all current participants!")
async def list(interaction: discord.Interaction, page:int = 1):
    data = readdata()
    print(data.items())

@bot.tree.command(name="setprofile")
async def setprofile(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    register(uid)
    await interaction.response.send_modal(profilemodal())


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

bot.run(BOT_TOKEN)