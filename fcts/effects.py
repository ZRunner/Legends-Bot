from nextcord.ext import commands
from math import log
from inspect import signature
from fcts.classes import Perso, Effect

class EffectsCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.file = 'effects'
        self.fire_immunes = ['Dohvakiin']
        self.poison_immunes = ['Xénomorphe']
        self.effects = {'regen': self.healing,
            'blessing': self.blessing,
            'curse': self.curse,
            'fire': self.fire,
            'poison':self.poison,
            'bleeding':self.bleeding,
            'critical_bonus':self.critical,
            'attack_bonus':self.attack,
            'shield_bonus':self.shield_bonus,
            'shield_malus':self.shield_malus,
            'invisibility':self.invisibility,
            'frozen':self.frozen,
            'dodge_bonus':self.dodge,
            'provocation':self.provocation
            # 'Guerrier imbattable':self.p_1,
            # 'Pistolet à portails':self.p_2,
            # 'Espiègle et rusé':self.p_3,
            # 'Combattant de boss':self.p_4,
            # 'Discrétion surnaturelle':self.p_5,
            # 'Alien amélioré':self.p_6,
            # 'Danger silencieux':self.p_8,
            # 'Tchoa':self.p_10,
            # 'Terreur nocturne':self.p_11,
            # 'Don de champignons':self.p_12,
            }
    

    async def add_effect(self, perso:Perso, nom:str, duration:int, **kwargs):
        if nom=='_on_fire' and perso.name in self.fire_immunes:
            return perso
        if nom=='_on_poison' and perso.name in self.poison_immunes:
            return perso
        if nom in self.effects:
            sign = signature(self.effects[nom])
            kwargs = {k:v for k,v in kwargs.items() if k in sign.parameters}
            perso.effects.add(self.effects[nom](duration, **kwargs))

    class healing(Effect):
        """Soigne de 15% les PV du personnage."""
        def __init__(self, duration=1):
            super().__init__("regen", "❤️", duration, True)

        async def execute(self, perso: Perso):
            perso.life[0] = min(perso.life[1], perso.life[0]+perso.life[1]*0.15)

    class blessing(Effect):
        """Retire les effets négatifs (Fire, Poison, Bleed, Freeze, Attack Penalty, Shield Penalty, Esquive Penalty)."""
        def __init__(self, duration=1):
            super().__init__("blessing", "✨", duration, True, event='after_action')

        async def execute(self, perso: Perso):
            perso.effects.array = [x for x in perso.effects.array if x.positive]

    class curse(Effect):
        """Retire les effets positifs (Attack Boost, Contre-attaque, Shield, Esquive Boost, Invisible, Provocation)."""
        def __init__(self, duration=1):
            super().__init__("curse", "✨", duration, True, event='after_action')

        async def execute(self, perso: Perso):
            perso.effects.array = [x for x in perso.effects.array if not x.positive]

    class fire(Effect):
        """8 de dégâts, dure 1 tour. Non cumulable."""
        def __init__(self, duration=1):
            super().__init__("fire", "🔥", duration)
        
        async def execute(self, perso: Perso):
            lvl = perso.lvl
            perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
            if perso.life[0] < 0:
                perso.life[0] = 0

    class poison(Effect):
        """5 de dégâts, dure 2 tours. Non cumulable."""
        def __init__(self, duration=1):
            super().__init__("poison", 680872153872334849, duration)

        async def execute(self, perso: Perso):
            lvl = perso.lvl
            perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
            if perso.life[0] < 0:
                perso.life[0] = 0

    class bleeding(Effect):
        """6 de dégâts, dure 1 tour. 2 cumulables."""
        def __init__(self, duration=1):
            super().__init__("bleeding", 640580514012463141, duration)

        async def execute(self, perso: Perso):
            lvl = perso.lvl
            perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
            if perso.life[0] < 0:
                perso.life[0] = 0

    class critical(Effect):
        def __init__(self, duration=1, bonus=1):
            super().__init__("critical_bonus", None, duration, positive=(bonus>0), event="after_attack")
            self.value = bonus
            self.fusion = False
        
        async def execute(self, perso: Perso):
            return

    class attack(Effect):
        """Augmente les dégâts de 20%. Peut être cumulé une seconde fois, mais à seulement 15% (donc un total de 35% de dégâts en plus). Idem en Penalty, en réduisant les dégâts infligés."""
        def __init__(self, duration=1, bonus=1, _type=None):
            super().__init__("attack_bonus", None, duration, positive=(bonus>0), event="after_attack")
            self.value = bonus
            self.type = _type
            self.fusion = False
        
        async def execute(self, perso: Perso):
            return

    class shield_bonus(Effect):
        """Réduit les dégâts reçus de 20%/30%/40%/45%/50%. Cumulable 5 fois."""
        def __init__(self, duration=1):
            super().__init__("shield_bonus", None, duration, positive=True)
            self.fusion = False
        
        async def execute(self, perso: Perso):
            return

    class shield_malus(Effect):
        """Augmente les dégâts reçus de 20%/30%. Cumulable 2 fois."""
        def __init__(self, duration=1):
            super().__init__("shield_malus", None, duration, positive=False)
            self.fusion = False
        
        async def execute(self, perso: Perso):
            return

    class invisibility(Effect):
        """Met l'esquive à 100, ignorant les malus d'esquive. Non cumulable. Exclusif à la Cu des Espions."""
        def __init__(self, duration=1):
            super().__init__("invisibility", 639951219254624267, duration, positive=True)
        
        async def execute(self, perso: Perso):
            return

    class frozen(Effect):
        """Esquive à 0, empêche le personnage de participer à son prochain tour. Non cumulable."""
        def __init__(self, duration=1):
            super().__init__("frozen", '❄', duration, positive=False, event="after_action")
        
        async def execute(self, perso: Perso):
            return

    class dodge(Effect):
        """Apporte 15 points d'esquive en plus. 2 cumulables (pour un total de 30 points d'esquive en plus). Idem en Penalty, mais bloquera à 0 évidemment."""
        def __init__(self, duration=1, bonus=1):
            """bonus = 1 if bonus, -1 if malus"""
            if bonus not in (1, -1):
                raise ValueError
            emoji = 640586268585099272 if bonus==1 else 640586246564872204
            super().__init__("dodge_bonus", emoji, duration, positive=(bonus>0))
            self.value = bonus
            self.fusion = False
        
        async def execute(self, perso: Perso):
            return

    class provocation(Effect):
        """Oblige les ennemis à attaquer le personnage ayant cet effet. Exclusif aux Tanks."""
        def __init__(self, duration=1):
            super().__init__("provocation", 772086308881039371, duration, positive=True)
        
        async def execute(self, perso: Perso):
            return

    class thorny(Effect):
        """Si attaqué lorsqu'il possède cet effet, le personnage infligera 25% de ses points d'attaque à l'attaquant. Cela consomme l'effet. Non cumulable."""
        def __init__(self, duration=1):
            super().__init__("thorny", 772095039903498240, duration, positive=True, event="after_defense")
        
        async def execute(self, perso: Perso):
            return


    async def p_1(self,perso):
        """Guerrier imbattable"""
        if not perso.initialized:
            for target in perso.Team1.players:
                target.attack_bonus += 0.3
                if target==perso:
                    pass
                    # target.esquive = min(0,target.esquive-3)
        perso.initialized = True
    
    async def p_2(self,perso):
        """Pistolet à portails"""
        if not perso.initialized:
            for target in perso.Team1.players:
                pass
                # target.esquive += 5
        perso.initialized = True
    
    async def p_3(self,perso):
        """Espiègle et rusé"""
        if not perso.initialized:
            perso.attack_bonus_type['Guerrier'] = 10
            perso.initialized = True

    async def p_4(self,perso):
        """Combattant de boss"""
        if not perso.initialized:
            perso.attack_bonus_type['Destructeur'] = 10
            perso.initialized = True

    async def p_5(self,perso):
        """Discrétion surnaturelle"""
        if not perso.initialized:
            # perso.esquive = 14
            perso.initialized = True

    async def p_6(self,perso):
        """Alien amélioré"""
        if (not perso.initialized) or (not perso.name in self.poison_immunes):
            self.poison_immunes.append(perso.name)
            perso.initialized = True

    async def p_8(self,perso):
        """Danger silencieux"""
        if not perso.initialized:
            for target in perso.Team2.players:
                pass
                # target.esquive -= 3
        perso.initialized = True

    async def p_10(self,perso):
        """Tchoa"""
        if not perso.initialized:
            perso.critical += 15
        perso.initialized = True

    async def p_11(self,perso):
        """Terreur nocturne"""
        if not perso.initialized:
            for target in perso.Team2.players:
                pass
                # target.esquive -= 4
        perso.initialized = True
    
    async def p_12(self,perso):
        """Don de champignons"""
        if not perso.initialized:
            perso.life[0] += 10
            perso.life[1] += 10
        perso.initialized = True




def setup(bot):
    bot.add_cog(EffectsCog(bot))