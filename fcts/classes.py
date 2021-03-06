import random

class Team:
    """General class for a characters group during a match"""
    def __init__(self, players=[], user=None, rounds=0):
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
    
    @property
    def lost(self) -> bool:
        """if everyone died"""
        return len([1 for x in self.players if x.life[0] > 0]) == 0

    def __str__(self):
        return '<Team  user="{}"  players=[{}]  rounds={}>'.format(self.user, ", ".join([str(x) for x in self.players]), self.rounds)

    def __len__(self):
        return len(self.players)


class Effects:
    """Manage every character's effects"""
    def __init__(self):
        self.array = list()
    
    def has(self, name: str) -> bool:
        """Check if the character already has an effect"""
        return any([(x.name == name and x.duration > 0) for x in self.array])
    
    def get(self, name: str) -> list:
        """Get specific effects by their name
        Returns None if the character doesn't have that effect"""
        matches = [x for x in self.array if x.name == name and x.duration > 0]
        if len(matches) > 0:
            if name == "shield_bonus": # max 5 shield bonus
                return matches[:5]
            elif name == "shield_malus": # max 2 shield malus
                return matches[:2]
            else:
                return matches
        return None
    
    def get_one(self, name:str):
        """Get a specific effect by its name
        Returns None if the character doesn't have that effect"""
        matches = self.get(name)
        if not matches:
            return None
        return matches[0]

    def add(self, effect):
        """Add an effect to a character"""
        match = self.get_one(effect.name)
        if effect.fusion and match:
            match.duration = max(match.duration, effect.duration)
        else:
            self.array.append(effect)
    
    def remove(self, name:str, count:int=1) -> int:
        """Remove a certain number of effects
        returns the number of deleted effects"""
        to_remove = list()
        for i, effect in enumerate(self.array):
            if effect.name == name and len(to_remove) < count:
                to_remove.append(i)
        for i in reversed(to_remove):
            del self.array[i]
        return len(to_remove)
    
    def clean(self):
        """Remove every old effect"""
        self.array = [x for x in self.array if x.duration > 0]
    
    def empty(self):
        """Remove every effect"""
        self.array = list()
    
    async def execute(self, player, event:str):
        """Apply effects when needed
        - end_turn when a team has ended its turn"""
        for effect in self.array:
            if effect.event == event:
                await effect.execute(player)
                effect.duration -= 1

class Perso:
    """General class for a character"""
    def __init__(self, name, classe, lvl, at1, at2, ult, pas, life, dodge, Type, passifType):
        self.name = name
        self.classe = classe
        self.lvl = lvl
        self.attaque1 = at1
        self.attaque2 = at2
        self.ultime = ult
        self.passif = pas
        self.xp = 0
        self.points = random.randint(0, 5)
        self.life = [life, life]  # [actuel, max]
        self.effects = Effects()
        self.initialized = False
        # self.esquive = esquive  # donner/enlever 20-40 à chaque fois
        self.type = Type
        self.passifType = passifType
        self.Team1: Team  # sa propre équipe
        self.Team2: Team  # équipe adverse
        self._critical_base = 10
        self._dodge_base = dodge

    @property
    def critical(self) -> int:
        bonuses = self.effects.get('critical_bonus')
        if bonuses is None:
            return self._critical_base
        return self._critical_base + sum([x.value for x in bonuses])
    
    @property
    def shield_boost(self) -> int:
        b = [0.2, 0.3, 0.4, 0.45, 0.5]
        temp = self.effects.get('shield_bonus')
        bonuses = 0 if temp is None else b[len(temp)-1]
        b = [0.2, 0.3]
        temp = self.effects.get('shield_malus')
        bonuses -= 0 if temp is None else b[len(temp)-1]
        return bonuses
    
    @property
    def dodge(self) -> int:
        if self.frozen:
            return 0
        if self.invisible:
            return 100
        bonuses = self.effects.get('dodge_bonus')
        if bonuses is None:
            return self._dodge_base
        # can't be lower than opposite of base (so 0)
        b = max(-self._dodge_base, sum([x.value*15 for x in bonuses]))
        # can't be higher than 30 (so base+30)
        b = min(30, b)
        return self._dodge_base + b
    
    @property
    def invisible(self) -> bool:
        return self.effects.get("invisibility") is not None

    @property
    def frozen(self) -> bool:
        return self.effects.get("frozen") is not None
    
    @property
    def thorny(self) -> bool:
        return self.effects.get("thorny") is not None

    @property
    def provocation(self) -> bool:
        if self.invisible:
            return False
        return self.classe == "Tank" and self.effects.get("provocation") is not None

    def attack_bonus(self, _type=None) -> int:
        bonuses = self.effects.get('attack_bonus')
        if bonuses is None:
            return 0
        val = sum([x.value for x in bonuses if x.type in (None, _type)])
        b = (0, 20, 35)
        if val > 0:
            return b[min(val, 2)]
        else:
            return b[min(-val, 2)]

    def __str__(self):
        return '<Perso  name="{}"  classe="{}"  xp={} effects={}>'.format(self.name, self.classe, self.xp, len(self.effects.array))


class Effect:
    """The base effect type for all used effects
    
    Event types
    -----------
    end_turn: right before choosing an action
    before_action: between the action choice and the action execution
    before_attack: right before the action, if it is an attack
    after_attack: right after the action, if it was an attack
    after_action: right after any action
    instant: after any action of any opposite player
    after_defense: right after undergoing an attack"""
    def __init__(self, name: str, emoji: str = None, duration: int = 1, positive: bool = False, event: str = "end_turn"):
        self.name = name
        self.emoji = emoji
        self.duration = duration
        self.positive = positive
        self.event = event
        self.fusion = True

    async def execute(self, perso: Perso):
        pass

    def __str__(self):
        return f'<Effect {self.name} duration={self.duration}>'
