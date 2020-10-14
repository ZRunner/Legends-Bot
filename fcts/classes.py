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
        return any([True for x in self.array if x.name == name])
    
    def get(self, name: str) -> list:
        """Get specific effects by their name
        Returns None if the character doesn't have that effect"""
        matches = [x for x in self.array if x.name == name]
        if len(matches) > 0:
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
        match = self.get(effect.name)
        if match and effect.fusion:
            match.duration = max(match.duration, effect.duration)
        else:
            self.array.append(effect)
    
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
    def __init__(self, name, classe, lvl, at1, at2, ult, pas, life, esquive, Type, passifType):
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
        self.frozen = 0
        self.shield = 0
        self.invisible = 0
        self.initialized = False
        self.esquive = esquive  # donner/enlever 20-40 à chaque fois
        self.thorny = False
        self.type = Type
        self.provocation_coef = 1
        self.passifType = passifType
        self.Team1: Team  # sa propre équipe
        self.Team2: Team  # équipe adverse
        self._critical = 10

    @property
    def critical(self) -> int:
        bonuses = self.effects.get('critical_bonus')
        if bonuses is None:
            return self._critical
        return self._critical + sum([x.value for x in bonuses])
    
    def attack_bonus(self, _type=None) -> int:
        bonuses = self.effects.get('attack_bonus')
        if bonuses is None:
            return 0
        return sum([x.value for x in bonuses if x.type in (None, _type)])

    def __str__(self):
        return '<Perso  name="{}"  classe="{}"  lvl={}  xp={}>'.format(self.name, self.classe, self.lvl, self.xp)


class Effect:
    """The base effect type for all used effects"""
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
