import nextcord
import sys
import psutil
import os
import requests
import asyncio
from nextcord.ext import commands

from utils import LegendsBot


SLASH_GUILDS = [513348985528778754]

class Commands(commands.Cog):

    def __init__(self, bot: LegendsBot):
        self.bot = bot
        self.embed_color = nextcord.Colour(16295964)
        self.file = 'commands'

    @nextcord.slash_command(name="classes", description="Describe each available class")
    async def cl(self, inter: nextcord.Interaction, name: str=nextcord.SlashOption(
                name="name",
                description="The name of the class. Don't fill to get the whole list",
                choices=("Guerrier", "Tank", "Soigneur", "Soutien", "Espion"),
                required=False)):
        """Get info about any class"""
        ClassesCog = self.bot.cogs['ClassesCog']
        await ClassesCog.get_data()
        data = ClassesCog.data
        names = [c['Name'].lower() for c in data]
        if name is None or name.lower() not in names:
            t = await self.bot._(inter, 'classes.list_title')
            emb = nextcord.Embed(title=t, color=self.embed_color)
            
            for c in data:
                class_desc = await self.bot._(inter, 'classes.field', hp=c['Health'], esc=c['Escape'])
                emb.add_field(name=c['Name'], value=class_desc, inline=False)
        else:
            c = data[names.index(name.lower())]
            emojis = self.bot.cogs["UtilitiesCog"].emojis
            t = await self.bot._(inter, 'classes.details', classe=c['Name'])
            emb = nextcord.Embed(title=t, color=self.embed_color)
            emb.add_field(name=await self.bot._(inter, 'classes.name'), value=c['Name'], inline=False)
            emb.add_field(name=await self.bot._(inter, 'classes.hp'), value="{} {}".format(self.bot.get_emoji(emojis['legends_heart']), c['Health']), inline=False)
            emb.add_field(name=await self.bot._(inter, 'classes.dodge'), value="{}%".format(c['Escape']), inline=False)
        await inter.send(embed=emb)

    @nextcord.slash_command(name="ping", description="Get the bot general latency")
    async def ping_slash(self, inter: nextcord.Interaction):
        """Get the bot latency"""
        await inter.send(f"Pong ! {self.bot.latency*1000:.2f}ms")

    @nextcord.slash_command(name="stats", description="Display some stats about the bot")
    async def stats(self, inter: nextcord.Interaction):
        """Get some bot stats"""
        v = sys.version_info
        version = str(v.major)+"."+str(v.minor)+"."+str(v.micro)
        pid = os.getpid()
        py = psutil.Process(pid)
        cl = self.bot.get_cog('UtilitiesCog').codelines
        r = requests.get('https://discordapp.com/api/v6')
        d = (await self.bot._(inter, "stats.general")).format(len(self.bot.guilds), len(self.bot.users), len([x for x in self.bot.users if x.bot]), cl, version, nextcord.__version__, round(py.memory_info()[0]/2.**30, 3), psutil.cpu_percent(), round(r.elapsed.total_seconds()*1000, 3))
        t = "**" + await self.bot._(inter, 'stats.title') + '**'
        emb = nextcord.Embed(title=t, description=d, color=self.embed_color)
        await inter.send(embed=emb)

    @nextcord.slash_command(name="deck", description="Show the characters owned by a player", guild_ids=SLASH_GUILDS)
    async def deck(self, inter: nextcord.Interaction, user: nextcord.User=nextcord.SlashOption(
                name="player",
                description="The player to target. Don't fill to see your own deck",
                required=False  
    )):
        """Display characters owned by a player"""
        if user.bot:
            await inter.send(await self.bot._(inter, "player.nobot"))
            return
        if user is None:
            user = inter.user
        deck: dict = await self.bot.cogs['UsersCog'].get_user_deck(user.id)
        if not deck:
            if user == inter.user:
                await inter.send(await self.bot._(inter, "player.nopeople1"))
            else:
                await inter.send(await self.bot._(inter, "player.nopeople2", user=user))
            return
        text = list()
        lvl_txt = await self.bot._(inter, "player.level")
        for x in sorted(deck.values(), key=lambda k: k['xp'], reverse=True):
            lvl = await self.bot.get_cog("UtilitiesCog").calc_level(x['xp'])
            text.append("{} ({} {})".format(x['personnage'], lvl_txt, lvl))
        t = await self.bot._(inter, "player.decktitle", user=user)
        emb = nextcord.Embed(title=t, description="\n".join(text), color=self.embed_color)
        await inter.send(embed=emb)

    @nextcord.slash_command(name="characters", description="Describe each character", guild_ids=SLASH_GUILDS)
    async def perso_display(self, inter: nextcord.Interaction, name: str=nextcord.SlashOption(
                name="character",
                description="The character name to look for. Don't fill to see the whole list",
                required=False
    )):
        """Get info about any character"""
        PCog = self.bot.cogs['PersosCog']
        await PCog.get_data()
        data = PCog.data
        deck = await self.bot.cogs['UsersCog'].get_user_deck(inter.user.id)
        deck = [x['personnage'] for x in deck.values()]
        for k, v in data.items():
            if k.lower() == str(name).lower() and v['actif']:
                name = k
        if name in data.keys():
            x = data[name]  # personnage info
            # Coins emoji
            lg_coin = str(await self.bot.cogs['UtilitiesCog'].get_emoji('legends_coin'))
            # Embed title
            t = await self.bot._(inter, "player.detailstitle")
            # Embed
            emb = nextcord.Embed(title=t, description=x['Description'], color=self.embed_color)
            # Embed field data
            price = str(x['Prix']) + lg_coin
            get = await self.bot._(inter, 'keywords.yes' if name in deck else 'keywords.no')
            emo = ':white_check_mark:' if name in deck else ':x:'
            # Embed field
            class_ = await self.bot._(inter, 'classes.list.'+x['Class'])
            field_value = await self.bot._(inter, "player.field", classe=class_, att1=x['Attaque 1'], att2=x['Attaque 2'], att3=x['Ultime'], passiv=x['Passif'], price=price, got_emoji=emo, got=get)
            emb.add_field(name=name, value=field_value, inline=False)
        elif name is None:
            t = await self.bot._(inter, "player.listtitle")
            emb = nextcord.Embed(title=t, color=self.embed_color)
            data = sorted(x for x in data.keys() if data[x]['actif'])
            nbr = len(data)
            for i in range(0, nbr, 10):
                l = list()
                for x in data[i:i+10]:
                    if x in deck:
                        l.append('**'+x+'**')
                    else:
                        l.append(x)
                name = "{}-{}".format(i+1, i+10 if i +10 < nbr else nbr)
                emb.add_field(name=name, value="\n".join(l), inline=True)
        else:
            await inter.send(await self.bot._(inter, "player.invalidperson"))
            return
        await inter.send(embed=emb)
    
    @perso_display.on_autocomplete("name")
    async def perso_display_autocomplete(self, inter: nextcord.Interaction, text: str):
        "Used to suggest character names to the user typing the command"
        PCog = self.bot.get_cog('PersosCog')
        data: list[str] = sorted(name for name, attrs in PCog.data.items() if attrs['actif'])
        text = text.lower()
        await inter.response.send_autocomplete([value for value in data if text in value.lower()][:25])

    @commands.command(name="combat")
    async def combat(self, ctx: commands.Context, tours: int = None):
        """Lance un combat"""
        asyncio.run_coroutine_threadsafe(self.bot.cogs['CombatCog'].begin(
            ctx, tours), asyncio.get_running_loop())

    @nextcord.slash_command(name="start", description="Start the game, with 5 random characters", guild_ids=SLASH_GUILDS)
    async def init_user(self, inter: nextcord.Interaction):
        """Commencer la partie, avec 5 personnages aléatoires"""
        deck = await self.bot.cogs['UsersCog'].get_user_deck(inter.user.id)
        if len(deck) > 0:
            await inter.send(await self.bot._(inter, "start.already"))
            return
        await inter.send(await self.bot._(inter, "start.welcome", user=inter.user.mention))
        l = await self.bot.cogs["UsersCog"].select_starterKit(inter.user)
        await inter.send(await self.bot._(inter, "start.persons", people=", ".join(l)))

def setup(bot):
    bot.add_cog(Commands(bot))
