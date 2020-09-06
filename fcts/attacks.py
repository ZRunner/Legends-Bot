import random
from discord.ext import commands
from math import log, exp


class AttacksCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file = 'attacks'
        self.shields_lvl = None
        self.critical = ["C'est un coup critique !","Coup critique !","Wow, quel coup critique !","Il s'agit d'un coup critique !","Coup critique !"]
        self.escape = ["Belle esquive !","Heureusement qu'il a esquivé !","C'est une esquive !"]
        self.attacks = {"Coup laser":self.a_1,
                        "Force protectrice":self.c_1,
                        "Tir de la mort":self.u_1,
                        "Pour les voleurs":self.a_3,
                        "Araignée géante":self.c_3,
                        "Le précieux":self.u_3,
                        "Doigt pistolet":self.a_4,
                        "Bonus tactique":self.c_4,
                        "Déluge de lait":self.u_4,
                        "Hache volée":self.a_5,
                        "Cri destructeur":self.c_5,
                        "Déferlante de magie":self.u_5,
                        "Main mutée":self.a_6,
                        "Corps acide":self.c_6,
                        "Seconde bouche":self.u_6,
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
                        "Découpe souriante":self.a_25,
                        "Rire inarrêtable":self.c_25,
                        "Représentation spectaculaire":self.u_25,
                        "Gobage":self.a_32,
                        "Chute d'étoile":self.c_32,}
        
    def __getitem__(self, key):
        if key in self.attacks:
            return self.attacks[key]
        async def t(*args, **kwargs):
            return "Attaque non codée"
        return t
    
    async def add_effect(self, *args, **kwargs):
       await self.bot.cogs['EffectsCog'].add_effect(*args, **kwargs)

    async def merge_names(self,names:list) -> str:
        if len(names) == 0:
            return "personne"
        if not isinstance(names[0],str):
            names = [x.name for x in names]
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return names[0] + " et " + names[1]
        else:
            return ", ".join(names[:-2]) + " et "+ names[-1]
    
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
        if random.randrange(100) < perso.esquive and perso.frozen == 0:
            return 0
        attack_boost = attacker.attack_bonus(perso.type)
        print(perso.name, attack_boost)
        if attacker.passifType == 'B':
            await self.bot.cogs['CombatCog'].apply_one_passif(attacker)
        points += round(points * (attack_boost*0.25),1)
        if critic and random.random() < await self.calc_critic(perso.lvl):
            points += round(random.randint(20,30)/100*points,1)
        damage, perso.shield = await self.attack_with_shield(perso.shield,points,perso.life[0])
        perso.life[0] = max(0,perso.life[0]-damage)
        if perso.thorny:
            damage, attacker.shield = await self.attack_with_shield(attacker.shield,5*log(perso.lvl) + perso.lvl/5,attacker.life[0])
            attacker.life[0] = max(0, attacker.life[0]-damage)
        if perso.passifType != 'H':
            await self.bot.cogs['CombatCog'].apply_one_passif(perso)
        return round(points, None if int(points) == points else 1)
    
    async def calc_critic(self,level) -> float:
        #return min(exp(level/100) - 1, 0.85)
        return 0.1

    
    async def select_random_players(self, nbr:int, Team:list, avoid_player=None, has_type:str=None, return_index:bool=False, evil:bool=True) -> list:
        """Sort des joueurs aléatoirement d'une équipe"""
        if not evil:
            possible_players = [x for x in Team.players if x.life[0] > 0 and x != avoid_player]
            nbr = min(nbr, len(possible_players))
            if len(possible_players) == nbr:
                players = possible_players
            else:
                random.shuffle(possible_players)
                players = possible_players[:nbr]
            if return_index:
                return players, [x.id for x in players]
            return players

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
        if len([1 for x in Team.players if x.life[0]<=0]) > 0:
            # print([(x.name, x.life) for x in Team.players if x.invisible==0 and x.life[0]>0 and x!=avoid_player])
        if has_type!=None:
            possible_players = [x for x in possible_players if x.type==has_type]
        len_targets = min(len(possible_players),nbr)
        tries = 30
        while len(players) < len_targets:
            if tries <= 0:
                break
            t = rdm_coef([x.provocation_coef for x in possible_players])
            if t >= len(Team.players) or Team.players[t] in players or t >= len(possible_players):
                tries -= 1
                continue
            players.append(possible_players[t])
            IDs.append(Team.players.index(players[-1]))
            # print("  ", t, [x.provocation_coef for x in possible_players])
            possible_players.pop(t)
            tries = 30
        if return_index:
            return players,IDs
        else:
            return players


    async def a_1(self,perso):
        "Coup laser"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],14,perso)
        txt = "{} donne des coups puissants avec son sabre laser contre {}, et fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>14:
            txt += random.choice(self.critical)
        elif points==0:
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
        return "{p} lève la main et protège, grâce à une étrange énergie, {t[1]} et {t[2]}, en leur ajoutant 2 points de bouclier".format(p=names[0],t=names)
    
    async def u_1(self,perso):
        "Tir de la mort"
        names = list()
        targets = await self.select_random_players(3,perso.Team2)
        for t in targets:
            await self.apply_dmg(t,22,perso,False)
            await self.add_effect(t,'fire',2)
            names.append(t.name)
        txt =  "Le ciel s'obscurcit avec l'apparition d'une planète. {p} lui fait envoyer un rayon destructeur sur {t}, ce qui leur inflige 22 PV de dégâts, et les enflamme !".format(p=perso.name,t = await self.merge_names(names))
        return txt

    async def a_3(self,perso):
        "Pour les voleurs"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],20,perso)
        txt = "{} se jette sur {} et lui fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>20:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt
    
    async def c_3(self,perso):
        "Araignée géante"
        targets = await self.select_random_players(3,perso.Team2)
        points = await self.apply_dmg(targets[0],22,perso)
        targets[1].frozen += 1
        await self.add_effect(targets[2],'poison',1)
        txt = "{p} appelle une araignée géante, qui fait {d}PV de dégâts sur {t[0]}, immobilise {t[1]} et empoisonne {t[2]} ! ".format(p=perso.name,t=[x.name for x in targets],d=points)
        return txt

    async def u_3(self,perso):
        "Le précieux"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],32,perso)
        perso.invisible += 1
        txt = "La main de {} scintille un instant. Il devient invisible et parvient à faire {} PV de dégâts à {} ! ".format(perso.name,points,target[0].name)
        if points>32:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def a_4(self,perso):
        "Doigt pistolet"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target,26,perso)
        perso.invisible += 1
        txt = "{} utilise son doigt sur {} et lui fait {} PV de dégâts ! ".format(perso.name,target.name,points)
        if points>26:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def c_4(self,perso):
        "Bonus tactique"
        targets_attack = await self.select_random_players(3, perso.Team1, evil=False)
        for t in targets_attack:
            # t.attack_bonus += 1
            await self.add_effect(t, 'attack_bonus', 1, bonus=1)
        targets_shield = await self.select_random_players(2, perso.Team1, evil=False)
        for t in targets_shield:
            t.shield += 1
        return "{} utilise ses compétences sur {} en leur procurant un boost d'attaque, et ajoute un bouclier à {} ! ".format(perso.name,await self.merge_names(targets_attack),await self.merge_names(targets_shield))

    async def u_4(self,perso):
        "Déluge de lait"
        for t in await self.select_random_players(50,perso.Team2):
            await self.apply_dmg(t,28,perso)
        targets_shield = await self.select_random_players(2,perso.Team2)
        for t in targets_shield:
            t.shield -= 1
        return "{} utilise ses compétences sur l'équipe adverse en leur infligeant 28pv de dégâts, et réduit le bouclier de {} ! ".format(perso.name,await self.merge_names(targets_shield))

    async def a_5(self,perso):
        "Hache volée"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],24,perso)
        txt = "{} utilise son épée contre {}, et fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points > 24:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def c_5(self,perso):
        "Cri destructeur"
        targets = await self.select_random_players(5,perso.Team2)
        for e, p in enumerate(targets):
            if e<3:
                # p.attack_bonus -= 1
                await self.add_effect(p, 'attack_bonus', 1, bonus=-1)
            else:
                p.esquive -= 25
        return "{} utilise son cri contre l'équipe adverse, réduisant l'attaque de {}, et l'esquive de {}. ".format(perso.name, await self.merge_names(targets[:3]), await self.merge_names(targets[3:]))

    async def u_5(self,perso):
        "Déferlante de magie"
        for t in await self.select_random_players(5,perso.Team2):
            await self.apply_dmg(t,20,perso)
        targets_fire = await self.select_random_players(2,perso.Team2)
        for t in targets_fire:
            await self.add_effect(t,'fire',1)
        target_poison = await self.select_random_players(1,perso.Team2)
        for t in target_poison:
            await self.add_effect(t,'poison',1)
        # perso.attack_bonus += 1
        await self.add_effect(perso, 'attack_bonus', 1, bonus=1)
        gr = "s'enflamment" if len(targets_fire)>1 else "s'enflamme"
        txt = "{p} utilise sa magie contre l'équipe adverse, leur causant 20pv de dégâts. De plus {fire} {gr}".format(p=perso.name,fire = await self.merge_names(targets_fire),gr=gr)
        if len(target_poison)==1:
            txt += ", et {} est empoisonné".format(target_poison[0].name)
        return txt+" ! "

    async def a_6(self,perso):
        "Main mutée"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target,20,perso)
        perso.invisible += 1
        txt = "{} attaque de sa main sur {} et lui fait {} PV de dégâts ! ".format(perso.name,target.name,points)
        if points>20:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def c_6(self,perso):
        "Corps acide"
        targets = await self.select_random_players(3,perso.Team2)
        for t in targets:
            await self.add_effect(t,'poison',1)
        perso.thorny = True
        txt = "{} empoisonne {} et se protège contre la prochaine attaque ! ".format(perso.name, await self.merge_names(targets))
        return txt
    
    async def u_6(self,perso):
        "Seconde bouche"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target,30,perso)
        perso.invisible += 1
        txt = "{} mord violemment {} en lui faisant {} PV de dégâts, avec un effet de poison ! ".format(perso.name,target.name,points)
        if points>30:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def a_9(self,perso):
        "Epées rouillées"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],6*4,perso)
        txt = "La {} se retourne contre {}, lui infligeant {}pv de dégât !".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt
    
    async def c_9(self,perso):
        "Sort de rage"
        target = await self.select_random_players(1,perso.Team2)
        target[0].attack_bonus -= 1
        for i in perso.Team1.players:
            # i.attack_bonus += 1
            await self.add_effect(i, 'attack_bonus', 1, bonus=1)
        perso.thorny = True
        txt = "La {} utilise un sort de rage, augmentant leurs attaques, et effrayant {} qui voit ses attaques diminuer !".format(perso.name,target[0].name)
        return txt
    
    async def u_9(self,perso):
        "Renforts aériens"
        for i in perso.Team2.players:
            await self.apply_dmg(i,22,perso)
            await self.add_effect(i,'fire',2)
        txt = "Des dragons rejoignent la {} et enflamment l'équipe adverse, leur enlevant 22pv chacun".format(perso.name)
        return txt

    async def a_10(self,perso):
        "Se vider les poches"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],10,perso)
        txt = "{} vide ses poches sur {}, en lui faisant au passage {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt
    
    async def c_10(self,perso):
        "Avalanche de bière"
        targets = await self.select_random_players(3,perso.Team2)
        names = list()
        for t in targets:
            await self.apply_dmg(t,18,perso)
            names.append(t.name)
        return "{p} déverse ses stocks de bières contre {t}, ce qui leur inflige 18 PV de dégâts !".format(p=perso.name,t = await self.merge_names(names))
    
    async def u_10(self,perso):
        "Donut atomique"
        for p in perso.Team1.players:
            await self.add_effect(p, 'regen', 1)
            await self.add_effect(p, 'blessing', 1)
        return "{} utilise un donut brillant en vert et, étonnamment, régénère tous ses alliés ! :doughnut: ".format(perso.name)

    async def a_13(self,perso):
        "Boule de froid"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],26,perso)
        txt = "{} envoie une boule de neige sur {}, et fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>26:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt
    
    async def c_13(self,perso):
        "Coup de gel"
        targets = await self.select_random_players(3,perso.Team2)
        names = list()
        for t in targets:
            await self.apply_dmg(t,20,perso)
            # t.attack_bonus -= 1
            await self.add_effect(t, 'attack_bonus', 1, bonus=-1)
            names.append(t.name)
        return "{p} refroidit {t[0]}, {t[1]} et {t[2]}, en faisant des dégâts à chacun et réduisant leurs attaques ! (-20pv)".format(p=perso.name,t=names)
    
    async def u_13(self,perso):
        "Tempête hivernale"
        points = list()
        for target in await self.select_random_players(50, perso.Team2):
            points.append(await self.apply_dmg(target, 22, perso))
        if len(points) == 0:
            return f"{perso.name} n'a trouvé aucun ennemi à viser.../"
        points = round(sum(points)/len(perso.Team2))
        targets = (await self.select_random_players(2,perso.Team2))
        if len(targets) > 0:
            targets[0].frozen += 1
            if len(targets) > 1:
                await self.add_effect(targets[1], 'bleeding', 2)
                return "{p} lance une tempête affectant toute l'équipe ennemie, qui se retrouve avec {s} PV en moins ! La tempête gèle aussi {t} et blesse {t2}".format(p=perso.name,t=targets[0].name,s=points,t2=targets[1].name)
            return "{p} lance une tempête affectant toute l'équipe ennemie, qui se retrouve avec {s} PV en moins ! La tempête gèle aussi {t} ".format(p=perso.name,t=targets[0].name,s=points)
        return f"{perso.name} lance une tempête affectant toute l'équipe ennemie, qui se retrouve avec {s} PV en moins !"
    
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
            await self.add_effect(t, 'attack_bonus', 1, bonus=-1)
        perso.provocation_coef += 1
        if len(targets) > 0:
            t = await self.merge_names([x.name for x in targets])
            return "{p} utilise son aboiement pour effayer l'équipe adverse, ce qui fait baisser les attaques de {t} !".format(p=perso.name, t=t)
        else:
            return f"{perso.name} n'a trouvé aucun adversaire"
    
    async def u_16(self,perso):
        "Flammes de l'enfer"
        for target in await self.select_random_players(50,perso.Team2):
            await self.add_effect(target,'fire',3)
            await self.apply_dmg(target,12,perso,False)
        return "{p} fait fissurer la terre, et des jets de lave enflamment l'équipe adverse, réduisant aussi leurs PV de 12 points !".format(p=perso.name)

    async def a_17(self,perso):
        "Grand coup"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],22,perso)
        txt = "{} porte un coup à {}, et fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>22:
            txt += random.choice(self.critical)
        elif points==0:
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
        txt = "{} fixe {}, et brusquement lui fait {} PV de dégâts. ".format(perso.name,target[0].name,points)
        if points>36:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def a_22(self,perso):
        "Couteau d'assassin"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],10,perso)
        txt = "{} utilise ses outils tranchants sur {}, et fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def c_22(self,perso):
        "Chara"
        # perso.attack_bonus += 1
        await self.add_effect(perso, 'attack_bonus', 2, bonus=1)
        perso.esquive += 20
        perso.thorny = True
        return "{p} perd contrôle et reçoit une augmentation soudaine de ses statistiques, lui apportant un bonus d'attaque et d'esquive".format(p=perso.name)
    
    async def u_22(self,perso):
        "Esprit déterminé"
        for i in await self.select_random_players(50, perso.Team1, avoid_player=perso, evil=False):
            i.shield += 1
            i.esquive += 30
        return "{}, déterminé comme jamais, soigne et renforce le bouclier de tous ses alliés".format(perso.name)

    async def a_24(self,perso):
        "Epée de l'ordre"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],20,perso)
        txt = "{} utilise son épée sur {}, et fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>20:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def c_24(self,perso):
        "Bombe fumigène"
        victimes = list()
        for player in await self.select_random_players(3,perso.Team2):
            # player.attack_bonus -= 1
            await self.add_effect(player, 'attack_bonus', 1, bonus=-1)
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
        txt = "{} disparaît dans la fumée, et utilise sa lame cachée pour faire {} de dégâts à {}. ".format(perso.name,points,target[0].name)
        if points>34:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt

    async def a_25(self,perso):
        "Découpe souriante"
        target = await self.select_random_players(1,perso.Team2)
        points = await self.apply_dmg(target[0],24,perso)
        if random.random()<0.1:
            self.add_effect(target,'bleeding',2)
            txt = "{} attaque avec sa scie {} et lui fait {} PV de dégâts, en plus de lui causer un saignement !".format(perso.name,target[0].name,points)
        else:
            txt = "{} utilise son couteau sur {} et lui fait {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt
    
    async def c_25(self,perso):
        "Rire inarrêtable"
        targets1 = await self.select_random_players(2, perso.Team1, avoid_player=perso, evil=False)
        for i in targets1:
            # i.attack_bonus += 1
            await self.add_effect(i, 'attack_bonus', 1, bonus=1)
        targets2 = await self.select_random_players(3,perso.Team2)
        for i in targets2:
            # i.attack_bonus -= 1
            await self.add_effect(i, 'attack_bonus', 1, bonus=-1)
        await self.add_effect(perso, 'attack_bonus', 1, bonus=1)
        # perso.attack_bonus += 1
        txt = "{p} éclate d'un rire dément, ce qui a pour effet d'augmenter les attaques de lui et ses alliés {a[0]} et {a[1]}, ainsi que de diminuer celles de {t[0]}, {t[1]} et {t[2]} ! ".format(p=perso.name,a=[x.name for x in targets1],t=[x.name for x in targets2])
        return txt
    
    async def u_25(self,perso):
        "Représentation spectaculaire"
        for target in await self.select_random_players(50,perso.Team2):
            await self.apply_dmg(target,26,perso)
            await self.add_effect(target,'poison',2)
        txt = "{p} se met à joyeusement danser. Chaque mouvement cause une explosion chez ses ennemis, leur faisant de lourds dégâts et les empoisonnant pour 2 tours".format(p=perso.name)
        return txt

    async def a_32(self,perso):
        "Gobage"
        target = await self.select_random_players(1,perso.Team2)
        if len(target)==0:
            return "{} n'a plus aucun adversaire à combattre !".format(perso.name)
        points = await self.apply_dmg(target[0],14,perso)
        txt = "{} avale des objets et les recrache sous forme d'étoile contre {}, lui faisant {} PV de dégâts ! ".format(perso.name,target[0].name,points)
        if points>14:
            txt += random.choice(self.critical)
        elif points==0:
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
        elif points==0:
            txt += random.choice(self.escape)
        allys = await self.select_random_players(2,perso.Team1,avoid_player=perso)
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
        points = await self.apply_dmg(target,10,perso)
        perso.invisible += 1
        txt = "{} utilise ses pouvoirs magiques sur {} et fait {} PV de dégâts ! ".format(perso.name,target.name,points)
        if points>10:
            txt += random.choice(self.critical)
        elif points==0:
            txt += random.choice(self.escape)
        return txt


def setup(bot):
    bot.add_cog(AttacksCog(bot))
