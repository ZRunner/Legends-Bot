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
                flds.append({'name':c['Name'], 'value':await self.bot._(ctx, 'classes.field', hp=c['Health'], esc=c['Escape']), 'inline':False})
        else:
            c = data[names.index(nom.lower())]
            emojis = ctx.bot.cogs["UtilitiesCog"].emojis
            emb = self.bot.cogs["EmbedCog"].Embed(title=await self.bot._(ctx, 'classes.details', classe=c['Name']),desc=c['Description'],color=self.embed_color).update_timestamp().create_footer(ctx.author)
            flds.append({'name':await self.bot._(ctx, 'classes.name'), 'value':c['Name'], 'inline':False})
            flds.append({'name':await self.bot._(ctx, 'classes.hp'), 'value':"{} {}".format(ctx.bot.get_emoji(emojis['legends_heart']),c['Health']), 'inline':False})
            flds.append({'name':await self.bot._(ctx, 'classes.dodge'), 'value':"{}%".format(c['Escape']), 'inline':False})
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
        d = (await self.bot._(ctx, "stats.general")).format(len(self.bot.guilds),len(self.bot.users),len([x for x in ctx.bot.users if x.bot]),cl,version,discord.__version__,round(py.memory_info()[0]/2.**30,3),psutil.cpu_percent(),round(r.elapsed.total_seconds()*1000,3))
        t = "**" + await self.bot._(ctx, 'stats.title') + '**'
        emb = self.bot.cogs["EmbedCog"].Embed(title=t,desc=d,color=self.embed_color,fields=[]).update_timestamp().create_footer(ctx.author)
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
                await ctx.send(await self.bot._(ctx, "player.notfound", user=user))
                return
        d = await self.bot.cogs['UsersCog'].get_user_deck(user.id)
        if d == {}:
            if user == ctx.author:
                await ctx.send(await self.bot._(ctx, "player.nopeople1"))
            else:
                await ctx.send(await self.bot._(ctx, "player.nopeople2", user=user))
            return
        text = list()
        lvl = await self.bot._(ctx, "player.level")
        for x in sorted(d.values(), key=lambda k: k['level'],reverse=True):
            text.append("{} ({} {})".format(x['personnage'], lvl, x['level']))
        t = await self.bot._(ctx, "player.decktitle", user=user)
        emb = self.bot.cogs["EmbedCog"].Embed(title=t,desc="\n".join(text),color=self.embed_color,fields=[]).update_timestamp().create_footer(ctx.author)
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
            x = data[name] # personnage info
            # Coins emoji
            lg_coin = str(await ctx.bot.cogs['UtilitiesCog'].get_emoji('legends_coin'))
            # Embed title
            t = await self.bot._(ctx, "player.detailstitle")
            # Embed
            emb = self.bot.cogs["EmbedCog"].Embed(title=t, desc=x['Description'], color=self.embed_color).update_timestamp().create_footer(ctx.author)
            # Embed field data
            price = str(x['Prix']) + lg_coin
            get = 'Oui' if name in deck else 'Non'
            emo = ':white_check_mark:' if name in deck else ':x:'
            # Embed field
            emb.fields = [{'name':name, 'value': await self.bot._(ctx, "player.field", classe=x['Class'], att1=x['Attaque 1'], att2=x['Attaque 2'], att3=x['Ultime'], passiv=x['Passif'], price=price, got_emoji=emo, got=get), 'inline':False}]
        elif name is None:
            t = await self.bot._(ctx, "player.listtitle")
            emb = self.bot.cogs["EmbedCog"].Embed(title=t, color=self.embed_color, fields=[]).update_timestamp().create_footer(ctx.author)
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
        else:
            await ctx.send(await self.bot._(ctx, "player.invalidperson"))
            return
        await ctx.send(embed=emb.discord_embed())


    @commands.command(name="combat")
    async def combat(self,ctx,tours:int=None):
        """Lance un combat"""
        asyncio.run_coroutine_threadsafe(self.bot.cogs['CombatCog'].begin(ctx,tours),asyncio.get_running_loop())

    @commands.command(name="start")
    async def init_user(self,ctx):
        """Commencer la partie, avec 5 personnages aléatoires"""
        deck = await ctx.bot.cogs['UsersCog'].get_user_deck(ctx.author.id)
        if len(deck)>0:
            await ctx.send(await self.bot._(ctx, "start.already"))
            return
        await ctx.send(await self.bot._(ctx, "start.welcome", user=ctx.author.mention))
        l = await ctx.bot.cogs["UsersCog"].select_starterKit(ctx.author)
        await ctx.send(await self.bot._(ctx, "start.persons", people=", ".join(l)))
        

def setup(bot):
    bot.add_cog(Commands(bot))