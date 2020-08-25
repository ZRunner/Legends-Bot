import i18n
from discord.ext import commands


i18n.translations.container.clear() # invalidate old cache
i18n.set('filename_format', '{locale}.{format}')
i18n.set('fallback', 'en')
i18n.load_path.append('./lang')

class LangCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file="languages"
        self.languages = ['fr', 'en']
        self.cache = dict()


    async def tr(self, ctx, key, **kwargs):
        """Translate something"""
        if ctx.guild:
            lang = self.languages[await self.get_lang(ctx.guild.id)]
        else:
            lang = self.languages[0]
        return i18n.t(key, locale=lang, **kwargs)


    async def db_edit_lang(self, guildID: int, lang: int):
        cnx = self.bot.cnx
        cursor = cnx.cursor()
        query = ("INSERT INTO `server_config` (guild, lang) VALUES (%(ID)s, %(lang)s) ON DUPLICATE KEY UPDATE lang = %(lang)s;")
        cursor.execute(query, {'ID': guildID, 'lang': lang})
        cnx.commit()
        cursor.close()

    async def get_lang(self, guildID: int) -> int:
        if guildID not in self.cache:
            cnx = self.bot.cnx
            cursor = cnx.cursor(dictionary=False)
            query = ("SELECT lang FROM `server_config` WHERE guild=%(id)s")
            cursor.execute(query, {'id': guildID})
            liste = list(cursor)
            cursor.close()
            if len(liste) == 0:
                self.cache[guildID] = 0
            else:
                self.cache[guildID] = liste[0][0]
        return self.cache[guildID]

    @commands.command(name="language")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def change_lang(self, ctx):
        """Change the server language"""
        current = await self.get_lang(ctx.guild.id)
        self.cache[ctx.guild.id] = (current + 1) % len(self.languages)
        await self.db_edit_lang(ctx.guild.id, self.cache[ctx.guild.id])
        await ctx.send(await self.bot._(ctx, 'config.new_lang'))


def setup(bot):
    bot.add_cog(LangCog(bot))