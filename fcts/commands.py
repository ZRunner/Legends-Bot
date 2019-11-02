import discord, sys, psutil, os, requests, asyncio
from discord.ext import commands

class Commands(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.embed_color = discord.Colour(16295964)
        self.file = 'commands'


    @commands.command(name="classes",aliases=["classe"])
    async def cl(self,ctx,*,nom='None'):
        """Voir les détails de chaque classe"""
        ClassesCog = self.bot.cogs['ClassesCog']
        await ClassesCog.get_data()
        data = ClassesCog.data
        names = list()
        flds = list()
        for c in data:
            names.append(c['Name'].lower())
        if nom.lower() not in names:
            emb = self.bot.cogs["EmbedCog"].Embed(title="Liste des classes",color=self.embed_color).update_timestamp().create_footer(ctx.author)
            for c in data:
                flds.append({'name':c['Name'], 'value':"Points de vie : {}\nChances d'esquive : {}%".format(c['Health'],c['Escape']), 'inline':False})
        else:
            c = data[names.index(nom.lower())]
            emojis = ctx.bot.cogs["UtilitiesCog"].emojis
            emb = self.bot.cogs["EmbedCog"].Embed(title="Détails de la classe {}".format(c['Name']),desc=c['Description'],color=self.embed_color).update_timestamp().create_footer(ctx.author)
            flds.append({'name':'Nom', 'value':c['Name'], 'inline':False})
            flds.append({'name':'Points de vie', 'value':"{} {}".format(ctx.bot.get_emoji(emojis['legends_heart']),c['Health']), 'inline':False})
            flds.append({'name':"Chances d'esquiver", 'value':"{}%".format(c['Escape']), 'inline':False})
        emb.fields = flds
        await ctx.send(embed=emb.discord_embed())

    @commands.command(name="ping")
    async def ping(self,ctx):
        """Voir la latence du bot"""
        m = await ctx.send("Pong !")
        t = (m.created_at - ctx.message.created_at).total_seconds()
        await m.edit(content="Pong ! ("+str(round(t*1000,3))+"ms)")

    @commands.command(name="stats")
    async def stats(self,ctx):
        """Voir quelques statistiques du bot"""
        v = sys.version_info
        version = str(v.major)+"."+str(v.minor)+"."+str(v.micro)
        pid = os.getpid()
        py = psutil.Process(pid)
        cl = ctx.bot.cogs['UtilitiesCog'].codelines
        r = requests.get('https://discordapp.com/api/v6')
        d = """**Nombre de serveurs :** {}
        **Nombre de membres visibles :** {} ({} bots)
        **Nombre de lignes de code :** {}
        **Version de Python :** {}
        **Version de la bibliothèque `discord.py` :** {}
        **Charge sur la mémoire vive :** {} GB
        **Charge sur le CPU :** {} %
        **Temps de latence de l'api :** {} ms
        """.format(len(self.bot.guilds),len(self.bot.users),len([x for x in ctx.bot.users if x.bot]),cl,version,discord.__version__,round(py.memory_info()[0]/2.**30,3),psutil.cpu_percent(),round(r.elapsed.total_seconds()*1000,3))
        emb = self.bot.cogs["EmbedCog"].Embed(title="**Statistiques du bot**",desc=d,color=self.embed_color,fields=[]).update_timestamp().create_footer(ctx.author)
        await ctx.send(embed=emb.discord_embed())

    @commands.command(name="deck")
    async def deck(self,ctx,*,user=None):
        """Afficher les personnages possédés par utilisateur"""
        if user == None:
            user = ctx.author
        else:
            try:
                user = await commands.UserConverter().convert(ctx,user)
            except:
                await ctx.send('Impossible de trouver le joueur {} !'.format(user))
                return
        d = await self.bot.cogs['UsersCog'].get_user_deck(user.id)
        if d == {}:
            if user == ctx.author:
                await ctx.send("Vous ne possédez aucun personnage !")
            else:
                await ctx.send("Le joueur {} ne possède aucun personnage !".format(user))
            return
        text = list()
        for x in sorted(d.values(), key=lambda k: k['level'],reverse=True):
            text.append("{} (niveau {})".format(x['personnage'],x['level']))
        emb = self.bot.cogs["EmbedCog"].Embed(title="Personnages du joueur {}".format(user),desc="\n".join(text),color=self.embed_color,fields=[]).update_timestamp().create_footer(ctx.author)
        await ctx.send(embed=emb.discord_embed())


    @commands.command(name="perso",aliases=['persos','personnages'])
    async def perso_display(self,ctx,*,name=None):
        """Obtenir les détails de chaque personnage"""
        PCog = self.bot.cogs['PersosCog']
        await PCog.get_data()
        data = PCog.data
        deck = await self.bot.cogs['UsersCog'].get_user_deck(ctx.author.id)
        deck = [x['personnage'] for x in deck.values()]
        for k,v in data.items():
            if k.lower() == str(name).lower() and v['actif']:
                name = k
        if name in data.keys():
            x = data[name]
            lg_coin = str(await ctx.bot.cogs['UtilitiesCog'].get_emoji('legends_coin'))
            emb = self.bot.cogs["EmbedCog"].Embed(title="Détails du personnage",desc=x['Description'],color=self.embed_color).update_timestamp().create_footer(ctx.author)
            get = 'Oui' if name in deck else 'Non'
            emb.fields = [{'name':name, 'value':"Classe : {}\nAttaque de base : {}\nCompétence : {}\nCompétence ultime : {}\nCompétence passive : {}\nPrix actuel : {}{}\n\n{} Obtenu : {}".format(x['Class'],x['Attaque 1'],x['Attaque 2'],x['Ultime'],x['Passif'],x['Prix'],lg_coin,':white_check_mark:' if name in deck else ':x:',get), 'inline':False}]
        else:
            emb = self.bot.cogs["EmbedCog"].Embed(title="Liste des personnages",color=self.embed_color,fields=[]).update_timestamp().create_footer(ctx.author)
            data = [x for x in sorted(list(data.keys())) if data[x]['actif']]
            nbr = len(data)
            for i in range(0, nbr, 10):
                l = list()
                for x in data[i:i+10]:
                    if x in deck:
                        l.append('**'+x+'**')
                    else:
                        l.append(x)
                emb.fields.append({'name':"{}-{}".format(i+1,i+10 if i+10<nbr else nbr), 'value':"\n".join(l), 'inline':True})
        await ctx.send(embed=emb.discord_embed())


    @commands.command(name="combat")
    async def combat(self,ctx):
        """Lance un combat"""
        asyncio.run_coroutine_threadsafe(self.bot.cogs['CombatCog'].begin(ctx),asyncio.get_running_loop())

    @commands.command(name="start")
    async def init_user(self,ctx):
        """Commencer la partie, avec 5 personnages aléatoires"""
        deck = await ctx.bot.cogs['UsersCog'].get_user_deck(ctx.author.id)
        if len(deck)>0:
            return await ctx.send("Vous avez déjà des personnages !")
        await ctx.send("Bienvenue {} dans l'aventure !\nPour que vous commenciez avec de bonnes bases, nous vous avons donné au hasard 5 personnages.".format(ctx.author.mention))
        l = await ctx.bot.cogs["UsersCog"].select_starterKit(ctx.author)
        await ctx.send("Ces personnages sont {}.\nVous pouvez entrer `/deck` pour voir la liste de vos personnages, et `/help` pour la liste des commandes disponibles. Bonne chance !".format(", ".join(l)))
        

def setup(bot):
    bot.add_cog(Commands(bot))