import nextcord
from nextcord.ui import View, Button, Select
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils import LegendsBot

class ChooseOpponent(View):
    "A view allowing players to accept a fight"

    def __init__(self, bot: "LegendsBot", parent_inter: nextcord.Interaction, timeout: int=90):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.parent_inter = parent_inter
        self.player: nextcord.User = None

    async def init(self):
        "Initialize buttons with translations"
        join_label = await self.bot._(self.parent_inter, "buttons.join.label")
        confirm_btn = Button(label=join_label, style=nextcord.ButtonStyle.green)
        confirm_btn.callback = self.join
        self.add_item(confirm_btn)
        cancel_label = await self.bot._(self.parent_inter, "buttons.cancel.label")
        cancel_btn = Button(label=cancel_label, style=nextcord.ButtonStyle.grey)
        cancel_btn.callback = self.cancel
        self.add_item(cancel_btn)
    
    async def disable(self, original_interaction: nextcord.Interaction):
        "Disable the view buttons, to avoid any new interaction"
        for child in self.children:
            child.disabled = True
        try:
            await original_interaction.edit(view=self)
        except nextcord.InvalidArgument:
            await original_interaction.edit_original_message(view=self)
    
    async def join(self, inter: nextcord.Interaction):
        "A player want to join the fight"
        if not inter.user:
            self.bot.log.warning("I didn't receive the interaction user ._.")
            return
        if inter.user == self.parent_inter.user:
            return
        if not await self.check_player_deck(inter.user):
            await inter.send(await self.bot._(inter, "combat.preparation.too-few"), ephemeral=True)
            return
        if await self.check_player_busy(inter.user):
            await inter.send(await self.bot._(inter, "combat.preparation.already-in"), ephemeral=True)
            return
        self.player = inter.user
        self.stop()
    
    async def cancel(self, inter: nextcord.Interaction):
        "Cancel the action when clicking"
        if inter.user != self.parent_inter.user:
            return
        await inter.send(await self.bot._(self.parent_inter, "buttons.cancel.answer"), ephemeral=True)
        self.value = False
        await self.disable(inter)
        self.stop()

    async def check_player_deck(self, user: nextcord.User):
        "Check if a user has enough characters in their deck"
        play2_deck = await self.bot.cogs['UsersCog'].get_user_deck(user.id)
        return len(play2_deck) >= 5
    
    async def check_player_busy(self, user: nextcord.User):
        "Check if a user is already playing with someone else"
        return user in self.bot.fight_module.in_combat


class ChooseCharacters(View):
    "A view asking a user to select 5 characters"

    def __init__(self, bot: "LegendsBot", parent_inter: nextcord.Interaction, user_id: int, timeout: int=30):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.parent_inter = parent_inter
        self.user_id = user_id
        self.team: list = []
        self.select: Select = None
        self.deck = dict()
    
    async def init(self):
        placeholder = await self.bot._(self.parent_inter, "combat.choice.placeholder")
        self.deck: dict = await self.bot.cogs['UsersCog'].get_user_deck(self.user_id)
        self.select = Select(min_values=5, max_values=5, placeholder=placeholder, options=[
            nextcord.SelectOption(label=character['personnage'], value=key)
            for key, character in self.deck.items()
        ])
        self.select.callback = self.callback
        self.add_item(self.select)
    
    async def disable(self, original_interaction: nextcord.Interaction):
        "Disable the view select, to avoid any new interaction"
        self.select.disabled = True
        try:
            await original_interaction.edit(view=self)
        except nextcord.InvalidArgument:
            await original_interaction.edit_original_message(view=self)
    
    async def callback(self, inter: nextcord.Interaction):
        "Called when the user select their characters"
        if inter.user.id != self.user_id:
            return
        await inter.send("uwu")
        await self.disable(inter)
        self.team = [self.deck[int(key)] for key in self.select.values]
        self.stop()
