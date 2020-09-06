from discord.ext import commands
from math import log
from inspect import signature
from fcts.classes import Perso, Effect

class EffectsCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.file = 'effects'
        self.fire_immunes = ['Dohvakiin']
        self.poison_immunes = ['Xénomorphe']
        self.effects = {'regen': self.regen,
            'blessing': self.blessing,
            'fire': self.fire,
            'poison':self.poison,
            'bleeding':self.bleeding,
            'critical_bonus':self.critical,
            'attack_bonus':self.attack
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

    class regen(Effect):
        def __init__(self, duration=1):
            super().__init__("regen", "❤️", duration, True)

        async def execute(self, perso: Perso):
            perso.life[0] = min(perso.life[1], perso.life[0]+perso.life[1]*0.15)

    class blessing(Effect):
        def __init__(self, duration=1):
            super().__init__("blessing", "✨", duration, True)

        async def execute(self, perso: Perso):
            perso.frozen = 0
            perso.effects.array = [x for x in perso.effects.array if x.positive]

    class fire(Effect):
        def __init__(self, duration=1):
            super().__init__("fire", "🔥", duration)
        
        async def execute(self, perso: Perso):
            lvl = perso.lvl
            perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
            if perso.life[0] < 0:
                perso.life[0] = 0
    
    class poison(Effect):
        def __init__(self, duration=1):
            super().__init__("poison", "🤢", duration)

        async def execute(self, perso: Perso):
            lvl = perso.lvl
            perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
            if perso.life[0] < 0:
                perso.life[0] = 0

    class bleeding(Effect):
        def __init__(self, duration=1):
            super().__init__("bleeding", "🩸", duration)

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
        def __init__(self, duration=1, bonus=1, _type=None):
            super().__init__("attack_bonus", None, duration, positive=(bonus>0), event="after_attack")
            self.value = bonus
            self.type = _type
            self.fusion = False
        
        async def execute(self, perso: Perso):
            return


    async def p_1(self,perso):
        """Guerrier imbattable"""
        if not perso.initialized:
            for target in perso.Team1.players:
                target.attack_bonus += 0.3
                if target==perso:
                    target.esquive = min(0,target.esquive-3)
        perso.initialized = True
    
    async def p_2(self,perso):
        """Pistolet à portails"""
        if not perso.initialized:
            for target in perso.Team1.players:
                target.esquive += 5
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
            perso.esquive = 14
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
                target.esquive -= 3
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
                target.esquive -= 4
        perso.initialized = True
    
    async def p_12(self,perso):
        """Don de champignons"""
        if not perso.initialized:
            perso.life[0] += 10
            perso.life[1] += 10
        perso.initialized = True




def setup(bot):
    bot.add_cog(EffectsCog(bot))