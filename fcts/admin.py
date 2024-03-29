import nextcord
from nextcord.ext import commands

import time, importlib, traceback, os, importlib, io, textwrap, copy, typing, asyncio
from contextlib import redirect_stdout
from fcts import reloads
from utils import LegendsBot
importlib.reload(reloads)


class perso(commands.Converter):
    async def convert(self,ctx:commands.Context,arg) -> str:
        PCog = set(ctx.bot.cogs['PersosCog'].data.keys())
        if len(PCog)==0:
            PCog = set((await ctx.bot.cogs['PersosCog'].get_data()).keys())
        if arg in PCog:
            return arg
        else:
            raise commands.errors.BadArgument('Personnage invalide : '+arg)


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])
    # remove `foo`
    return content.strip('` \n')

class AdminCog(commands.Cog):
        
    def __init__(self, bot: LegendsBot):
        self.bot = bot
        self.file = "admin"
        self._last_result = None
    
    @commands.command(name='admins')
    async def admin_list(self, ctx: commands.Context):
        """Affiche la liste des administrateurs du bot"""
        l  = list()
        for u in reloads.admins_id:
            l.append(str(self.bot.get_user(u)))
        await ctx.send("Les administrateurs de ce bot sont : {}".format(", ".join(l)))

    @commands.group(name='admin',hidden=False)
    @commands.check(reloads.check_admin)
    async def main_msg(self, ctx: commands.Context):
        """Fonctions réservées aux admins du bot"""
        if ctx.invoked_subcommand is None:
            text = "Liste des commandes disponibles :"
            for cmd in self.main_msg.commands:
                text+="\n- {} *({})*".format(cmd.name,cmd.help)
                if not cmd.enabled:
                    continue
                if type(cmd)==commands.core.Group:
                    for cmds in cmd.commands:
                        text+="\n    - {} *({})*".format(cmds.name,cmds.help)
            await ctx.send(text)

    @main_msg.command(name='db_reload')
    @commands.check(reloads.check_admin)
    async def db_reload(self, ctx: commands.Context):
        """Reconnecte le bot à la base de donnée"""
        try:
            self.bot.cogs['UtilitiesCog'].config = None
            self.bot.cnx.close()
            self.bot.connect_database()

            if self.bot.cnx != None:
                await ctx.bot.cogs['UtilitiesCog'].add_check_reaction(ctx.message)
        except Exception as e:
            await self.bot.cogs['ErrorsCog'].on_cmd_error(ctx,e)

    @main_msg.command(name="logs")
    @commands.check(reloads.check_admin)
    async def show_last_logs(self, ctx: commands.Context,lines:typing.Optional[int]=5,match=''):
        """Affiche les <lines> derniers logs ayant <match> dedans"""
        try:
            with open('debug.log','r',encoding='utf-8') as file:
                text = file.read().split("\n")
            msg = str()
            liste = list()
            i = 1
            while len(liste)<=lines and i<min(2000,len(text)):
                i+=1
                if (not match in text[-i]) or ctx.message.content in text[-i]:
                    continue
                liste.append(text[-i].replace('`',''))
            for i in liste:
                if len(msg+i)>1900:
                    await ctx.send("```\n{}\n```".format(msg))
                    msg = ""
                if len(i)<1900:
                    msg += "\n"+i.replace('`','')
            await ctx.send("```\n{}\n```".format(msg))
        except Exception as e:
            await self.bot.cogs['ErrorsCog'].on_error(e,ctx)

    @main_msg.command(name="cogs",hidden=True)
    @commands.check(reloads.check_admin)
    async def list_cogs(self, ctx: commands.Context):
        """Donne la liste des cogs chargés"""
        text = str()
        for k,v in self.bot.cogs.items():
            text +="- {} ({}) \n".format(v.file,k)
        await ctx.send(text)

    @main_msg.command(name='shutdown')
    async def shutdown(self, ctx: commands.Context,arg=""):
        """Eteint le bot"""
        m = await ctx.send("Nettoyage de l'espace de travail...")
        self.bot.log.debug("Suppression des fichiers pycache")
        for folderName, _, filenames in os.walk('.'):
            for filename in filenames:
                if filename.endswith('.pyc'):
                    os.unlink(folderName+'/'+filename)
            if  folderName.endswith('__pycache__'):
                os.rmdir(folderName)
        await m.edit(content="Bot en voie d'extinction")
        await self.bot.change_presence(status=nextcord.Status('offline'))
        self.bot.log.info("Fermeture du bot")
        self.bot.cnx.close()
        await self.bot.close()


    @main_msg.command(name='reload')
    async def reload_cog(self, ctx: commands.Context, *, cog: str):
        """Recharge un module"""
        cogs = cog.split(" ")
        await self.bot.cogs["ReloadsCog"].reload_cogs(ctx,cogs)

    @main_msg.command(name="get_invites",aliases=['invite'])
    async def adm_invites(self, ctx: commands.Context,server=None):
        """Cherche une invitation pour un serveur, ou tous"""
        if server != None:
            guild = nextcord.utils.get(self.bot.guilds, name=server)
            if guild == None:
                msg = "Le serveur `{}` n'a pas été trouvé".format(server)
            else:
                inv = await guild.invites()
                if len(inv)>0:
                    msg = inv[0]
                else:
                    msg = "Le serveur `{}` ne possède pas d'invitation".format(guild.name)
        else:
            liste = list()
            for server in self.bot.guilds:
                try:
                    inv = await server.invites()
                except:
                    inv = []
                if len(inv)>0:
                    inv = inv[0]
                else:
                    inv = "None"
                liste.append("{} - {} ({} membres)".format(server.name,inv,len(server.members)))
            msg = "\n".join(liste)
        await ctx.author.send(msg)

    @commands.command(name="activity",hidden=True)
    @commands.check(reloads.check_admin)
    async def change_activity(self, ctx: commands.Context, Type: str, * act: str):
        """Change l'activité du bot (play,watch,listen,stream)"""
        act = " ".join(act)
        if Type in ['game','play']:
            await self.bot.change_presence(activity=nextcord.Game(name=act))
        elif Type in ['watch','see']:
            await self.bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching,name=act,timestamps={'start':time.time()}))
        elif Type in ['listen']:
            await self.bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening,name=act,timestamps={'start':time.time()}))
        elif Type in ['stream']:
            await self.bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.streaming,name=act,timestamps={'start':time.time()}))
        else:
            return await ctx.send("Sélectionnez *play*, *watch*, *listen* ou *stream* suivi du nom")
        await ctx.message.delete()

    @commands.command(name='eval')
    @commands.check(reloads.check_admin)
    async def _eval(self, ctx: commands.Context, *, body: str):
        """Evaluates a code
        Credits: Rapptz (https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py)"""
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }
        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()
        try:
            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
        except Exception as e:
            await self.bot.cogs['ErrorsCog'].on_error(e,ctx)
            return
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            await ctx.bot.cogs['UtilitiesCog'].add_check_reaction(ctx.message)

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')
    
    @commands.command(name='execute',hidden=True)
    @commands.check(reloads.check_admin)
    async def sudo(self, ctx: commands.Context, who: typing.Union[nextcord.Member, nextcord.User], *, command: str):
        """Run a command as another user
        Credits: Rapptz (https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py)"""
        msg = copy.copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        #new_ctx.db = ctx.db
        await self.bot.invoke(new_ctx)
            
    @commands.command(name="reset")
    @commands.check(reloads.check_admin)
    async def reset_player(self, ctx: commands.Context,*,user:nextcord.User):
        """Supprime tous les personnages d'un joueur"""
        if user.id in reloads.admins_id and user!=ctx.author:
            return await ctx.send("Vous ne pouvez pas reset les personnages d'un autre administrateur !")
        deck = await ctx.bot.cogs['UsersCog'].get_user_deck(user.id)
        msg = await ctx.send("Le joueur {} a actuellement {} personnages. Veuillez confirmer le reset".format(user,len(deck)))
        await msg.add_reaction('✅')
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅' and reaction.message.id==msg.id and user != ctx.guild.me
        try:
            await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Procédure de reset du joueur {} annulée".format(ctx.author.mention))
            return
        await ctx.bot.cogs["UsersCog"].reset_player(user.id)
        await ctx.send("Le joueur {} ({}) a bien été remis à zéro".format(user,user.id))
        ctx.bot.log.info("Le joueur {} ({}) a bien été remis à zéro".format(user,user.id))
    
    @commands.command(name="give-user")
    @commands.check(reloads.check_admin)
    async def give_perso(self, ctx: commands.Context,user:nextcord.User,persos:commands.Greedy[perso]):
        """Donne au joueur certains personnages"""
        PCog = set(self.bot.cogs['PersosCog'].data.keys())
        if len(PCog)==0:
            PCog = set((await self.bot.cogs['PersosCog'].get_data()).keys())
        txt = list()
        worked = list()
        for p in persos:
            if not p in PCog:
                txt.append(f"Le personnage '{p}' est invalide")
            else:
                await self.bot.cogs['UsersCog'].add_perso(p,user.id)
                worked.append(p)
        txt.append("{} personnage(s) ajouté(s) pour le joueur {}".format(len(worked),user))
        await ctx.send("\n".join(txt))
        self.bot.log.info("{} personnages ajoutés au joueur {} ({}) : {}".format(len(worked),user,user.id," ".join(worked)))


def setup(bot):
    bot.add_cog(AdminCog(bot))
