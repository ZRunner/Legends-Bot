from typing import Tuple, TYPE_CHECKING
from nextcord.ext import commands
import nextcord
import asyncio
import random
from fcts.classes import Team, Perso
from libs.views import ChooseCharacters, ChooseOpponent

if TYPE_CHECKING:
    from utils import LegendsBot


class FightModule:
    def __init__(self, bot: "LegendsBot"):
        self.bot = bot
        self.in_combat = list()
        self.costs = {'attaque2': 3, 'ultime': 6}
    

    async def begin(self, inter: nextcord.Interaction, tours:int):
        """Attend un début de partie"""
        if tours < 2:
            return await inter.send(await self.bot._(inter, 'combat.preparation.invalid-tours', user=inter.user.mention, min=2), ephemeral=True)
        if inter.user in self.in_combat:
            return await inter.send(await self.bot._(inter, 'combat.preparation.already-in', user=inter.user.mention), ephemeral=True)
        play1_deck: dict[int, dict] = await self.bot.cogs['UsersCog'].get_user_deck(inter.user.id)
        if len(play1_deck) < 5:
            return await inter.send(await self.bot._(inter, 'combat.preparation.too-few', user=inter.user.mention), ephemeral=True)
        
        self.in_combat.append(inter.user)
        join_view = ChooseOpponent(self.bot, inter)
        await join_view.init()
        msg_ = await self.bot._(inter, 'combat.preparation.preparing', user=inter.user.mention)
        await inter.send(msg_, view=join_view)
        timeouted = await join_view.wait()
        if timeouted:
            # no one answered
            self.in_combat.remove(inter.user)
            await inter.send(await self.bot._(inter, 'combat.preparation.too-late', user=inter.user.mention), ephemeral=True)
            await join_view.disable(inter)
            return
        if not join_view.player:
            # fight got cancelled
            self.in_combat.remove(inter.user)
            return
        await join_view.disable(inter)
        
        player1: nextcord.User = inter.user
        player2: nextcord.User = join_view.player
        self.in_combat.append(player2)
        play2_deck: dict[int, dict] = await self.bot.cogs['UsersCog'].get_user_deck(player2.id)

        await inter.send(await self.bot._(inter, 'combat.preparation.user-joined', user=player2.mention))
        # Sélection des personnages
        try:
            play1_players = []
            play2_players = []
            if len(play1_deck) == 5:
                play1_players = [x for x in play1_deck.values()]
            else:
                play1_select = ChooseCharacters(self.bot, inter, player1.id)
                await play1_select.init()
                await inter.send(await self.bot._(inter, "combat.choice.select", user=player1.mention), view=play1_select)
                await play1_select.wait()
                if len(play1_select.team) == 0:
                    self.in_combat.remove(player1)
                    self.in_combat.remove(player2)
                    return
                play1_players = play1_select.team
            if len(play2_deck) == 5:
                play2_players = [x for x in play2_deck.values()]
            else:
                play2_select = ChooseCharacters(self.bot, inter, player2.id)
                await play2_select.init()
                await inter.send(await self.bot._(inter, "combat.choice.select", user=player2.mention), view=play2_select)
                await play2_select.wait()
                if len(play2_select.team) == 0:
                    self.in_combat.remove(player1)
                    self.in_combat.remove(player2)
                    return
                play2_players = play2_select.team

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
                l.append(Perso(name=p['personnage'],classe=data['Class'],lvl=lvl,at1=data['Attaque 1'],at2=data['Attaque 2'],ult=data['Ultime'],pas=data['Passif'],life=life,dodge=esq,Type=data['Type'],passifType=data['type_passif']))
            Team1 = Team(user=inter.user,players=l)
            # Création de l'équipe 2
            l = list()
            for p in play2_players:
                data = PCog[p['personnage']]
                lvl = await self.bot.get_cog("UtilitiesCog").calc_level(p['xp'])
                life = await self.bot.cogs['PersosCog'].calc_life(data,lvl)
                esq = (await self.bot.cogs['ClassesCog'].get_class(data['Class']))['Escape']
                l.append(Perso(name=p['personnage'],classe=data['Class'],lvl=lvl,at1=data['Attaque 1'],at2=data['Attaque 2'],ult=data['Ultime'],pas=data['Passif'],life=life,dodge=esq,Type=data['Type'],passifType=data['type_passif']))
            Team2 = Team(user=player2,players=l)
            # Référencement des équipes l'une dans l'autre
            for p in Team1.players:
                p.Team1 = Team1
                p.Team2 = Team2
            for p in Team2.players:
                p.Team1 = Team2
                p.Team2 = Team1
            # Début des tours
            self.bot.log.debug("Début d'un combat entre {u.name} ({u.id}) et {a.name} ({a.id})".format(u=inter.user,a=player2))
            await self.make_tours(inter,Team1,Team2,tours)

        except Exception as e:
            await self.bot.cogs["ErrorsCog"].on_interaction_error(inter, e)
        self.in_combat.remove(inter.user)
        self.in_combat.remove(player2)



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

    async def do_attack(self, ctx:commands.Context, action:str, perso:Perso) -> Tuple[str, str, bool]:
        """Exécute une action"""
        did_something = False
        await perso.effects.execute(perso, 'before_action')
        if action=='pass':
            result = await self.bot._(ctx, 'combat.attacks.passed', user=perso.name)
        elif action=='frozen':
            result = await self.bot._(ctx, 'combat.attacks.frozen', user=perso.name)
        elif action=='dead':
            result = await self.bot._(ctx, 'combat.attacks.dead', user=perso.name)
        else:
            await perso.effects.execute(perso, 'before_attack')
            result = await self.bot.cogs['AttacksCog'][action](perso)
            await perso.effects.execute(perso, 'after_attack')
            did_something = True
        return action, result, did_something

    async def make_tours(self, inter: nextcord.Interaction, Team1:Team, Team2:Team, tours:int):
        """Fait passer un tour"""
        # Préparation de l'embed
        title = await self.bot._(inter, 'combat.embed.title', user1=Team1.user.display_name, user2=Team2.user.display_name)
        desc = await self.bot._(inter, 'combat.embed.desc')
        f1_v= await self.bot._(inter, 'combat.embed.history')
        f1_k= await self.bot._(inter, 'combat.embed.beginning')
        loading = await self.bot._(inter, 'combat.embed.loading')
        emb = self.bot.cogs['EmbedCog'].Embed(title=title,desc=desc,color=self.bot.cogs['Commands'].embed_color,fields=[{'name':f1_v,'value':f1_k},{'name':loading,'value':'None'},{'name':'\u200b','value':'\u200b'},{'name':loading,'value':'None'},{'name':'\u200b','value':'\u200b'},{'name':loading,'value':loading}])
        msg = None
        result = str()
        need_update = True
        can_del_reactions = inter.channel.permissions_for(inter.guild.me).manage_messages
        # Mélange des personnages
        random.shuffle(Team1.players)
        random.shuffle(Team2.players)
        await self.apply_passifs(Team1, Team2)
        def check_cond():
            if isinstance(tours, int):
                return Team2.rounds > tours
            return any([x.life[0] > 0 for x in Team1.players]) and any([x.life[0] > 0 for x in Team2.players])
        
        async def send_embed(msg:nextcord.Message, emb, sentence:str, need_update:bool):
            if need_update or msg is None or not can_del_reactions:
                if msg:
                    await msg.delete()
                if sentence:
                    await inter.send(sentence)
                return await inter.send(embed=emb)
            else:
                await msg.edit(embed=emb)
                await msg.clear_reactions()
                return msg

        while check_cond():
            if not (Team1.user in self.in_combat or Team2.user in self.in_combat):
                break

            await self.update_status(inter, emb, Team1, Team2)
            msg = await send_embed(msg, emb, result, need_update)
            perso = Team1.players[Team1.nbr] # sélection du personnage
            # on applique les effets sur ce perso
            await self.apply_effects(perso)
            # l'utilisateur choisit l'action, et on l'exécute
            action, result, need_update = await self.do_attack(inter, await self.ask_action(msg,emb,perso,Team1.user), perso)
            await perso.effects.execute(perso, 'after_action')
            if action == 'pass':
                perso.points += 2
            elif need_update or action == "freeze":
                perso.points += 1
            # on ajoute le résultat à l'historique
            await self.add_history(emb,result)
            # on enlève les effets thorny de l'équipe adverse
            for p in Team2.players:
                await p.effects.execute(p, 'instant')
            
            Team1.rounds += 1 # incrémentation du nombre de tours

            if not (Team1.user in self.in_combat or Team2.user in self.in_combat):
                break

            await self.update_status(inter, emb, Team1, Team2)
            msg = await send_embed(msg, emb, result, need_update)
            perso = Team2.players[Team2.nbr] # sélection du personnage
            # on applique les effets sur ce perso
            await self.apply_effects(perso)
            # l'utilisateur choisit l'action, et on l'exécute
            action, result, need_update = await self.do_attack(inter, await self.ask_action(msg,emb,perso,Team2.user), perso)
            await perso.effects.execute(perso, 'after_action')
            if action == 'pass':
                perso.points += 2
            elif need_update or action == "freeze":
                perso.points += 1
            # on ajoute le résultat à l'historique
            await self.add_history(emb,result)
            # on enlève les effets thorny de l'équipe adverse
            for p in Team1.players:
                await p.effects.execute(p, 'instant')
            
            Team2.rounds += 1 # incrémentation du nombre de tours

        winner = Team1 if Team2.lost else Team2
        await self.add_history(emb, await self.bot._(inter, 'combat.embed.winner', user=winner.user))
        await self.update_status(inter, emb, Team1, Team2)
        del emb.fields[-1]
        # if msg != None:
        #     await msg.delete()
        # msg = await inter.send(embed=emb)
        await send_embed(msg, emb, result, True)


    async def add_history(self,emb,text):
        """Ajoute un historique"""
        history = emb.fields[0]['value'].replace('**','')
        while len(history+text)>1000:
            history = "\n".join(history.split("\n")[1:])
        emb.fields[0]['value'] = history + "\n- **"+text+'**'


    async def create_perso_status(self, p:Perso, emojis:dict):
        life = round(p.life[0], None if p.life[0]==int(p.life[0]) else 1)
        if life == 0:
            return '{} ({}) : {} K.O.'.format(p.name,p.classe,emojis['ko'])
        text = '{} ({}) : {} {}/{}'.format(p.name,p.classe,emojis['life'],life,p.life[1])
        text += '{}**|** {} {}'.format(emojis['none'], emojis['energy'], p.points)
        other_effects = list()
        attack_bonus = p.attack_bonus()
        critic_bonus = p.critical
        shield_bonus = p.shield_boost
        for e in p.effects.array:
            if e.name in ('attack_bonus', 'critical_bonus', 'shield_bonus', 'shield_malus'):
                continue
            if e.emoji and e.duration > 0:
                emoji = e.emoji if isinstance(e.emoji, str) else str(self.bot.get_emoji(e.emoji))
                text += '{}**|** {} {}'.format(emojis['none'], emoji, e.duration)
            else:
                other_effects.append(e.name)
        if shield_bonus > 0:
            text += "{}**|** {} {}".format(emojis['none'],'🛡', shield_bonus)
        if shield_bonus < 0:
            text += "{}**|** {} {}".format(emojis['none'],emojis['shield_less'], shield_bonus)
        if attack_bonus > 0:
            text += "{}**|** {} {}".format(emojis['none'],emojis['att_boost'], attack_bonus)
        elif attack_bonus < 0:
            text += "{}**|** {} {}".format(emojis['none'],emojis['att_less'], attack_bonus)
        if critic_bonus != 0:
            text += "{}**|** {} {}".format(emojis['none'],':anger:',critic_bonus)
        if len(other_effects)>0:
            text += "{}**|** {} {}".format(emojis['none'], emojis['effect'], ' '.join(other_effects))
        return text

    async def update_status(self, ctx: commands.Context, emb, Team1, Team2):
        """Met à jour l'état des personnages"""
        get_emoji = self.bot.cogs['UtilitiesCog'].get_emoji
        life_emoji = str(await get_emoji('legends_heart'))
        none_emoji = str(await get_emoji('vide'))
        effect_emoji = str(await get_emoji('effects'))
        ko_emoji = str(await get_emoji('ko'))
        invisible_emoji = str(await get_emoji('invisible'))
        blood_emoji = str(await get_emoji('bleed'))
        poison_emoji = str(await get_emoji('poison'))
        att_boost = str(await get_emoji('att_boost'))
        att_less = str(await get_emoji('att_less'))
        shield_less = str(await get_emoji('shield_less'))
        energy = str(await get_emoji('energy'))
        emb.fields[1]['name'] = await self.bot._(ctx, 'combat.embed.team', user=Team1.user.display_name)
        text = list()
        emojis_map = {'life':life_emoji,'none':none_emoji,'effect':effect_emoji,'invisible':invisible_emoji,'ko':ko_emoji, 'blood':blood_emoji,'poison':poison_emoji, 'att_boost':att_boost, 'att_less':att_less, 'shield_less': shield_less, 'energy': energy}
        for p in Team1.players:
            text.append(await self.create_perso_status(p,emojis_map))
        if len("\n".join(text)) > 1024:
            m = len(text)//2 + 1
            emb.fields[1]['value'] = "\n".join(text[:m])
            emb.fields[2]['value'] = "\n".join(text[m:])
        else:
            emb.fields[1]['value'] = "\n".join(text)
            emb.fields[2]['value'] = '\u200b'

        emb.fields[3]['name'] = await self.bot._(ctx, 'combat.embed.team', user=Team2.user.display_name)
        text.clear()
        for p in Team2.players:
            text.append(await self.create_perso_status(p,emojis_map))
        if len("\n".join(text)) > 1024:
            m = len(text)//2 +1 
            emb.fields[3]['value'] = "\n".join(text[:m])
            emb.fields[4]['value'] = "\n".join(text[m:])
        else:
            emb.fields[3]['value'] = "\n".join(text)
            emb.fields[4]['value'] = '\u200b'

    async def ask_action(self, msg, emb, perso, player) -> str:
        """Demande à un joueur de choisir une action"""
        if perso.frozen:
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
            attaques += await self.bot._(msg.channel, 'combat.attacks.pass', e='🏃')
        emb.fields[5] = {'name':await self.bot._(msg.channel, 'combat.embed.choose', user=player.display_name, perso=perso.name),'value':attaques,'inline':False}
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


    async def apply_effects(self, player:Perso):
        """Applique les effets sur un perso (feu,regen etc)"""
        await player.effects.execute(player, 'end_turn')
        player.effects.clean()
        # if player.invisible > 0:
        #     player.invisible = max(player.invisible-1, 0)
