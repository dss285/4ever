import asyncio
import discord
from forever.CrissCross import CrissCross as CC
from forever.Utilities import Args
from forever.Newswire import NewswireMessage, Newswire
from models.Commands import Commands, Command
from models.EmbedTemplate import EmbedTemplate
import re

class ForeverCommands(Commands):
    def __init__(self, module_name, description, command_key, client, database, newswire):
        self.client = client
        self.database = database
        self.newswire = newswire
        command_list = self.fetch_commands(command_key)
        super().__init__(module_name, command_list, description, command_key)

    def fetch_commands(self, command_key):
        command_list = {}
        command_list["crisscross"] = CrissCross(command_key, self.client)
        command_list["gtanw"] = GTANewswire(command_key, self.database, self.newswire)
        return command_list
class CrissCross(Command):
    def __init__(self, command_key, client):
        self.client = client
        super().__init__(command_key, "crisscross", """Start a game of crisscross""", f"{command_key} crisscross *<challenged user>*", [])
        self.args = Args(mention=Args.MENTION_ARG, size=Args.OPTIONAL_INT_ARG)
        self.args.set_pattern(command_key, self.aliases)
    async def run(self, message, server):
        pattern = re.escape(self.prefix)+"\s("+"|".join(self.aliases)+")\s(?:<@!?(?:\d+)>)\s?(\d{1,2})?"
        parse = self.args.parse(message.content)
        if parse:
            if len(message.mentions) == 1:
                user = message.mentions[0]
                await message.channel.send("Would you like to accept this challenge ? (y) for yes, and anything to reject")
                response = await self.client.wait_for('message', timeout=30.0, check=lambda x: x.author == user and x.channel == message.channel)
                if "y" in response.content.lower():
                    size = int(parse.get("size")) or 3
                    game = CC(message.author, response.author, self.client, size)
                    await game.StartGame(message.channel)
                else:
                    await message.channel.send("Challenge denied.")
            else:
                await message.channel.send("Only 1 user may be challenged at once.")
class GTANewswire(Command):
    def __init__(self, command_key, database, newswire):
        self.database = database
        self.newswire = newswire
        super().__init__(command_key, "gtanw", """GTA V newswire""", f"{command_key} gtanw", [])
        self.args = Args(message=Args.OPTIONAL_STRING_ARG)
        self.args.set_pattern(command_key, self.aliases)
    async def run(self, message, server):
        parse = self.args.parse(message.content)
        if parse:
            if parse.get("message") == "message":
                em = EmbedTemplate(title="GTANW Message", description="Updating soon..")
                msg = await message.channel.send(embed=em)
                nwmessage = NewswireMessage(msg)
                await self.database.create_updated_message(msg.guild.id, "gtanw", msg.channel.id, msg.id)
                server.updated_messages["name"]["gtanw"] = nwmessage
                server.updated_messages["id"][nwmessage.id] = nwmessage
            else:
                x = 5
                posts = await self.newswire.getEmbeds(x)
                for i in posts:
                    await message.channel.send(embed=i)
                    x+=1
class RemindMe(Command):
    def __init__(self, command_key, client):
        self.client = client
        super().__init__(command_key, "remindme", """Remind me""", f"{command_key} *remindme* *<minutes>* *<name>*")
    async def run(self, message, server):
        pass