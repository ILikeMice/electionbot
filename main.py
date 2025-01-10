import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import dotenv
import math

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
        data[uid] = {"votes": 0, "voted": False}
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

@bot.tree.command(name="setprofile")
async def setprofile(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    register(uid)
    await interaction.response.send_modal(profilemodal())

@bot.tree.command(name="list", description="List all current participants!")
async def list(interaction: discord.Interaction, page:int = 1):
    data = readdata()
    del data["voteable"]
    print(data.items())
    sorteddata = sorted(data.items(), key=lambda x: x[1]["votes"], reverse=True)
    pageamnt = math.ceil(len(sorteddata)/10)


    if page > pageamnt:
        return await interaction.response.send_message(f"Please enter a lower page number! Maximum is {pageamnt}")
    
    description = ""

    start = 1 + (page-1)*10
    if len(sorteddata) >= 10+(page-1)*10:
        end = 10+(page-1)*10
    else:
        end = len(sorteddata)

    for i in range(start-1,end):
        description += f"**{i+1}.** <@{sorteddata[i][0]}>, {sorteddata[i][1]["votes"]} vote(s) \n"


    leadembed = discord.Embed(title="Current Participants", description=description)
    await interaction.response.send_message(embed=leadembed)

def has_role(roleid: int):
    async def predicate(interaction: discord.Interaction):
        role = discord.utils.get(interaction.user.roles, id=roleid)
        if role is None:
            await interaction.response.send_message("nuh uh")
            return False
        return True
    return app_commands.check(predicate)

class electionview(discord.ui.View):
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirmbtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = readdata()
        data["voteable"] = False
        for i in data:
            if i != "voteable":
                data[i]["votes"] = 0
        writedata(data)
        await bot.get_channel(config["channel_id"]).send(f"New Election started by <@{interaction.user.id}>!")

    

@bot.tree.command(name="election", description="Control elections! (Admin only!)") # only id in config json allowed
@has_role(config["role_id"])
async def election(interaction: discord.Interaction, function: str):
        
        match function:

            case "create":
                print()
                await interaction.response.send_message(content="Are you sure? This will delete all ongoing elections and zero everyones' votes.", view=electionview(), ephemeral=True)

            case "end":
                print()
                data = readdata() 
                data["voteable"] = False
                writedata(data)
                del data["voteable"]
                print(data.items())
                await bot.get_channel(config["channel_id"]).send(f"Election ended! <@{sorted(data.items(), key=lambda x: x[1]["votes"], reverse=True)[0][0]}> Won!")
            
            case "open":
                data = readdata()
                data["voteable"]  = True
                writedata(data)
                await bot.get_channel(config["channel_id"]).send("Election is now open!")
     

@bot.tree.command(name="vote", description="Vote for someone")
async def vote(interaction: discord.Interaction, user: discord.User):
    data = readdata()
    if data["voteable"] == False:
        return await interaction.response.send_message("You can't vote yet! Please wait for the election to be opened!", ephemeral=True)
    
    if data[str(interaction.user.id)]["voted"] == True:
        return await interaction.response.send_message("You've already voted!", ephemeral=True)

    user2id = str(user.id)

    data[user2id]["votes"] += 1
    data[str(interaction.user.id)]["voted"] = True

    writedata(data)

    await interaction.response.send_message(f"Voted for <@{user2id}>!")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

bot.run(BOT_TOKEN)