import nextcord
import mysql.connector
from nextcord.ext import commands
from math import floor


class UtilitiesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "utilities"
        self.codelines = 0
        self.emojis = {'legends_coin': 539098866931335210,
                       'legends_heart': 513685971443646464,
                       'legends_bag': 513713064449671169,
                       'ultime': 546756240798121994,
                       'attaque1': 546756241272078346,
                       'attaque2': 546756242258001951,
                       'passif': 546756240748052511,
                       'vide': 552451143004061696,
                       'effects': 552848967377879040,
                       'invisible': 639951219254624267,
                       'ko': 640312453103878165,
                       'bleed': 640580514012463141,
                       'poison': 680872153872334849,
                       'att_boost': 640580485415698452,
                       'att_less': 640580460249874491,
                       'shield_less': 763084759298474044,
                       'energy': 765896121917636629}
        self.config = self.get_bot_infos()

    async def get_emoji(self, name):
        if name not in self.emojis.keys():
            return None
        return self.bot.get_emoji(self.emojis[name])

    async def suppr(self, msg):
        try:
            await msg.delete()
        except:
            pass

    def get_bot_infos(self):
        """Retourne toutes les options du bot"""
        cnx = mysql.connector.connect(
            user=self.bot.database_keys['user'], password=self.bot.database_keys['password'], host=self.bot.database_keys['host'], database='frm')
        cursor = cnx.cursor(dictionary=True)
        query = ("SELECT * FROM `bot_infos` WHERE `ID`=493195981450379292")
        cursor.execute(query)
        liste = list()
        for x in cursor:
            liste.append(x)
        cursor.close()
        cnx.close()
        return liste

    def getIfromRGB(self, rgb):
        red = rgb[0]
        green = rgb[1]
        blue = rgb[2]
        RGBint = (red << 16) + (green << 8) + blue
        return RGBint

    async def add_check_reaction(self, message):
        try:
            emoji = nextcord.utils.get(self.bot.emojis, name='greencheck')
            if emoji:
                await message.add_reaction(emoji)
            else:
                await message.add_reaction('\u2705')
        except:
            pass

    async def count_lines_code(self):
        """Count the number of lines for the whole project"""
        count = 0
        try:
            with open('start.py', 'r') as file:
                for line in file.read().split("\n"):
                    if len(line.strip()) > 2 and line[0] != '#':
                        count += 1
            files = list()
            for cog in self.bot.cogs.values():
                if cog.file in files:
                    break
                with open('fcts/'+cog.file+'.py', 'r') as file:
                    for line in file.read().split("\n"):
                        if len(line.strip()) > 2 and line[0] != '#':
                            count += 1
                    files.append(cog.file)
        except Exception as e:
            await self.bot.cogs['ErrorsCog'].on_error(e, None)
        self.codelines = count
        return count

    async def calc_level(self, xp: int) -> int:
        return 1 + floor(0.287*(xp**0.411))


def setup(bot):
    bot.add_cog(UtilitiesCog(bot))
