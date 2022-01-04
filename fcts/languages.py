import i18n
import nextcord
from nextcord.ext import commands

class LangCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file="languages"
        self.languages = ['fr', 'en']
        self.cache = dict()
        i18n.translations.container.clear() # invalidate old cache
        i18n.load_path.clear()
        i18n.set('filename_format', '{locale}.{format}')
        i18n.set('fallback', 'en')
        i18n.load_path.append('./lang')


    async def tr(self, ctx, key: str, **kwargs):
        """Translate something"""
        lang = self.languages[0]
        if isinstance(ctx, commands.Context) and ctx.guild:
            lang = self.languages[await self.get_lang(ctx.guild.id)]
        elif isinstance(ctx, nextcord.Interaction) and ctx.guild_id:
            lang = self.languages[await self.get_lang(ctx.guild_id)]
        elif isinstance(ctx, nextcord.Guild):
            lang = self.languages[await self.get_lang(ctx.id)]
        elif isinstance(ctx, nextcord.abc.GuildChannel):
            lang = self.languages[await self.get_lang(ctx.guild.id)]
        elif isinstance(ctx, str) and ctx in self.languages:
            lang = ctx
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

    @nextcord.slash_command(name="language", description="Toggle the bot language in your server")
    async def change_lang(self, inter: nextcord.Interaction):
        """Change the server language"""
        if not inter.guild:
            await inter.send(await self.bot._(inter, 'error.command_in_dm'))
            return
        if not inter.user.guild_permissions.manage_guild:
            await inter.send(await self.bot._(inter, 'error.missing_perms', perms=await self.bot._(inter, 'perms.manage_guild')))
            return
        current = await self.get_lang(inter.guild_id)
        self.cache[inter.guild_id] = (current + 1) % len(self.languages)
        await self.db_edit_lang(inter.guild_id, self.cache[inter.guild_id])
        await inter.send(await self.bot._(inter, 'config.new_lang'))


def setup(bot):
    bot.add_cog(LangCog(bot))