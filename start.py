#!/usr/bin/env python
#coding=utf-8

import time
t1=time.time()

#Here we import some libs
def check_libs():
    count = 0
    for m in ["mysql","discord","psutil","requests"]:
        try:
            exec("import "+m)
            exec("del "+m)
        except ModuleNotFoundError:
            print("Library {} manquante".format(m))
            count +=1
    if count>0:
        return False
    del count
    return True

if check_libs():
    import discord, sys, traceback, asyncio, time, logging, os, mysql
    from discord.ext import commands
else:
    import sys
    print("Fin de l'exécution")
    sys.exit()


def get_prefix(bot,msg):
    return '/'


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

    return log

class zbot(commands.AutoShardedBot):

    def __init__(self,command_prefix=None,case_insensitive=None,status=None,database_online=True):
        super().__init__(command_prefix=command_prefix,case_insensitive=case_insensitive,status=status)
        self.database_online = database_online
        self.log = logging.getLogger("runner")
        self._cnx = [None,0]
        self.database_keys = {'user':'legendsbot','password':'12lEGE-nD-0754','host':'137.74.246.110','database':'legends_club'}
    
    async def user_avatar_as(self,user,size=512):
        """Get the avatar of an user, format gif or png (as webp isn't supported by some browsers)"""
        if not isinstance(user,(discord.User,discord.Member)):
            raise ValueError
        try:
            if user.is_avatar_animated():
                return user.avatar_url_as(format='gif',size=size)
            else:
                return user.avatar_url_as(format='png',size=size)
        except Exception as e:
            await self.cogs['ErrorsCog'].on_error(e,None)
    
    @property
    def _(self):
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

initial_extensions = ['fcts.admin',
                    'fcts.classes',
                    'fcts.commands',
                    'fcts.errors',
                    'fcts.languages',
                    'fcts.persos',
                    'fcts.reloads',
                    'fcts.timeclass',
                    'fcts.users',
                    'fcts.utilities',
                    'fcts.aide',
                    'fcts.embeds',
                    'fcts.combat',
                    'fcts.attacks',
                    'fcts.effects'
  ]

def main():
    client = zbot(command_prefix=get_prefix,case_insensitive=True,status=discord.Status('online'))
    if os.path.exists("debug.log"):
        s = os.path.getsize('debug.log')/1.e9
        if s>10:
            print("Taille de debug.log supérieure à 10Gb ({}Gb)\n   -> Suppression des logs".format(s))
            os.remove('debug.log')
        del s

    # Here we load our extensions(cogs) listed above in [initial_extensions]
    count = 0
    for extension in initial_extensions:
        if not client.database_online:
            extension = extension.replace('fcts','fctshl')
        try:
            client.load_extension(extension)
        except:
            print(f'\nFailed to load extension {extension}', file=sys.stderr)
            traceback.print_exc()
            count += 1
        if count >0:
            raise Exception("\n{} modules not loaded".format(count))
    del count
    utilities = client.cogs["UtilitiesCog"]

    async def on_ready():
        await utilities.count_lines_code()
        await utilities.print2('\nBot connecté')
        await utilities.print2("Nom : "+client.user.name)
        await utilities.print2("ID : "+str(client.user.id))
        serveurs = []
        for i in client.guilds:
            serveurs.append(i.name)
        ihvbsdi="Connecté sur ["+str(len(client.guilds))+"] "+", ".join(serveurs)
        await utilities.print2(ihvbsdi)
        await utilities.print2(time.strftime("%d/%m  %H:%M:%S"))
        await utilities.print2("Prêt en {}s".format(round(time.time()-t1,3)))
        await utilities.print2('------')
        await asyncio.sleep(3)
        await client.change_presence(activity=discord.Game(name="baaatttle!"))

    with open('secrets.txt','r') as f:
        token = f.read().strip()

    async def check_once(ctx):
        try:
            return await ctx.bot.cogs['UtilitiesCog'].global_check(ctx)
        except Exception as e:
            ctx.bot.log.error("ERROR on global_check:",e,ctx.guild)
            return True

    client.add_listener(on_ready)
    client.add_check(check_once,call_once=True)

    log = setup_logger()
    log.setLevel(logging.DEBUG)
    log.info("Lancement du bot")

    client.run(token)

if check_libs() and __name__ == "__main__":
    main()