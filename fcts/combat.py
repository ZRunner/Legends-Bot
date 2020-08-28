from discord.ext import commands
import discord
import asyncio
import random
from fcts.classes import Team, Perso


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
                if len(play1_players) == 0:
                    self.in_combat.remove(ctx.author)
                    self.in_combat.remove(user)
                    return
            if len(play2_deck)==5:
                play2_players = [x for x in play2_deck.values()]
            else:
                play2_players = await self.select_team(user,ctx.channel,play2_deck)
                if len(play2_players) == 0:
                    self.in_combat.remove(ctx.author)
                    self.in_combat.remove(user)
                    return
            # Création de l'équipe 1
            l = list()
            PCog = self.bot.cogs['PersosCog'].data
            if len(PCog) == 0:
                PCog = await self.bot.cogs['PersosCog'].get_data()
            for p in play1_players:
                data = PCog[p['personnage']]
                lvl = await self.bot.get_cog("UtilitiesCog").calc_level(p['xp'])
                life = await self.bot.cogs['PersosCog'].calc_life(data, lvl)
                esq = (await self.bot.cogs['ClassesCog'].get_class(data['Class']))['Escape']
                l.append(Perso(name=p['personnage'],classe=data['Class'],lvl=lvl,at1=data['Attaque 1'],at2=data['Attaque 2'],ult=data['Ultime'],pas=data['Passif'],life=life,esquive=esq,Type=data['Type'],passifType=data['type_passif']))
            Team1 = Team(user=ctx.author,players=l)
            # Création de l'équipe 2
            l = list()
            for p in play2_players:
                data = PCog[p['personnage']]
                lvl = await self.bot.get_cog("UtilitiesCog").calc_level(p['xp'])
                life = await self.bot.cogs['PersosCog'].calc_life(data,lvl)
                esq = (await self.bot.cogs['ClassesCog'].get_class(data['Class']))['Escape']
                l.append(Perso(name=p['personnage'],classe=data['Class'],lvl=lvl,at1=data['Attaque 1'],at2=data['Attaque 2'],ult=data['Ultime'],pas=data['Passif'],life=life,esquive=esq,Type=data['Type'],passifType=data['type_passif']))
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
            # await self.bot.cogs['EffectsCog'].effects[perso.passif](perso)
            pass
        except KeyError:
            pass
        except Exception as e:
            raise e
    
    async def do_attack(self, action:list, perso:Perso):
        """Exécute une action"""
        did_something = False
        if action=='pass':
            result = '{} passe son tour 🏃'.format(perso.name)
        elif action=='frozen':
            result = '{} est immobilisé, il ne peut rien faire :snowflake:'.format(perso.name)
        elif action=='dead':
            result = '{} est mort, il ne peut rien faire'.format(perso.name)
        else:
            result = await self.bot.cogs['AttacksCog'][action](perso)
            did_something = True
        return result, did_something

    async def make_tours(self, ctx:commands.Context, Team1:Team, Team2:Team, tours:int):
        """Fait passer un tour"""
        # Préparation de l'embed
        title = "Combat : {} contre {}".format(Team1.user.display_name,Team2.user.display_name)
        emb = self.bot.cogs['EmbedCog'].Embed(title=title,desc="*Réagissez à ce message pour effectuer une action*",color=self.bot.cogs['Commands'].embed_color,fields=[{'name':'Historique','value':'Début du combat'},{'name':'Equipe 1','value':'None'},{'name':'Equipe 2','value':'None'},{'name':"Action...",'value':'loading...'}])
        msg = None
        need_update = True
        can_del_reactions = ctx.channel.permissions_for(ctx.guild.me).manage_messages
        # Mélange des personnages
        random.shuffle(Team1.players)
        random.shuffle(Team2.players)
        await self.apply_passifs(Team1, Team2)
        def check_cond():
            if isinstance(tours, int):
                return Team2.rounds > tours
            return any([x.life[0] > 0 for x in Team1.players]) and any([x.life[0] > 0 for x in Team2.players])
        
        async def send_embed(msg, emb, need_update):
            if need_update or msg is None or not can_del_reactions:
                if msg:
                    await msg.delete()
                return await ctx.send(embed=emb)
            else:
                await msg.edit(embed=emb)
                return msg

        while check_cond():
            if not (Team1.user in self.in_combat or Team2.user in self.in_combat):
                break

            await self.update_status(emb,Team1,Team2)
            # if msg != None:
            #     await msg.delete()
            # msg = await ctx.send(embed=emb.discord_embed())
            msg = await send_embed(msg, emb, need_update)
            perso = Team1.players[Team1.nbr]
            result, need_update = await self.do_attack(await self.ask_action(msg,emb,perso,Team1.user), perso)
            await ctx.send(result)
            if "passe son tour" in result:
                perso.points += 2
            else:
                perso.points += 1
            await self.add_history(emb,result)
            await self.apply_effects(Team1)
            for p in Team2.players:
                p.thorny = False
            
            Team1.rounds += 1

            if not (Team1.user in self.in_combat or Team2.user in self.in_combat):
                break

            await self.update_status(emb,Team1,Team2)
            # await msg.delete()
            # msg = await ctx.send(embed=emb.discord_embed())
            msg = await send_embed(msg, emb, need_update)
            perso = Team2.players[Team2.nbr]
            result, need_update = await self.do_attack(await self.ask_action(msg,emb,perso,Team2.user), perso)
            await ctx.send(result)
            if "passe son tour" in result:
                perso.points += 2
            else:
                perso.points += 1
            await self.add_history(emb,result)
            await self.apply_effects(Team2)
            for p in Team1.players:
                p.thorny = False
            
            Team2.rounds += 1

        await self.update_status(emb,Team1,Team2)
        del emb.fields[3]
        # if msg != None:
        #     await msg.delete()
        # msg = await ctx.send(embed=emb)
        await send_embed(msg, emb, True)


    async def add_history(self,emb,text):
        """Ajoute un historique"""
        history = emb.fields[0]['value'].replace('**','')
        while len(history+text)>1000:
            history = "\n".join(history.split("\n")[1:])
        emb.fields[0]['value'] = history + "\n**"+text+'**'


    async def create_perso_status(self,p:Perso,emojis:dict):
        life = round(p.life[0], None if p.life[0]==int(p.life[0]) else 1)
        if life == 0:
            return '{} ({}) : {} K.O.'.format(p.name,p.classe,emojis['ko'])
        text = '{} ({}) : {} {}/{}'.format(p.name,p.classe,emojis['life'],life,p.life[1])
        text += '{}**|** Energie : {}'.format(emojis['none'],p.points)
        other_effects = list()
        for e in p.effects.array:
            if e.emoji:
                text += '{}**|** {} {}'.format(emojis['none'], e.emoji, e.duration)
            else:
                other_effects.append(e.name)
        if p.shield > 0:
            text += "{}**|** {} {}".format(emojis['none'],'🛡',p.shield)
        if p.invisible > 0:
            text += "{}**|** {} {}".format(emojis['none'],emojis['invisible'],p.invisible)
        if p.frozen > 0:
            text += "{}**|** {} {}".format(emojis['none'],':snowflake:',p.frozen)
        used_effects = ('on_fire', 'on_bleeding','on_poison')
        if len(other_effects)>0:
            text += "{}**|** {} {}".format(emojis['none'], emojis['effect'], ' '.join(other_effects))
        return text

    async def update_status(self,emb,Team1,Team2):
        """Met à jour l'état des personnages"""
        life_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('legends_heart'))
        none_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('vide'))
        effect_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('effects'))
        ko_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('ko'))
        invisible_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('invisible'))
        blood_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('bleed'))
        poison_emoji = str(await self.bot.cogs['UtilitiesCog'].get_emoji('poison'))
        emb.fields[1]['name'] = "Equipe de "+Team1.user.display_name
        text = ""
        emojis_map = {'life':life_emoji,'none':none_emoji,'effect':effect_emoji,'invisible':invisible_emoji,'ko':ko_emoji, 'blood':blood_emoji,'poison':poison_emoji}
        for p in Team1.players:
            text += "\n"+await self.create_perso_status(p,emojis_map)
        emb.fields[1]['value'] = text[:1024]

        emb.fields[2]['name'] = "Equipe de "+Team2.user.display_name
        text = ""
        for p in Team2.players:
            text += "\n"+await self.create_perso_status(p,emojis_map)
        emb.fields[2]['value'] = text[:1024]

    async def ask_action(self, msg, emb, perso, player):
        """Demande à un joueur de choisir une action"""
        if perso.frozen > 0:
            perso.frozen -= 1
            return 'frozen'
        if perso.life[0] == 0:
            return 'dead'
        attaques = str()
        emojis = list()
        attaques_emojis = [await self.bot.cogs['UtilitiesCog'].get_emoji('attaque1'), await self.bot.cogs['UtilitiesCog'].get_emoji('attaque2'), await self.bot.cogs['UtilitiesCog'].get_emoji('ultime')]
        if True:
            emojis.append(attaques_emojis[0])
            attaques += "{}  {}\n".format(emojis[-1], perso.attaque1)
        if perso.points >= self.costs['attaque2']:
            emojis.append(attaques_emojis[1])
            attaques += "{}  {}\n".format(emojis[-1], perso.attaque2)
        if perso.points >= self.costs['ultime']:
            emojis.append(attaques_emojis[2])
            attaques += "{}  {}\n".format(emojis[-1], perso.ultime)
        if True:
            emojis.append('🏃')
            attaques += '🏃 Passer le tour'
        emb.fields[3] = {'name':"**{}**, choisissez l'action de {}".format(player.display_name,perso.name),'value':attaques,'inline':False}
        await msg.edit(embed=emb)
        for x in emojis:
            await msg.add_reaction(x)
        
        def check(reaction,user):
            return reaction.emoji in emojis and user==player

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            reaction = 'pass'
        else:
            if reaction.emoji == attaques_emojis[0]:
                reaction = perso.attaque1
            elif reaction.emoji == attaques_emojis[1]:
                reaction = perso.attaque2
                perso.points -= self.costs['attaque2']
            elif reaction.emoji == attaques_emojis[2]:
                reaction = perso.ultime
                perso.points -= self.costs['ultime']
            else:
                reaction = 'pass'
        return reaction


    async def apply_effects(self,Team1):
        """Applique les effets sur un perso (feu,regen etc)"""
        for player in Team1.players:
            await player.effects.execute(player, 'end_turn')
            player.effects.clean()
            player.invisible = max(player.invisible-1, 0)


def setup(bot):
    bot.add_cog(CombatCog(bot))