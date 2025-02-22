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

def readelections():
    with open("elections.json", "r") as infile:
        return json.load(infile)
    
def writeelections(elections):
    with open("elections.json", "w") as outfile:
        json.dump(elections, outfile, indent=4)

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
        data[uid] = {"votes": 0, "voted": [], "anonymous": False, "usersvoted": []}
        data[uid]["profile"] = {
            "aboutme": "",
            "reason": "",
            "age": ""
        }
        writedata(data)

@bot.tree.command(name="profile", description="View your or someone elses' profile")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    try:
        uid = str(user.id)
    except:
        uid = str(interaction.user.id)
    register(uid)
    data = readdata()
    embed = discord.Embed()
    userobj = await bot.fetch_user(uid)

    aboutme = data[uid]["profile"]["aboutme"]
    reason = data[uid]["profile"]["reason"]
    age = data[uid]["profile"]["age"]

    embed.add_field(name="Name", value= userobj.name)
    embed.add_field(name="Age", value=age)
    embed.add_field(name="About me", value=aboutme)
    embed.add_field(name="Why you should vote for me", value=reason)
    try:
        embed.set_thumbnail(url=userobj.avatar.url)
    except:
        return await interaction.response.send_message("Error! Is the target user a bot?", ephemeral=True)
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

@bot.tree.command(name="setprofile", description="Set your profile!")
async def setprofile(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    register(uid)
    await interaction.response.send_modal(profilemodal())

@bot.tree.command(name="list", description="List all current participants!")
async def list(interaction: discord.Interaction, page: int = 1):
    elections = readelections()
    current_election_id = str(len(elections) - 1)
    current_election = elections[current_election_id]

    if "voteable" in current_election:
        del current_election["voteable"]

    sorted_election = sorted(current_election.items(), key=lambda x: len(x[1]["usersvoted"]), reverse=True)
    pageamnt = math.ceil(len(sorted_election) / 10)

    if page > pageamnt:
        return await interaction.response.send_message(f"Please enter a lower page number! Maximum is {pageamnt}", ephemeral=True)

    description = ""

    start = 1 + (page - 1) * 10
    end = min(len(sorted_election), 10 + (page - 1) * 10)

    for i in range(start - 1, end):
        user_id = sorted_election[i][0]
        votes = len(sorted_election[i][1]["usersvoted"])
        description += f"**{i + 1}.** <@{user_id}>, {votes} vote(s) \n"

    leadembed = discord.Embed(title="Current Participants", description=description)
    await interaction.response.send_message(embed=leadembed, ephemeral=True)



def has_role(roleid: int):
    async def predicate(interaction: discord.Interaction):
        role = discord.utils.get(interaction.user.roles, id=roleid)
        if role is None:
            await interaction.response.send_message("You dont have the permission for that!")
            return False
        return True
    return app_commands.check(predicate)

class electionview(discord.ui.View):
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirmbtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = readdata()
        elections = readelections()

        for i in elections:
            elections[i]["voteable"] = False

        elections[len(elections.items())] = {"voteable": False}

        writeelections(elections)
        await interaction.response.send_message("Election made!", ephemeral=True)
        await bot.get_channel(config["results_channel_id"]).send(f"<@&{config["election_ping_role_id"]}>!  New Election created by <@{interaction.user.id}>!")

@bot.tree.command(name="election", description="Control elections! (Admin only!)") # only id in config.json allowed
@has_role(config["role_id"])
async def election(interaction: discord.Interaction, function: str):
        register(interaction.user.id)
        if function not in ["create", "end", "open"]:
            return await interaction.response.send_message('Unknown function! Please use "create", "open" or "end" ! create resets all the votes and makes a new election, end ends the current going election and announces the winner, open lets the users vote for others!', ephemeral=True)

        match function:
            case "create":
                print()
                await interaction.response.send_message(content="Are you sure? This will delete all ongoing elections and zero everyones' votes.", view=electionview(), ephemeral=True)

            case "end":
                print()
                data = readdata() 
                elections = readelections()

                elections[str(len(elections.items()) - 1)]["voteable"] = False

                writedata(data)
                writeelections(elections)
                
                print(data.items())

                await interaction.response.send_message("Ended!", ephemeral=True)
                await bot.get_channel(config["results_channel_id"]).send(f"Election ended! <@{sorted(data.items(), key=lambda x: x[1]["votes"], reverse=True)[0][0]}> Won!")
            
            case "open":
                data = readdata()
                elections = readelections()
                if elections[str(len(elections.items()) - 1)]["voteable"] == True:
                    return await interaction.response.send_message("Election already open!", ephemeral=True)
                elections[str(len(elections.items()) - 1)]["voteable"]  = True
                writedata(data)
                writeelections(elections)
                await interaction.response.send_message("Opened!", ephemeral=True)
                await bot.get_channel(config["results_channel_id"]).send(f"<@&{config["election_ping_role_id"]}>! Election is now open!")


@bot.tree.command(name="vote", description="Vote for someone")
async def vote(interaction: discord.Interaction, user: discord.User):
    register(interaction.user.id)
    data = readdata()
    elections = readelections()
    if elections[str(len(elections.items()) - 1)]["voteable"] == False:
        return await interaction.response.send_message("You can't vote yet! Please wait for the election to be opened!", ephemeral=True)
    
    if str(len(elections.items()) - 1) in data[str(interaction.user.id)]["voted"]:
        return await interaction.response.send_message("You've already voted in this election!", ephemeral=True)

    user2id = str(user.id)
    register(user2id)
    data = readdata()

    # uncomment the lines below if you want profile required, this was commented for testing 
    #if data[user2id]["profile"]["aboutme"] == "": 
    #    return await interaction.response.send_message("The participant needs to set their profile!", ephemeral=True)

    data[user2id]["votes"] += 1
    
    elections[str(len(elections.items()) - 1)][user2id] = {"usersvoted": []}
    elections[str(len(elections.items()) - 1)][user2id]["usersvoted"].append(f"{interaction.user.id} ({interaction.user.name})")
    
    data[str(interaction.user.id)]["voted"].append(str(len(elections.items()) - 1))

    writedata(data)
    writeelections(elections)

    if data[str(interaction.user.id)]["anonymous"] == False:
        await bot.get_channel(config["votes_channel_id"]).send(f"<@{interaction.user.id}> voted for <@{user2id}>!")
    else:
        await bot.get_channel(config["votes_channel_id"]).send(f"Anonymous vote for <@{user2id}>!")
    
    await interaction.response.send_message(f"Voted for <@{user2id}>!", ephemeral=True)

@bot.tree.command(name="help", description="List all the commands!")
async def help(interaction: discord.Interaction):
    helpembed = discord.Embed(title="Commands!")

    for i in bot.tree.get_commands():
        helpembed.add_field(name="/"+i.name, value=i.description)

    await interaction.response.send_message(embed=helpembed, ephemeral=True)

@bot.tree.command(name="anonymous", description="Toggle anonymous voting! (Off by default)")
async def anonymous(interaction: discord.Interaction):
    data = readdata()
    uid = str(interaction.user.id)
    if data[uid]["anonymous"] == True:
        data[uid]["anonymous"] = False
        await interaction.response.send_message("Anonymous voting turned off! Your vote is now public!", ephemeral=True)
    else:
        data[uid]["anonymous"] = True
        await interaction.response.send_message("Anonymous voting turned on! Nobody will be able to see your vote!", ephemeral=True)
    writedata(data)

@bot.tree.command(name="electionresults", description="View the results of any election by its ID!")
async def electionresults(interaction: discord.Interaction, electionid: int = -1):
    elections = readelections()

    if electionid > len(elections.items()) - 1:
        return await interaction.response.send_message("Invalid Election ID!", ephemeral=True)
    if electionid == -1:
        selectedid = str(len(elections.items()) - 1)
    else:
        selectedid = str(electionid)
    electionembed = discord.Embed(description="")


    electionembed.title = f"Election {selectedid} Results"
    uservotes = {}
    totalvotes = 0
    elections = readelections()

    for i in elections[selectedid].items():
        if i[0] != "voteable":
            uservotes[i[0]] = len(i[1]["usersvoted"])
            totalvotes += len(i[1]["usersvoted"])
            print(uservotes)
    sortedvotes = sorted(uservotes.items())
    print(sortedvotes)
    try:
        electionembed.description += f"**Winner:** <@{sortedvotes[0][0]}> with **{sortedvotes[0][1]}** vote(s) \n"
        electionembed.description += f"**Second Place:** <@{sortedvotes[1][0]}> with **{sortedvotes[1][1]}** vote(s) \n" or ""
        electionembed.description += f"Third Place: <@{sortedvotes[2][0]}> with **{sortedvotes[2][1]}** vote(s) \n" or ""
    except:
        pass
    electionembed.description += f"**Total votes:** {totalvotes}"
    
    await interaction.response.send_message(embed=electionembed, ephemeral=True)

@bot.tree.command(name="listelections", description="View all Elections and their status!")
async def listelections(interaction: discord.Interaction):
    elections = readelections()
    electionsembed = discord.Embed(title="Elections!", description="")

    for i in reversed(elections.items()) :
        electionsembed.description += f"**Election {i[0]}** - {"Open" if i[1]["voteable"] else "Closed/Ended"} \n"

    await interaction.response.send_message(embed=electionsembed, ephemeral=True)

@bot.tree.command(name="getallvotes", description="Get a list of votes for an Election!")
async def getallvotes(interaction: discord.Interaction, electionid: int):
    elections = readelections()
    res = {}
    for i in elections[str(electionid)].items():
        if i[0] != "voteable":
            resuser = str(i[0])
            try:
                resuser += bot.get_user(int(i[0])).name
            except: 
                pass
            res[resuser] = i[1]["usersvoted"]
    
    await interaction.response.send_message(f"```{res}```", ephemeral=True)


'''
More Features to add:
- List of who voted for who (together with election history, probably will have to give elections IDs, still, saving in json might be bad, so probaby save top 3 peoples list of votes)
- Election history (might be not that good to store the data on who voted for who for all past elections in a json)

'''

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

bot.run(BOT_TOKEN)