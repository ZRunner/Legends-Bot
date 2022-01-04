import datetime
import time
from nextcord.ext import commands
import logging
import nextcord
import mysql
import sys


class LegendsBot(commands.AutoShardedBot):

    def __init__(self, case_insensitive=None, status=None):
        # defining allowed default mentions
        allowed_mentions = nextcord.AllowedMentions(everyone=False, roles=False)
        # defining intents usage
        intents = nextcord.Intents.default()
        intents.members = True
        intents.typing = False
        intents.webhooks = False
        intents.integrations = False
        # we now initialize the bot class
        super().__init__(command_prefix=get_prefix,
                case_insensitive=case_insensitive,
                status=status,
                allowed_mentions=allowed_mentions,
                intents=intents)
        self.database_online = True
        self.log = logging.getLogger("runner")
        self._cnx = [None,0]
        self.database_keys = {'user':'legendsbot','password':'12lEGE-nD-0754','host':'137.74.246.110','database':'legends_club'}
        self.add_check(check_banned_use, call_once=True)
    
    async def user_avatar_as(self,user,size=512):
        """Get the avatar of an user, format gif or png (as webp isn't supported by some browsers)"""
        if not isinstance(user,(nextcord.User,nextcord.Member)):
            raise ValueError
        try:
            return user.display_avatar.replace(size=size, static_format='png')
        except Exception as e:
            await self.cogs['ErrorsCog'].on_error(e,None)

    def utcnow(self) -> datetime.datetime:
        """Get the current date and time with UTC timezone"""
        return datetime.datetime.now(datetime.timezone.utc)
    
    @property
    def _(self):
        cog = self.get_cog('LangCog')
        if cog is None:
            self.log.error("Unable to load Language cog")
            return lambda *args, **kwargs: args[1]
        return self.get_cog('LangCog').tr
    
    @property
    def cnx(self):
        if self._cnx[1] + 1260 < round(time.time()): # 21min
            self.connect_database()
            self._cnx[1] = round(time.time())
            return self._cnx[0]
        else:
            return self._cnx[0]
    
    def connect_database(self):
        if len(self.database_keys)>0:
            if self._cnx[0] != None:
                self._cnx[0].close()
            self.log.debug('Connection à MySQL (user {})'.format(self.database_keys['user']))
            self._cnx[0] = mysql.connector.connect(user=self.database_keys['user'],password=self.database_keys['password'],host=self.database_keys['host'],database=self.database_keys['database'])
            self._cnx[1] = round(time.time())
        else:
            raise ValueError(dict)
    
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    
    async def get_prefix(self,msg):
        return get_prefix(self,msg)


def get_prefix(bot, msg):
    return '&'


def setup_logger():
    # on chope le premier logger
    log = logging.getLogger("runner")
    # on définis un formatteur
    format = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", datefmt="[%d/%m/%Y %H:%M]")
    # ex du format : [08/11/2018 14:46] WARNING RSSCog fetch_rss_flux l.288 : Cannot get the RSS flux because of the following error: (suivi du traceback)

    # log vers un fichier
    file_handler = logging.FileHandler("debug.log")
    file_handler.setLevel(logging.DEBUG)  # tous les logs de niveau DEBUG et supérieur sont evoyés dans le fichier
    file_handler.setFormatter(format)

    # log vers la console
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)  # tous les logs de niveau INFO et supérieur sont evoyés dans le fichier
    stream_handler.setFormatter(format)

    ## supposons que tu veuille collecter les erreurs sur ton site d'analyse d'erreurs comme sentry
    #sentry_handler = x
    #sentry_handler.setLevel(logging.ERROR)  # on veut voir que les erreurs et au delà, pas en dessous
    #sentry_handler.setFormatter(format)

    # log.debug("message de debug osef")
    # log.info("message moins osef")
    # log.warn("y'a un problème")
    # log.error("y'a un gros problème")
    # log.critical("y'a un énorme problème")

    log.addHandler(file_handler)
    log.addHandler(stream_handler)
    #log.addHandler(sentry_handler)

    log.setLevel(logging.DEBUG)

    return log

def check_banned_use(ctx: commands.Context):
    if Utils := ctx.bot.get_cog("UtilitiesCog"):
        if not Utils.config:
            return
    banned_users = Utils.config[0]['banned_users'].split(";")
    if str(ctx.author.id) in banned_users:
        return False
    banned_guilds = Utils.config[0]['banned_guilds'].split(";")
    return ctx.guild == None or str(ctx.guild.id) not in banned_guilds