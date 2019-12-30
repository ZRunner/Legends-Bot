from discord.ext import commands
import discord, asyncio, random

class Team:
    def __init__(self,players=[],user=None,rounds=0):
        self.user = user
        self.players = players
        self.rounds = rounds
        self._nbr = 0
    
    @property
    def nbr(self) -> int:
        if self._nbr >= len(self.players):
            self._nbr = 0
        self._nbr += 1
        return self._nbr-1
    
    def __str__(self):
        return '<Team  user="{}"  players=[{}]  rounds={}>'.format(self.user,", ".join([str(x) for x in self.players]),self.rounds)
    
    def __len__(self):
        return len(self.players)

class Perso:
    def __init__(self,name,classe,lvl,at1,at2,ult,pas,life,esquive,Type,passifType):
        self.name = name
        self.classe = classe
        self.lvl = lvl
        self.attaque1 = at1
        self.attaque2 = at2
        self.ultime = ult
        self.passif = pas
        self.xp = 0
        self.points = random.randint(0,5)
        self.life = [life,life] # [actuel, max]
        self.effects = dict() # {nom: [coroutine,tours]}
        self.frozen = 0
        self.shield = 0
        self.invisible = 0
        self.critical = 10
        self.attack_bonus = 0 # par unité
        self.initialized = False
        self.esquive = esquive # donner/enlever 20-40 à chaque fois
        self.thorny = False
        self.type = Type
        self.provocation_coef = 1
        self.attack_bonus_type = dict() # {type : boost} pour les boosts contre un type de perso particulier
        self.passifType = passifType
        self.Team1 = None # sa propre équipe
        self.Team2 = None # équipe adverse
    
    def __str__(self):
        return '<Perso  name="{}"  classe="{}"  lvl={}  xp={}>'.format(self.name,self.classe,self.lvl,self.xp)



class CombatCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.in_combat = list()
        self.file = "combat"
        self.costs = {'attaque2':3, 'ultime':6}
        self.timeouts = {'choix-persos':60.0}
    

    def cog_unload(self):
        self.in_combat = list()
    
    async def select_team(self,user,channel,deck):
        """Demande à un utilisateur de choisir 5 personnages"""
        try:
            suppr = self.bot.cogs['UtilitiesCog'].suppr
            deck = [x for x in deck.values()]
            names = [x['personnage'] for x in deck]
            bot_msg = await channel.send("{}, veuillez choisir vos personnages. Pour cela, entrez simplement leurs numéros, séparés par des virgules. Voici la liste de vos personnages :\n {}".format(user.mention,"\n ".join(["{}) {}".format(e+1,v) for e,v in enumerate(names)])))
            def check(msg):
                return msg.author==user and msg.channel==channel
            tries = 0
            choice = list()
            while len(choice)<5:
                try:
                    choice_digits = list()
                    msg = await self.bot.wait_for('message', timeout=self.timeouts['choix-persos'], check=check)
                except asyncio.TimeoutError:
                    await channel.send("Vous avez été trop long à choisir, abandon du combat")
                    await suppr(bot_msg)
                    return []
                try:
                    choice = []
                    for item in msg.content.split(','):
                        item = item.strip()
                        if int(item)>0 and item not in choice_digits:
                            choice_digits.append(item)
                            choice.append(deck[int(item)-1])
                except:
                    if tries==3:
                        await channel.send("Vous avez échoué trop de fois :confused:")
                        await suppr(bot_msg)
                        return []
                    await channel.send("Réponse invalide. Veuillez recommencer")
                    tries += 1
                else:
                    if len(choice)<5:
                        await channel.send("Vous devez sélectionner 5 personnages")
                        tries +=1
            await suppr(bot_msg)
            return choice
        except Exception as e:
            await self.bot.cogs["ErrorsCog"].on_error(e,None)
        

    async def begin(self,ctx,tours:int):
        """Attend un début de partie"""
        if ctx.author in self.in_combat:
            return await ctx.send("{}, Vous avez déjà un combat en cours !".format(ctx.author.mention))
        play1_deck = await ctx.bot.cogs['UsersCog'].get_user_deck(ctx.author.id)
        if len(play1_deck)<5:
            return await ctx.send("Vous ne possédez pas assez de personnages pour jouer !")
        msg = await ctx.send("Un combat se prépare ! Cliquez sur la réaction :white_check_mark: pour affronter {} !".format(ctx.author))
        await msg.add_reaction('✅')
        self.in_combat.append(ctx.author)
        # Sélection de l'adversaire
        def check(reaction, user):
            return user != ctx.author and str(reaction.emoji) == '✅' and reaction.message.id==msg.id and user != ctx.guild.me and user not in self.in_combat
        try:
            _, user = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            self.in_combat.remove(ctx.author)
            await ctx.send("{}, vous n'avez pas réussi à trouver un adversaire dans les temps :hourglass:".format(ctx.author.mention))
            return
        await msg.clear_reactions()
        play2_deck = await ctx.bot.cogs['UsersCog'].get_user_deck(user.id)
        if len(play2_deck)<5:
            self.in_combat.remove(ctx.author)
            return await ctx.send("{}, vous ne possédez pas assez de personnages pour jouer !".format(user.mention))
        self.in_combat.append(user)
        await ctx.send("{} a rejoint le combat ! Bonne chance à vous deux !".format(user.mention))
        # Sélection des personnages
        try:
            play1_players = []
            play2_players = []
            if len(play1_deck)==5:
                play1_players = [x for x in play1_deck.values()]
            else:
                play1_players = await self.select_team(ctx.author,ctx.channel,play1_deck)
                if len(play1_players)==0:
                    self.in_combat.remove(ctx.author)
                    self.in_combat.remove(user)
                    return
            if len(play2_deck)==5:
                play2_players = [x for x in play2_deck.values()]
            else:
                play2_players = await self.select_team(user,ctx.channel,play2_deck)
                if len(play2_players)==0:
                    self.in_combat.remove(ctx.author)
                    self.in_combat.remove(user)
                    return
            # Création de l'équipe 1
            l = list()
            PCog = self.bot.cogs['PersosCog'].data
            if len(PCog)==0:
                PCog = await self.bot.cogs['PersosCog'].get_data()
            for p in play1_players:
                data = PCog[p['personnage']]
                life = await self.bot.cogs['PersosCog'].calc_life(data,p['level'])
                esq = (await self.bot.cogs['ClassesCog'].get_class(data['Class']))['Escape']
                l.append(Perso(name=p['personnage'],classe=data['Class'],lvl=p['level'],at1=data['Attaque 1'],at2=data['Attaque 2'],ult=data['Ultime'],pas=data['Passif'],life=life,esquive=esq,Type=data['Type'],passifType=data['type_passif']))
            Team1 = Team(user=ctx.author,players=l)
            # Création de l'équipe 2
            l = list()
            for p in play2_players:
                data = PCog[p['personnage']]
                life = await self.bot.cogs['PersosCog'].calc_life(data,p['level'])
                esq = (await self.bot.cogs['ClassesCog'].get_class(data['Class']))['Escape']
                l.append(Perso(name=p['personnage'],classe=data['Class'],lvl=p['level'],at1=data['Attaque 1'],at2=data['Attaque 2'],ult=data['Ultime'],pas=data['Passif'],life=life,esquive=esq,Type=data['Type'],passifType=data['type_passif']))
            Team2 = Team(user=user,players=l)
            # Référencement des équipes l'une dans l'autre
            for p in Team1.players:
                p.Team1 = Team1
                p.Team2 = Team2
            for p in Team2.players:
                p.Team1 = Team2
                p.Team2 = Team1
            # Début des tours
            self.bot.log.debug("Début d'un combat entre {u.name} ({u.id}) et {a.name} ({a.id})".format(u=ctx.author,a=user))
            await self.make_tours(ctx,Team1,Team2,tours)

        except Exception as e:
            await self.bot.cogs["ErrorsCog"].on_command_error(ctx,e)
        self.in_combat.remove(ctx.author)
        self.in_combat.remove(user)



    async def apply_passifs(self,Team1:Team,Team2:Team):
        """Ajoute les passifs aux personnages"""
        for p in Team1.players:
            if p.passifType != 'A':
                continue
            await self.apply_one_passif(p)
        for p in Team2.players:
            if p.passifType != 'A':
                continue
            await self.apply_one_passif(p)

    async def apply_one_passif(self,perso):
        """Ajoute le passif d'un perso"""
        try:
            await self.bot.cogs['EffectsCog'].effects[perso.passif](perso)
        except KeyError:
            pass
        except Exception as e:
            raise e
    
    async def do_attack(self,action:list,perso:Perso):
        """Exécute une action"""
        if action[0]=='pass':
            result = '{} passe son tour 🏃'.format(perso.name)
        elif action[0]=='frozen':
            result = '{} est immobilisé, il ne peut rien faire'.format(perso.name)
        elif action[0]=='dead':
            result = '{} est mort, il ne peut rien faire'.format(perso.name)
        else:
            result = await self.bot.cogs['AttacksCog'].attacks[action[0]](perso)
        return result

    async def make_tours(self,ctx:commands.Context,Team1:Team,Team2:Team,tours:int):
        """Fait passer un tour"""
        # Préparation de l'embed
        title = "Combat : {} contre {}".format(Team1.user.display_name,Team2.user.display_name)
        emb = self.bot.cogs['EmbedCog'].Embed(title=title,desc="*Réagissez à ce message pour effectuer une action*",color=self.bot.cogs['Commands'].embed_color,fields=[{'name':'Historique','value':'Début du combat'},{'name':'Equipe 1','value':'None'},{'name':'Equipe 2','value':'None'},{'name':"Action...",'value':'loading...'}])
        msg = None
        # Mélange des personnages
        random.shuffle(Team1.players)
        random.shuffle(Team2.players)
        await self.apply_passifs(Team1, Team2)

        while Team2.rounds<tours:
            if not (Team1.user in self.in_combat or Team2.user in self.in_combat):
                break

            await self.update_status(emb,Team1,Team2)
            if msg != None:
                await msg.delete()
            msg = await ctx.send(embed=emb.discord_embed())
            perso = Team1.players[Team1.nbr]
            result = await self.do_attack(await self.ask_action(msg,emb,perso,Team1.user), perso)
            await ctx.send(result)
            if "passe son tour" in result:
                perso.points += 2
            else:
                perso.points += 1
            await self.add_history(emb,result)
            Team1, Team2 = await self.apply_effects(Team1,Team2)
            for p in Team2.players:
                p.thorny = False
            
            Team1.rounds += 1

            if not (Team1.user in self.in_combat or Team2.user in self.in_combat):
                break

            await self.update_status(emb,Team1,Team2)
            await msg.delete()
            msg = await ctx.send(embed=emb.discord_embed())
            perso = Team2.players[Team2.nbr]
            result = await self.do_attack(await self.ask_action(msg,emb,perso,Team2.user), perso)
            await ctx.send(result)
            if "passe son tour" in result:
                perso.points += 2
            else:
                perso.points += 1
            await self.add_history(emb,result)
            Team2, Team1 = await self.apply_effects(Team2,Team1)
            for p in Team1.players:
                p.thorny = False
            
            Team2.rounds += 1

        await self.update_status(emb,Team1,Team2)
        del emb.fields[3]
        if msg != None:
            await msg.delete()
        msg = await ctx.send(embed=emb.discord_embed())


    async def add_history(self,emb,text):
        """Ajoute un historique"""
        history = emb.fields[0]['value'].replace('**','')
        while len(history+text)>1000:
            history = "\n".join(history.split("\n")[1:])
        emb.fields[0]['value'] = history + "\n**"+text+'**'


    async def create_perso_status(self,p:Perso,emojis:dict):
        life = round(p.life[0], 0 if p.life[0]==int(p.life[0]) else 1)
        if life==0:
            return '{} ({}) : {} K.O.'.format(p.name,p.classe,emojis['ko'])
        text = '{} ({}) : {} {}/{}'.format(p.name,p.classe,emojis['life'],life,p.life[1])
        if "_on_fire" in p.effects.keys() and p.effects['_on_fire'][1]>0:
            text += '{}**|** :fire: {}'.format(emojis['none'],p.effects['_on_fire'][1])
        text += '{}**|** Energie : {}'.format(emojis['none'],p.points)
        if p.shield > 0:
            text += "{}**|**  {} {}".format(emojis['none'],'🛡',p.shield)
        if p.invisible > 0:
            text += "{}**|**  {} {}".format(emojis['none'],emojis['invisible'],p.invisible)
        if p.frozen > 0:
            text += "{}**|**  {} {}".format(emojis['none'],':snowflake:',p.frozen)
        other_effects = [x[0].__doc__ for x in p.effects.values() if x[0].__name__!='on_fire' and x[1]>0]
        if len(other_effects)>0:
            text += "{}**|**  {} {}".format(emojis['none'],emojis['effect'],' '.join(other_effects))
        return text

    async def update_status(self,emb,Team1,Team2):
        """Met à jour l'état des personnages"""
        life_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('legends_heart'))
        none_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('vide'))
        effect_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('effects'))
        ko_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('ko'))
        invisible_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('invisibility'))
        emb.fields[1]['name'] = "Equipe de "+Team1.user.display_name
        text = ""
        emojis_map = {'life':life_emoji,'none':none_emoji,'effect':effect_emoji,'invisible':invisible_emoji,'ko':ko_emoji}
        for p in Team1.players:
            text += "\n"+await self.create_perso_status(p,emojis_map)
        emb.fields[1]['value'] = text

        emb.fields[2]['name'] = "Equipe de "+Team2.user.display_name
        text = ""
        for p in Team2.players:
            text += "\n"+await self.create_perso_status(p,emojis_map)
        emb.fields[2]['value'] = text

    async def ask_action(self,msg,emb,perso,player):
        """Demande à un joueur de choisir une action"""
        if perso.frozen>0:
            perso.frozen -= 1
            return ('frozen',perso)
        if perso.life[0]==0:
            return ('dead',perso)
        attaques = str()
        emojis = list()
        attaques_emojis = [await self.bot.cogs['UtilitiesCog'].get_emoji('attaque1'), await self.bot.cogs['UtilitiesCog'].get_emoji('attaque2'), await self.bot.cogs['UtilitiesCog'].get_emoji('ultime')]
        if True:
            emojis.append(attaques_emojis[0])
            attaques += "{}  {}\n".format(emojis[-1],perso.attaque1)
        if perso.points >= self.costs['attaque2']:
            emojis.append(attaques_emojis[1])
            attaques += "{}  {}\n".format(emojis[-1],perso.attaque2)
        if perso.points >= self.costs['ultime']:
            emojis.append(attaques_emojis[2])
            attaques += "{}  {}\n".format(emojis[-1],perso.ultime)
        if True:
            emojis.append('🏃')
            attaques += '🏃 Passer le tour'
        emb.fields[3] = {'name':"**{}**, choisissez l'action de {}".format(player.display_name,perso.name),'value':attaques,'inline':False}
        await msg.edit(embed=emb.discord_embed())
        for x in emojis:
            await msg.add_reaction(x)
        
        def check(reaction,user):
            return reaction.emoji in emojis and user==player
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            reaction = ('pass',perso)
        else:
            if reaction.emoji==attaques_emojis[0]:
                reaction = (perso.attaque1,perso)
            elif reaction.emoji==attaques_emojis[1]:
                reaction = (perso.attaque2,perso)
            elif reaction.emoji==attaques_emojis[2]:
                reaction = (perso.ultime,perso)
            else:
                reaction = ('pass',perso)
        return reaction


    async def apply_effects(self,Team1,Team2):
        """Applique les effets sur un perso (feu,regen etc)"""
        for player in Team1.players:
            for name, conf in player.effects.items():
                try:
                    if conf[1] == 0:
                        continue
                    await conf[0](player)
                    player.effects[name][1] -= 1
                except Exception as e:
                    await self.bot.cogs['ErrorsCog'].on_error(e,None)
            player.invisible = max(player.invisible-1,0)
        return Team1, Team2


def setup(bot):
    bot.add_cog(CombatCog(bot))