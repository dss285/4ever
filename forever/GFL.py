from models.EmbedTemplate import EmbedTemplate
import config
import datetime
class Doll:
    def __init__(self, doll_id, name, doll_type, rarity, formation_bonus, formation_tiles, skill, aliases, production_timer=None):
        self.doll_id = doll_id
        self.name = name
        self.doll_type = doll_type
        self.rarity = rarity
        self.formation_bonus = formation_bonus
        self.formation_tiles = formation_tiles
        self.skill = skill
        self.aliases = aliases
        self.production_timer = production_timer
    def getImagePath(self,):
        file_name = self.name.replace(" ", "_").replace("/","")
        return f"{config.asset_path}/images/gfl/dolls/128x167_{file_name}.png"
    def getEmbed(self,):
        em = EmbedTemplate(title=self.name)
        if self.production_timer:
            em.add_field(name="Production Time", value=f"{datetime.timedelta(seconds=self.production_timer)}", inline=False)
        
        em.add_field(name="Skill", value=self.skill if self.skill else "N/A")
        if self.formation_bonus and self.formation_tiles:
            formation_tiles = self.formation_tiles.replace("0", "⬛").replace("1", "⬜").replace("2", "🟦").replace("\\r\\n", "\r\n")
            formation_bonus = self.formation_bonus.replace("\\r\\n", "\r\n")
            em.add_field(
                name="Formation",
                value=f"{formation_tiles}\n\n{formation_bonus}",
                inline=False
            )
        return em
    def __repr__(self):
        return f'<GFL.Doll name={self.name}, id={self.doll_id}>'
class Fairy:
    def __init__(self, fairy_id, name, stats, skill, production_timer):
        self.fairy_id = fairy_id
        self.name = name
        self.stats = stats.split("|")
        self.skill = skill
        self.production_timer = production_timer
    def getEmbed(self,):
        em = EmbedTemplate(title=self.name)
        if self.production_timer:
            em.add_field(
                name="Production Time",
                value=f"{datetime.timedelta(seconds=self.production_timer)}",
                inline=False
            )
        if self.stats:
            em.add_field(name="Stats", value="\n".join(self.stats))
        em.add_field(name="Skill", value=self.skill if self.skill else "N/A")
        
        return em