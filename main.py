import nextcord
from nextcord.ext import commands
import github
import github.Repository
import pip_api._parse_requirements as pip
from cryptography.fernet import Fernet
import json
from requests import get
client = commands.Bot(command_prefix="git ")

@client.command()
async def init(ctx):
    
    await ctx.author.send("Please enter your GitHub Auth Key or type `auth cancel` to cancel.\n\n")
    await ctx.author.send("Please also consider Reading `gh privacy` and reassure yourself that we're using the right things `gh me`")
    await ctx.author.send("Also know that you can always delete this key using `gh init keyremove`. All of your Data will be eradicated from the Database.")
    message = await client.wait_for("MESSAGE",check=lambda m: m.author == ctx.author and isinstance(m.channel,nextcord.DMChannel))
    if message.content == "auth cancel":
        return await ctx.author.send("Cancelled!")
    frnt = Fernet(open("key.key",'rb').read())
    with open("config.json","r") as f:
        config = json.load(f)
    config[str(ctx.author.id)] = frnt.encrypt(message.content.encode("utf-8")).decode("utf-8")
    with open("config.json","w") as f:
        json.dump(config,f)
    git = github.Github(message.content)
    user = git.get_user()
    await ctx.send(f'Logged in as {git.get_user().name}')


class PushAgain(nextcord.ui.View):
    def __init__(self,repo:github.Repository.Repository,requirements):
        super().__init__(timeout=180)
        self.value = None
        self.reqs = requirements
        self.repo = repo

    @nextcord.ui.button(label="Update",style=nextcord.ButtonStyle.green)
    async def push(self,button,interaction:nextcord.Interaction):
        
        fernet = Fernet(open("key.key",'rb').read())
        with open("config.json","r") as f:
            config = json.load(f)
        if not str(interaction.user.id) in config:
            return await interaction.response.send_message(":x: You have to sync your Profile to a GitHub account: `git init`")
        git = github.Github(fernet.decrypt(config[str(interaction.user.id)].encode()).decode('utf-8'))
        sha = self.repo.get_contents("requirements.txt").sha
        self.repo.update_file("requirements.txt","[DependoCat] Update Requirements",self.reqs, sha)
        await interaction.response.send_message(":white_check_mark: Dependencies were updated!")
        self.stop()

class Confirm(nextcord.ui.View):
    def __init__(self,repo:github.Repository.Repository,requirements):
        super().__init__(timeout=180)
        self.value = None
        self.reqs = requirements
        self.repo = repo

    @nextcord.ui.button(label="Push",style=nextcord.ButtonStyle.green)
    async def push(self,button,interaction:nextcord.Interaction):
        
        fernet = Fernet(open("key.key",'rb').read())
        with open("config.json","r") as f:
            config = json.load(f)
        if not str(interaction.user.id) in config:
            return await interaction.response.send_message(":x: You have to sync your Profile to a GitHub account: `git init`")
        git = github.Github(fernet.decrypt(config[str(interaction.user.id)].encode()).decode('utf-8'))
        sha = self.repo.get_contents("requirements.txt").sha
        self.repo.update_file("requirements.txt","[DependaCord] Update Requirements",self.reqs, sha)
        await interaction.response.send_message(":white_check_mark: Dependencies were updated!")
        self.stop()
        
    @nextcord.ui.button(label="Cancel",style=nextcord.ButtonStyle.danger)
    async def cancel(self,button,interaction:nextcord.Interaction):
        await interaction.response.send_message(":white_check_mark: Dependency Bumo cancelled!")
        self.stop()


class MkReqs(nextcord.ui.View):
    def __init__(self,repo:github.Repository.Repository,requirements):
        super().__init__(timeout=180)
        self.value = None
        self.reqs = requirements
        self.repo = repo

    @nextcord.ui.button(label="Create Requirements",style=nextcord.ButtonStyle.green)
    async def push(self,button,interaction:nextcord.Interaction):
        
        fernet = Fernet(open("key.key",'rb').read())
        with open("config.json","r") as f:
            config = json.load(f)
        git = github.Github(fernet.decrypt(config[str(interaction.user.id)].encode()).decode('utf-8'))
        file = self.repo.get_contents("requirements.txt")
        if file:
            sha = file.sha  
        if not str(interaction.user.id) in config:
            return await interaction.response.send_message(":x: You have to sync your Profile to a GitHub account: `git init`")
        git = github.Github(fernet.decrypt(config[str(interaction.user.id)].encode()).decode('utf-8'))
        self.reqs = await self.getreqs(interaction)
        print(self.reqs)
        if file:
            self.repo.update_file("requirements.txt","[DependaCord] Create Requirements","\n".join(self.reqs.split("|")),sha)
        else:
            self.repo.create_file("requirements.txt","[DependaCord] Create Requirements","\n".join(self.reqs.split("|")))

        await interaction.response.send_message(":white_check_mark: Dependencies were updated!")
        self.stop()

    async def getreqs(self,interaction):
        await interaction.channel.send("Please send all Requirements, seperated by a `|`")
        msg = await client.wait_for("message",check=lambda m:m.channel.id == interaction.channel_id and m.author==interaction.user)
        return msg.content

    @nextcord.ui.button(label="Cancel",style=nextcord.ButtonStyle.danger)
    async def cancel(self,button,interaction:nextcord.Interaction):
        await interaction.response.send_message(":white_check_mark: requirements-file creation cancelled!")
        self.stop()

@client.command()
async def update(ctx,repo,c_path="requirements.txt"):
  async with ctx.channel.typing():
    fernet = Fernet(open("key.key",'rb').read())
    with open("config.json","r") as f:
        config = json.load(f)
    if not str(ctx.author.id) in config:
        return await ctx.send(":x: You have to sync your Profile to a GitHub account: `git init`")
    git = github.Github(fernet.decrypt(config[str(ctx.author.id)].encode()).decode('utf-8'))
    _repo = git.get_repo(repo)
    print(_repo.full_name)
    r = get(f'https://raw.githubusercontent.com/{_repo.full_name}/main/{c_path}')
    datas = r.text
    print(datas)
    res = ""
    if not datas or r.status_code>399:
        v = MkReqs(_repo,"")
        await ctx.send("No Dependency file (*requirements.txt*) was set!",view=v)
        await v.wait()
        return
    print("lul")
    for d in datas.split("\n"):
        if "==" in d:
            dtype, dversion = d.split("==")
            try:
                js = get(f"https://pypi.org/pypi/{dtype}/json").json()
                latest = list(js["releases"].keys())[-1]
                if dversion == latest:
                    res += d+"\n"
                else:
                    res += dtype+"=="+latest+"\n"
            except:
                return await ctx.send("No Dependencies to set or update!")
        else:
            try:
                dtype = d
                js = get(f"https://pypi.org/pypi/{dtype}/json").json()
                latest = list(js["releases"].keys())[-1]
                res += dtype+"=="+latest+"\n"
            except:
                return await ctx.send("No Dependencies to set or update!")
        
    embed = nextcord.Embed(title="Compare Changes")
    embed.add_field(name="Old Requirements",value=f"```\n{datas}```")
    embed.add_field(name="New Requirements",value=f"```\n{res}```")
    v = Confirm(_repo,res)
    await ctx.send(embed=embed,view=v)
    await v.wait()


@client.command()
async def update_by_url(ctx,c_path="requirements.txt"):
  async with ctx.channel.typing():
    fernet = Fernet(open("key.key",'rb').read())
    with open("config.json","r") as f:
        config = json.load(f)
    r = get(c_path)
    datas = r.text
    print(datas)
    res = ""
    if not datas or r.status_code>399:
        return await ctx.send("No Dependency file (*requirements.txt*) was set!")
    for d in datas.split("\n"):
        if "==" in d:
            dtype, dversion = d.split("==")
            try:
                js = get(f"https://pypi.org/pypi/{dtype}/json").json()
                latest = list(js["releases"].keys())[-1]
                if dversion == latest:
                    res += d+"\n"
                else:
                    res += dtype+"=="+latest+"\n"
            except Exception as error:
                
                res += dtype+"\n"
                await ctx.send(f"(Skipping) Skipping {d} due to already latest Version")
        else:
            try:
                dtype = d
                js = get(f"https://pypi.org/pypi/{dtype}/json").json()
                latest = list(js["releases"].keys())[-1]
                res += dtype+"=="+latest+"\n"
            except Exception as error:
                # print(error)
                res += dtype+"\n"
                await ctx.send(f"(Skipping) Skipping {d} due to already latest Version")
        
    embed = nextcord.Embed(title="Compare Changes")
    embed.add_field(name="Old Requirements",value=f"```\n{datas}```")
    embed.add_field(name="New Requirements",value=f"```\n{res}```")
    await ctx.send(embed=embed)

@client.command()
async def check(ctx,repo,c_path="requirements.txt"):
  async with ctx.channel.typing():
    fernet = Fernet(open("key.key",'rb').read())
    with open("config.json","r") as f:
        config = json.load(f)
    if not str(ctx.author.id) in config:
        return await ctx.send(":x: You have to sync your Profile to a GitHub account: `git init`")
    git = github.Github(fernet.decrypt(config[str(ctx.author.id)].encode()).decode('utf-8'))
    _repo = git.get_repo(repo)
    r = get(f'https://raw.githubusercontent.com/{_repo.full_name}/main/{c_path}')
    datas = r.text
    print(datas)
    res = ""
    if not datas or r.status_code>399:
        v = MkReqs(_repo,"")
        await ctx.send("No Dependency file (*requirements.txt*) was set!",view=v)
        await v.wait()
        return
    for d in datas.split("\n"):
        if "==" in d:
            dtype, dversion = d.split("==")
            print(dtype)
            print(dversion)
            try:
                js = get(f"https://pypi.org/pypi/{dtype}/json").json()
                latest = list(js["releases"].keys())[-1]
                if dversion == latest:
                    res += d+"\n"
                else:
                    res += dtype+"=="+latest+"\n"
            except Exception as error:
                print(error)
                await ctx.send(f"(Skipping) Skipping {d} due to already latest Version") # Usually errors get thrown because we're already on the latest Version
        else:
            try:
                dtype = d
                js = get(f"https://pypi.org/pypi/{dtype}/json").json()
                latest = list(js["releases"].keys())[-1]
                res += dtype+"=="+latest+"\n"
            except Exception as error:
                print(error)
                await ctx.send(f"(Skipping) Skipping {d} due to already latest Version")

        
    embed = nextcord.Embed()
    embed.add_field(name="Current Requirements",value=f"```\n{datas}```")
    if res != datas:
        view = PushAgain(_repo,res)
    else:
        view = None
    await ctx.send(embed=embed,view=view)
    if view:
        await view.wait()


client.run("Token")
