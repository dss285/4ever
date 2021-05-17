import pymysql.cursors
import discord
from models.BotMention import BotMention

from warframe.CetusMessage import CetusMessage
from warframe.FissureMessage import FissureMessage
from warframe.SortieMessage import SortieMessage
from warframe.NightwaveMessage import NightwaveMessage
from warframe.InvasionMessage import InvasionMessage
from forever.NewswireMessage import NewswireMessage

from warframe.SolNode import SolNode
from warframe.SolPlanet import SolPlanet
from forever.Server import Server
from gfl.Doll import Doll
class Database:
    def __init__(self, host, user, password, database):
        self.runtime = {}
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.tables = [
            "discord_images",
            "discord_server",
            "discord_notifications",
            "discord_joinable_roles",
            "discord_role_messages",
            "discord_updated_messages",
            "gfl_dolls",
            "gfl_equipment",
            "wf_builds",
            "wf_builds_images",
            "wf_items",
            "wf_missions",
            "wf_nightwave",
            "wf_solsystem_nodes",
            "wf_solsystem_planets",
            "wf_sorties",
            "news"
        ]
        self.mentions = []

        
        self.connection = pymysql.connect(host=self.host,
                                          user=self.user,
                                          password=self.password,
                                          db=self.database,
                                          cursorclass=pymysql.cursors.DictCursor)
    def object_query(self, object_in):
        self.connection.ping(reconnect=True)
        with self.connection.cursor() as cursor:
            cursor.execute(object_in.sql())
        self.connection.commit()
    def query(self, sql):
        self.connection.ping(reconnect=True)
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
        self.connection.commit()
    def getData(self,):
        self.connection.ping(reconnect=True)
        results = {}
        for i in self.tables:
            results[i] = self.getTableRows(i)
        return results
    def getTableRows(self, tabletype):
        results = None
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM {}".format(tabletype))
            results = cursor.fetchall()
        self.connection.commit()
        return results
    def structure(self,):
        self.runtime["warframe"] = {}
        self.runtime["warframe"]["nightwave"] = []
        self.runtime["warframe"]["invasions"] = []
        self.runtime["warframe"]["sorties"] = None
        self.runtime["warframe"]["translate"] = {}
        self.runtime["warframe"]["translate"]["missions"] = {}
        self.runtime["warframe"]["translate"]["nightwave"] = {}
        self.runtime["warframe"]["translate"]["sorties"] = {}
        self.runtime["warframe"]["translate"]["items"] = {}
        self.runtime["warframe"]["translate"]["solsystem"] = {}
        self.runtime["warframe"]["translate"]["solsystem"]["planets"] = []
        self.runtime["warframe"]["translate"]["solsystem"]["nodes"] = []
        

        self.runtime["gfl"] = {}
        self.runtime["gfl"]["dolls"] = []
        self.runtime["gfl"]["equipment"] = []

        self.runtime["servers"] = {}
        self.connection.ping(reconnect=True)
    async def getServer(self, server_id, data, client):
        log_id = next((i["logchannel_id"] for i in data["discord_server"] if i["server_id"] == server_id), None)
        discord_server = client.get_guild(server_id)
        logchannel = client.get_channel(log_id) if log_id else None
        updated_messages = {}
        joinable_roles = set()
        role_messages = {}
        notifications = []
        for x in data["discord_role_messages"]:
            if x["server_id"] == server_id:
                channel = client.get_channel(x["channel_id"])
                message = None
                try:
                    message = await channel.fetch_message(x["message_id"])
                except discord.NotFound:
                    self.query("DELETE FROM discord_updated_messages WHERE message_id={}".format(
                        x["message_id"]
                    ))
                    self.query("DELETE FROM discord_role_messages WHERE message_id={}".format(
                        x["message_id"]
                    ))
                    continue
                if message:
                    role_messages[message.id] = {
                        "message" : message,
                        "emoji" : x["emoji"],
                        "role_id" : x["role_id"] 
                    }
        for x in data["discord_joinable_roles"]:
            if x["server_id"] == server_id:
                role = discord_server.get_role(x["role_id"])
                if role:
                    joinable_roles.add(role)
                else:
                    sql = "DELETE FROM discord_joinable_roles WHERE role_id={}".format(x["role_id"])
                    self.query(sql)
        for x in data["discord_notifications"]:
            if x["server_id"] == server_id:
                role = discord_server.get_role(x["role_id"])
                if role:
                    bot_mention = BotMention(x["name"], role)
                    notifications.append(bot_mention)
                else:
                    sql = "DELETE FROM discord_notifications WHERE role_id={}".format(x["role_id"])
                    self.query(sql)
        if not updated_messages:
            for x in data["discord_updated_messages"]:
                if x["server_id"] == server_id:
                    channel = client.get_channel(x["channel_id"])
                    if channel:
                        message = None
                        try:
                            message = await channel.fetch_message(x["message_id"])
                        except discord.NotFound:
                            self.query("DELETE FROM discord_updated_messages WHERE message_id={}".format(
                                x["message_id"]
                            ))
                            self.query("DELETE FROM discord_role_messages WHERE message_id={}".format(
                                x["message_id"]
                            ))
                            message = None
                        if message:
                            message_type = x["message_type"]
                            if message_type == "nightwave":
                                updated_messages[message_type] = NightwaveMessage(message)
                            elif message_type == "invasions":
                                updated_messages[message_type] = InvasionMessage(message, [])
                            elif message_type == "fissures":
                                updated_messages[message_type] = FissureMessage(message, [])
                            elif message_type == "sorties":
                                updated_messages[message_type] = SortieMessage(message)
                            elif message_type == "poe":
                                mention = next((i for i in notifications if i.name == "poe_night"), None)
                                updated_messages[message_type] = CetusMessage(message, mention, client)
                            elif message_type == "gtanw":
                                updated_messages[message_type] = NewswireMessage(message)
        server = Server(server_id, discord_server, logchannel, updated_messages, notifications, joinable_roles, role_messages)
        self.runtime["servers"][server_id] = server
    async def update_runtime(self, client):
        data = self.getData()

        if "gfl" in self.runtime:
            self.gfl(data)
        if "warframe" in self.runtime:
            self.warframe(data)
    def gfl(self, data):
        self.runtime["gfl"]["dolls"].clear()
        self.runtime["gfl"]["equipment"].clear()
        for d in data["gfl_dolls"]:
            doll = Doll(d["id"], d["name"], 
            d["type"], 
            d["rarity"], 
            d["formation_bonus"], 
            d["formation_tiles"],
            d["skill"],
            d["aliases"].split("|") if d["aliases"] else [],
            d["productiontimer"])
            self.runtime["gfl"]["dolls"].append(doll)
    def warframe(self, data):
        self.runtime["warframe"]["translate"]["solsystem"]["planets"].clear()
        self.runtime["warframe"]["translate"]["solsystem"]["nodes"].clear()
        for item in data["wf_missions"]:
            self.runtime["warframe"]["translate"]["missions"][item["code_name"]]    = item["name"]
        for item in data["wf_nightwave"]:
            self.runtime["warframe"]["translate"]["nightwave"][item["code_name"]]   = item["name"]
        for item in data["wf_sorties"]:
            self.runtime["warframe"]["translate"]["sorties"][item["code_name"]]     = item["name"]
        for item in data["wf_items"]:
            self.runtime["warframe"]["translate"]["items"][item["code_name"]]       = item["name"]
        for item in data["wf_solsystem_planets"]:
            self.runtime["warframe"]["translate"]["solsystem"]["planets"].append(SolPlanet(item["planet_id"], item["name"]))
        for item in data["wf_solsystem_nodes"]:
            self.runtime["warframe"]["translate"]["solsystem"]["nodes"].append(SolNode(item["node_id"], item["name"],
            next(planet for planet in self.runtime["warframe"]["translate"]["solsystem"]["planets"] if planet.id == item["planet_id"])))
    async def initRuntime(self, client):
        self.structure()
        data = self.getData()
    #Server Translation
        for i in data["discord_server"]:
            await self.getServer(i["server_id"], data, client)
    #GFL Translation
        self.gfl(data)
    #WF Translation
        self.warframe(data)


if __name__ == "__main__":
    db = Database("localhost", "dss285", "aeon123", "aeon")