from discord.ext import commands
from math import log

class EffectsCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.file = 'effects'
        self.fire_immunes = ['Dohvakiin']
        self.poison_immunes = ['Xénomorphe']
        self.effects = {'_on_fire':self.on_fire,
            '_on_poison':self.poison,
            '_on_bleeding':self.saignement,
            'Guerrier imbattable':self.p_1,
            'Pistolet à portails':self.p_2,
            'Espiègle et rusé':self.p_3,
            'Fils de dragon':self.p_5,
            'Danger silencieux':self.p_8,
            'Tchoa':self.p_10,
            'Terreur nocturne':self.p_11,
            'Don de champignons':self.p_12,
            }
    

    async def add_effects(self,perso,nom:str,tours:int):
        if nom=='_on_fire' and perso.name in self.fire_immunes:
            return perso
        if nom=='_on_poison' and perso.name in self.poison_immunes:
            return perso
        if self.effects[nom] in perso.effects.keys():
            perso.effects[nom][1] = max(perso.effects[nom][1],tours)
        else:
            perso.effects[nom] = [self.effects[nom], tours]


    async def regen(self,persos:list):
        for p in persos:
            p.life[0] = min(p.life[1], p.life[0]+p.life[1]*0.15)
    
    async def blessing(self,persos:list):
        for p in persos:
            p.frozen = 0
            for i in ['_on_fire','_on_poison','_on_bleeding']:
                p.pop(i,None)

    async def on_fire(self,perso):
        """On Fire!"""
        lvl = perso.lvl
        perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
        if perso.life[0] < 0:
            perso.life[0] = 0
    
    async def poison(self,perso):
        """Poison"""
        lvl = perso.lvl
        perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
        if perso.life[0] < 0:
            perso.life[0] = 0
    
    async def saignement(self,perso):
        """Saignement"""
        lvl = perso.lvl
        perso.life[0] -= round((lvl**1.85)/80 + 2*log(lvl+1))
        if perso.life[0] < 0:
            perso.life[0] = 0




    async def p_1(self,perso):
        """Guerrier imbattable"""
        if not perso.initialized:
            for target in perso.Team1.players:
                target.attack_bonus += 0.3
                if target==perso:
                    target.esquive = min(0,target.esquive-3)
        perso.initialized = True
        perso.invisible = 1
    
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

    async def p_5(self,perso):
        """Fils de dragon"""
        if not perso.initialized:
            perso.esquive -= 6
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
            perso.critical += 20
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