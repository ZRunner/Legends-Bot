import discord
import sys
import traceback
import random
from discord.ext import commands
from math import log, exp


class ClassesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data = list()
        self.file = "persos"

    @commands.Cog.listener()
    async def on_ready(self):
        await self.get_data()

    async def get_data(self):
        cnx = self.bot.cnx
        cursor = cnx.cursor(dictionary=True)
        query = ("SELECT * FROM `classes` WHERE 1")
        cursor.execute(query)
        liste = list()
        for x in cursor:
            liste.append(x)
        cursor.close()
        self.data = liste
        return liste

    async def get_class(self, name):
        if len(self.data) == 0:
            await self.get_data
        for x in self.data:
            if x['Name'] == name:
                return x


class PersosCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "persos"
        self.data = dict()
        self.shields_lvl = None
        self.perso_names = list()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.get_data()
        self.shields_lvl = list()

    async def get_data(self):
        cnx = self.bot.cnx
        cursor = cnx.cursor(dictionary=True)
        query = ("SELECT * FROM `personnages` WHERE 1")
        cursor.execute(query)
        d = dict()
        for x in cursor:
            d[x['Name']] = x
        cursor.close()
        self.data = d
        return d

    async def calc_life(self, perso, level: int):
        d = self.bot.cogs['ClassesCog'].data
        if len(d) == 0:
            d = await self.bot.cogs['ClassesCog'].get_data()
        d = [x for x in d if x['Name'] == perso['Class']][0]
        return round(d['Health'] + 5/4*level)

    async def get_names_list(self) -> list:
        if len(self.perso_names) == 0:
            if len(self.data) == 0:
                await self.get_data()
            self.perso_names = list(self.data.keys())
        return self.perso_names


def setup(bot):
    bot.add_cog(ClassesCog(bot))
    bot.add_cog(PersosCog(bot))
