import random
from discord.ext import commands
from math import log, exp


class AttacksCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file = 'attacks'
        try:
            self.add_effects = bot.cogs['EffectsCog'].add_effects
        except KeyError:
            pass
        self.shields_lvl = None
        self.critical = ["C'est un coup critique !","Coup critique !","Wow, quel coup critique !","Il s'agit d'un coup critique !","Coup critique !"]
        self.escape = ["Belle esquive !","Heureusement qu'il a esquivé !","C'est une esquive !"]
        self.attacks = {"Coup laser":self.a_1,
                        "Force protectrice":self.c_1,
                        "Tir de la mort":self.u_1,
                        "Pour les voleurs":self.a_3,
                        "Araignée géante":self.c_3,
                        "Le précieux":self.u_3,
                        "Epée volée":self.a_5,
                        'Hache du Pyrobarbare':self.c_5,
                        "Fus Roh Dah":self.u_5,
                        "Epées rouillées":self.a_9,
                        "Sort de rage":self.c_9,
                        "Renforts aériens":self.u_9,
                        "Se vider les poches":self.a_10,
                        'Avalanche de bière':self.c_10,
                        "Donut atomique":self.u_10,
                        'Boule de froid':self.a_13,
                        'Coup de gel':self.c_13,
                        'Tempête hivernale':self.u_13,
                        'Triple morsure':self.a_16,
                        'Aboiement ténébreux':self.c_16,
                        "Flammes de l'enfer":self.u_16,
                        "Grand coup":self.a_17,
                        'Apparition terrifiante':self.c_17,
                        "Regard mortel":self.u_17,
                        "Couteau d'assassin":self.a_22,
                        'Chara':self.c_22,
                        "Esprit déterminé":self.u_22,
                        "Epée de l'ordre":self.a_24,
                        "Bombe fumigène":self.c_24,
                        "Lame cachée":self.u_24,
                        "Mitraillage fou":self.a_25,
                        "Rire entrainant":self.c_25,
                        "Bombe hilarante":self.u_25,
                        "Gobage":self.a_32,
                        "Chute d'étoile":self.c_32,}
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.add_effects = self.bot.cogs['EffectsCog'].add_effects

    
    async def calc_shield(self,points:int):
        if points == 0:
            return 0
        return round(25.45 * log(points) + 25)
        
    async def attack_with_shield(self,shield_lvl:int,points:int,life:int):
        damage = 0
        if self.shields_lvl==None:
            self.shields_lvl = list()
            for i in range(30):
                self.shields_lvl.append(await self.calc_shield(i))
        sh = self.shields_lvl[shield_lvl] - points
        if sh<0:
            damage -= sh
            shield_lvl = 0
        else:
            for e,i in enumerate(self.shields_lvl):
                if i >= sh:
                    shield_lvl = e-1
                    break
        if life-damage < 0:
            damage = life
        return damage, shield_lvl
    
    async def apply_dmg(self,perso,points:int,attacker,critic:bool=True) -> float:
        if attacker.passifType != 'B':
            await self.bot.cogs['CombatCog'].apply_one_passif(attacker)
        if perso.passifType != 'G':
            await self.bot.cogs['CombatCog'].apply_one_passif(perso)
        if random.randrange(100)<perso.esquive and perso.frozen==0:
            return 0.0
        attack_boost = attacker.attack_bonus
        if perso.type in attacker.attack_bonus_type.keys():
            attack_boost += attacker.attack_bonus_type[perso.type]
        if attacker.passifType == 'B':
            await self.bot.cogs['CombatCog'].apply_one_passif(attacker)
        points += round(points * (attack_boost*0.25),1)
        if critic and random.random() < await self.calc_critic(perso.lvl):
            points += round(random.randint(35,55)/100*points,1)
        damage, perso.shield = await self.attack_with_shield(perso.shield,points,perso.life[0])
        perso.life[0] = max(0,perso.life[0]-damage)
        if perso.thorny:
            damage, attacker.shield = await self.attack_with_shield(attacker.shield,5*log(perso.lvl) + perso.lvl/5,attacker.life[0])
            attacker.life[0] = max(0, attacker.life[0]-damage)
        if perso.passifType != 'H':
            await self.bot.cogs['CombatCog'].apply_one_passif(perso)
        return round(points,None if int(points)==points else 1)
    
    async def calc_critic(self,level) -> float:
        return min(exp(level/100) - 1, 0.85)

    
    async def select_random_players(self,nbr:int,Team:list,avoid_player=None,has_type:str=None,return_index:bool=False) -> list:
        """Sort des joueurs aléatoirement d'une équipe"""
        def rdm_coef(coefs:list) -> int:
            """Choisit un index dans une liste de coefs"""
            target = random.randrange(sum(coefs))
            temp = 0
            i = 0
            while temp<target:
                temp += coefs[i]
                i += 1
            return i

        players = list()
        IDs = list()
        possible_players = [x for x in Team.players if x.invisible==0 and x.life[0]>0 and x!=avoid_player]
        if has_type!=None:
            possible_players = [x for x in possible_players if x.type==has_type]
        while len(players) < min(len(possible_players),nbr):
            t = rdm_coef([x.provocation_coef for x in possible_players])
            if Team.players[t] in players:
                continue
            players.append(Team.players[t])
            IDs.append(t)
        if return_index:
            return players,IDs
        else:
            return players


    async def a_1(self,perso):
        "Coup laser"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],14,perso)
        txt = "{} utilise son sabre laser contre {}, et fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>14:
            txt += random.choice(self.critical)
        elif points<14:
            txt += random.choice(self.escape)
        return txt
    
    async def c_1(self,perso):
        "Force protectrice"
        names = [perso.name]
        perso.shield += 2
        while len(names)<3:
            target = random.choice(perso.Team1.players)
            if target.name in names:
                continue
            target.shield += 1
            names.append(target.name)
        return "{p} protège {t[1]} et {t[2]}, en leur ajoutant 2 points de bouclier".format(p=names[0],t=names)
    
    async def u_1(self,perso):
        "Tir de la mort"
        names = list()
        targets = await self.select_random_players(3,perso.Team2)
        for t in targets:
            await self.apply_dmg(t,22,perso,False)
            await self.add_effects(t,'_on_fire',2)
            names.append(t.name)
        txt =  "{p} envoie son rayon de la mort sur {t[0]}, {t[1]} et {t[2]}, ce qui leur inflige 22 PV de dégâts, et les enflamme !".format(p=perso.name,t=names)
        return txt

    async def a_3(self,perso):
        "Pour les voleurs"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],20,perso)
        txt = "{} attaque {} et lui fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>20:
            txt += random.choice(self.critical)
        elif points<20:
            txt += random.choice(self.escape)
        return txt
    
    async def c_3(self,perso):
        "Araignée géante"
        targets = await self.select_random_players(3,perso.Team2)
        points = await self.apply_dmg(targets[0],22,perso)
        targets[1].frozen += 1
        await self.add_effects(targets[2],'_on_poison',1)
        txt = "{p} invoque une araignée géante, qui fait {d}PV de dégâts sur {t[0]}, immobilise {t[1]} et empoisonne {t[2]} ! ".format(p=perso.name,t=[x.name for x in targets],d=points)
        return txt

    async def u_3(self,perso):
        "Le précieux"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],32,perso)
        perso.invisible += 1
        txt = "{} devient invisible et parvient à faire {} PV de dégâts à {} ! ".format(perso.name,points,target[0].name)
        if points>32:
            txt += random.choice(self.critical)
        elif points<32:
            txt += random.choice(self.escape)
        return txt

    async def a_5(self,perso):
        "Epée volée"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],24,perso)
        txt = "{} utilise son épée contre {}, et fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points > 24:
            txt += random.choice(self.critical)
        elif points<24:
            txt += random.choice(self.escape)
        return txt
    
    async def c_5(self,perso):
        "Hache du Pyrobarbare"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],28,perso)
        await self.add_effects(target[0],'_on_fire',2)
        txt =  "{} utilise sa hache contre {}, et fait {} PV de dégâts en l'enflammant. ".format(perso.name,target[0].name,points)
        if points>28:
            txt += random.choice(self.critical)
        elif points<28:
            txt += random.choice(self.escape)
        return txt
    
    async def u_5(self,perso):
        "Fus Roh Dah"
        targets = await self.select_random_players(2,perso.Team2)
        names = list()
        for t in targets:
            await self.apply_dmg(t,26,perso)
            names.append(t.name)
        return "{p} crie **Fus Roh Dah** à {t[0]}, {t[1]} et {t[2]}, ce qui leur inflige de lourds dégâts !".format(p=perso.name,t=names)

    async def a_9(self,perso):
        "Epées rouillées"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],6*4,perso)
        txt = "La {} se retourne contre {}, lui infligeant {}pv de dégât !".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points<10:
            txt += random.choice(self.escape)
        return txt
    
    async def c_9(self,perso):
        "Sort de rage"
        target = await self.select_random_players(1,perso.Team2)
        target[0].attack_bonus -= 1
        for i in perso.Team1.players:
            i.attack_bonus += 1
        perso.thorny = True
        txt = "La {} utilise un sort de rage, augmentant leurs attaques, et effrayant {} qui voit ses attaques diminuer !".format(perso.name,target[0].name)
        return txt
    
    async def u_9(self,perso):
        "Renforts aériens"
        for i in perso.Team2.players:
            await self.apply_dmg(i,22,perso)
            await self.add_effects(i,'_on_fire',2)
        txt = "Des dragons rejoignent la {} et enflamment l'équipe adverse, leur enlevant 22pv chacun".format(perso.name)
        return txt

    async def a_10(self,perso):
        "Se vider les poches"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],10,perso)
        txt = "{} vide ses poches face à {}, en lui faisant au passage {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points<10:
            txt += random.choice(self.escape)
        return txt
    
    async def c_10(self,perso):
        "Avalanche de bière"
        targets = await self.select_random_players(3,perso.Team2)
        names = list()
        for t in targets:
            await self.apply_dmg(t,18,perso)
            names.append(t.name)
        return "{p} utilise ses stocks de bières contre {t[0]}, {t[1]} et {t[2]}, ce qui leur inflige 18 PV de dégâts !".format(p=perso.name,t=names)
    
    async def u_10(self,perso):
        "Donut atomique"
        await self.bot.cogs['EffectsCog'].regen(perso.Team1.players)
        await self.bot.cogs['EffectsCog'].blessing(perso.Team1.players)
        return "{} utilise son donut atomique et régénère tous ses alliés ! :doughnut: ".format(perso.name)

    async def a_13(self,perso):
        "Boule de froid"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],26,perso)
        txt = "{} envoie une boule de neige sur {}, et fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>26:
            txt += random.choice(self.critical)
        elif points<26:
            txt += random.choice(self.escape)
        return txt
    
    async def c_13(self,perso):
        "Coup de gel"
        targets = await self.select_random_players(3,perso.Team2)
        names = list()
        for t in targets:
            await self.apply_dmg(t,20,perso)
            t.attack_bonus -= 1
            names.append(t.name)
        return "{p} refroidit {t[0]}, {t[1]} et {t[2]}, en faisant de gros dégâts à chacun et réduisant leurs attaques ! (-20pv)".format(p=perso.name,t=names)
    
    async def u_13(self,perso):
        "Tempête hivernale"
        for target in await self.select_random_players(50,perso.Team2):
            points = await self.apply_dmg(target,22,perso)
        target = (await self.select_random_players(1,perso.Team2))[0]
        target.frozen += 1
        target2 = (await self.select_random_players(1,perso.Team2,avoid_player=target))[0]
        await self.add_effects(target2,'_on_bleeding',2)
        txt = "{p} lance une tempête affectant toute l'équipe ennemie, qui se retrouve avec {s} PV en moins ! La tempête gèle aussi {t} et blesse {t2}".format(p=perso.name,t=target.name,s=points,t2=target2.name)
        return txt
    
    async def a_16(self,perso):
        "Triple morsure"
        target = await self.select_random_players(1,perso.Team2)
        pts = await self.apply_dmg(target[0],14,perso)
        return "{} attaque avec ses trois têtes sur {} et lui cause {}pv de dégâts !".format(perso.name,target[0].name,pts)
    
    async def c_16(self,perso):
        "Aboiement ténébreux"
        targets = await self.select_random_players(3,perso.Team2)
        for t in targets:
            await self.apply_dmg(t,20,perso)
        perso.provocation_coef += 1
        return "{p} utilise son aboiement pour effayer l'équipe adverse, ce qui fait besser les attaques de  {t[0]}, {t[1]} et {t[2]} !".format(p=perso.name,t=[x.name for x in targets])
    
    async def u_16(self,perso):
        "Flammes de l'enfer"
        for target in await self.select_random_players(50,perso.Team2):
            await self.add_effects(perso.Team2.players[target],'_on_fire',3)
            await self.apply_dmg(perso.Team2.players[target],12,perso,False)
        return "{p} enflamme l'équipe adverse, réduisant leurs PV de 12 points !".format(p=perso.name)

    async def a_17(self,perso):
        "Grand coup"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],22,perso)
        txt = "{} porte un coup à {}, et fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>22:
            txt += random.choice(self.critical)
        elif points<22:
            txt += random.choice(self.escape)
        return txt

    async def c_17(self,perso):
        "Apparition terrifiante"
        target = await self.select_random_players(1,perso.Team2)
        target[0].frozen += 1
        return "{p} apparaît brusquement devant {t}. Le pauvre appeuré est immobile pendant 1 tour".format(p=perso.name,t=target[0].name)
    
    async def u_17(self,perso):
        "Regard mortel"
        target =await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],36,perso)
        txt = "{} porte un coup à {}, et fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>36:
            txt += random.choice(self.critical)
        elif points<36:
            txt += random.choice(self.escape)
        return txt

    async def a_22(self,perso):
        "Couteau d'assassin"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],10,perso)
        txt = "{} utilise ses outils tranchants sur {}, et fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points<10:
            txt += random.choice(self.escape)
        return txt

    async def c_22(self,perso):
        "Chara"
        perso.attack_bonus += 1
        perso.esquive += 20
        perso.thorny = True
        return "{p} reçoit une augmentation soudaine de ses statistiques, lui apportant un bonus d'attaque et d'esquive".format(p=perso.name)
    
    async def u_22(self,perso):
        "Esprit déterminé"
        for i in await self.select_random_players(50,perso.Team1,avoid_player=perso):
            i.shield += 1
            i.esquive += 30
        return "{}, déterminé comme jamais, renforce le bouclier de tous ses alliés".format(perso.name)

    async def a_24(self,perso):
        "Epée de l'ordre"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],20,perso)
        txt = "{} utilise son épée sur {}, et fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>20:
            txt += random.choice(self.critical)
        elif points<20:
            txt += random.choice(self.escape)
        return txt

    async def c_24(self,perso):
        "Bombe fumigène"
        victimes = list()
        for player in await self.select_random_players(3,perso.Team2):
            player.attack_bonus -= 1
            player.esquive -= 15
            victimes.append(player.name)
        if len(victimes) == 3:
            txt = "{} utilise une bombe fumigène sur {}, {} et {}, en réduisant leurs bonus d'attaque et d'esquive".format(perso.name,victimes[0],victimes[1],victimes[2])
        elif len(victimes)==2:
            txt = "{} utilise une bombe fumigène sur {} et {}, en réduisant leurs bonus d'attaque et d'esquive".format(perso.name,victimes[0],victimes[1])
        else:
            txt = "{} utilise une bombe fumigène sur {}, en réduisant ses bonus d'attaque et d'esquive".format(perso.name,victimes[0])
        return txt
    
    async def u_24(self,perso):
        "Lame cachée"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],34,perso)
        perso.invisible += 1
        txt = "{} utilise ses pouvoirs magiques et fait {} PV de dégâts à {} ".format(perso.name,points,target[0].name)
        if points>34:
            txt += random.choice(self.critical)
        elif points<34:
            txt += random.choice(self.escape)
        return txt

    async def a_25(self,perso):
        "Mitraillage fou"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],26,perso)
        txt = "{} utilise sa mitraillette sur {} et lui fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points<10:
            txt += random.choice(self.escape)
        return txt
    
    async def c_25(self,perso):
        "Rire entrainant"
        targets1 = await self.select_random_players(2,perso.Team1,avoid_player=perso)
        for i in targets1:
            i.attack_bonus += 1
        targets2 = await self.select_random_players(3,perso.Team2)
        for i in targets2:
            i.attack_bonus += 1
        perso.attack_bonus += 1
        txt = "{p} éclate de rire, ce qui a pour effet d'augmenter les attaques de lui et de ses alliés {a[0]} et {a[1]}, ainsi que de diminuer celles de {t[0]}, {t[1]} et {t[2]} ! ".format(p=perso.name,a=[x.name for x in targets1],t=[x.name for x in targets2])
        return txt
    
    async def u_25(self,perso):
        "Bombe hilarante"
        for target in await self.select_random_players(50,perso.Team2):
            await self.apply_dmg(target,26,perso)
            await self.add_effects(target,'_on_poison',2)
        txt = "{p} lance une bombe sur ses ennemis, leurs faisant de lourds dégâts et les empoisonnant pour 2 tours".format(p=perso.name)
        return txt

    async def a_32(self,perso):
        "Gobage"
        target = await self.select_random_players(1,perso.Team2)
        if len(target)==0:
            return "{} n'a plus aucun adversaire à combattre !".format(perso.name)
        points = await self.apply_dmg(target[0],14,perso)
        txt = "{} attaque {} et lui fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>14:
            txt += random.choice(self.critical)
        elif points<14:
            txt += random.choice(self.escape)
        return txt

    async def c_32(self,perso):
        "Chute d'étoile"
        targets = await self.select_random_players(2,perso.Team2)
        if len(targets)==0:
            return "{} n'a plus aucun adversaire à combattre !".format(perso.name)
        for t in targets:
            points = await self.apply_dmg(t,10,perso)
        txt = "{} attaque {} et {}, ce qui fait baisser leurs PV de {} points ".format(perso.name,targets[0].name,targets[1].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points<10:
            txt += random.choice(self.escape)
        allys,_ = await self.select_random_players(2,perso.Team1,avoid_player=perso)
        for a in allys+[perso]:
            a.shield += 1
        return txt

    async def u_32(self,perso):
        "Absorption de pouvoir"
        target = await self.select_random_players(2,perso.Team2)
        if len(target)==0:
            return "{} n'a plus aucun adversaire à combattre !".format(perso.name)
        txt = "{} absorbe l'ultime de {} pour l'utiliser contre {} !\n".format(perso.name,target[0].name,target[1].name)
        txt += await self.attacks[target[0].ultime](perso)
        return txt


    async def a_0(self,perso):
        "Exemple"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(perso.Team2.players[target],10,perso)
        perso.invisible += 1
        txt = "{} utilise ses pouvoirs magiques sur {} et fait {} PV de dégâts ! ".format(perso.name,perso.Team2.players[target].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points<10:
            txt += random.choice(self.escape)
        return txt


def setup(bot):
    bot.add_cog(AttacksCog(bot))