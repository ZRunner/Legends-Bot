from typing import Union
import nextcord, sys, traceback, re, random
from nextcord.ext import commands

from utils import LegendsBot

class ErrorsCog(commands.Cog):

    def __init__(self, bot: LegendsBot):
        self.bot = bot
        self.file = "errors"
    
    async def on_interaction_error(self, inter: nextcord.Interaction, error: Exception):
        "The event triggered when an error is raised in an interaction process"
        try:
            await inter.send(await self.bot._(inter, 'error.unexpected_error'))
        except:
            self.bot.log.warn("[on_interaction_error] Impossible d'envoyer l'erreur", exc_info=True)
        # All other Errors not returned come here... And we can just print the default TraceBack.
        self.bot.log.info(f'Exception in Interaction {inter.id}:')
        #traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await self.on_error(error, inter)

    async def on_cmd_error(self, ctx: commands.Context, error: Exception):
        """The event triggered when an error is raised while invoking a command."""
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return
        
        ignored = (commands.CommandNotFound,commands.ConversionError,commands.BotMissingPermissions,nextcord.errors.Forbidden)
        
        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.CheckFailure):
            if hasattr(error, 'missing_permissions'):
                perms = " & ".join([await self.bot._(ctx, 'perms.'+x) for x in error.missing_permissions])
                await ctx.send(await self.bot._(ctx, 'error.missing_perms', perms=perms))
            return
        elif isinstance(error,commands.CommandOnCooldown):
            await ctx.send(await self.bot._(ctx, 'error.cooldown', count=round(error.retry_after,2)))
            return
        elif isinstance(error,(commands.BadArgument,commands.BadUnionArgument)):
            # Could not convert "limit" into int. OR Converting to "int" failed for parameter "number".
            r = re.search(r'Could not convert \"(?P<arg>[^\"]+)\" into (?P<type>[^.\n]+)',str(error))
            if r == None:
                r = re.search(r'Converting to \"(?P<type>[^\"]+)\" failed for parameter \"(?P<arg>[^.\n]+)\"',str(error))
            if r!=None:
                return await ctx.send(await self.bot._(ctx, 'error.convert', arg=r.group('arg'), type=r.group('type')))
            # zzz is not a recognised boolean option
            r = re.search(r'(?P<arg>[^\"]+) is not a recognised (?P<type>[^.\n]+) option',str(error))
            if r!=None:
                return await ctx.send(await self.bot._(ctx, 'error.invalid', arg=r.group(1), opt=r.group(2)))
            # Member "Z_runner" not found
            r = re.search(r'Member \"([^\"]+)\" not found',str(error))
            if r != None:
                return await ctx.send(await self.bot._(ctx, 'error.member_not_found', member=r.group(1)))
            # User "Z_runner" not found
            r = re.search(r'User \"([^\"]+)\" not found',str(error))
            if r!=None:
                return await ctx.send(await self.bot._(ctx, 'error.user_not_found', user=r.group(1)))
            print('errors -',error)
        elif isinstance(error,commands.MissingRequiredArgument):
            emo = random.choice([':eyes:','',':confused:',':thinking:',''])
            await ctx.send(await self.bot._(ctx, 'error.missing_argument', arg=error.param.name) + emo)
            return
        elif isinstance(error,commands.DisabledCommand):
            await ctx.send(await self.bot._(ctx, 'error.command_disabled', cmd=ctx.invoked_with))
            return
        elif isinstance(error,commands.errors.NoPrivateMessage):
            await ctx.send(await self.bot._(ctx, 'error.command_in_dm', cmd=ctx.invoked_with))
            return
        else:
            try:
                await ctx.send(await self.bot._(ctx, 'error.unexpected_error'))
            except:
                self.bot.log.warn("[on_cmd_error] Impossible d'envoyer l'erreur dans le salon {}".format(ctx.channel.id))
        # All other Errors not returned come here... And we can just print the default TraceBack.
        self.bot.log.info('Ignoring exception in command {}:'.format(ctx.command))
        #traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await self.on_error(error,ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        await self.on_cmd_error(ctx,error)

    @commands.Cog.listener()
    async def on_error(self, error: Exception, ctx: Union[commands.Context, nextcord.Interaction]):
        try:
            tr = traceback.format_exception(type(error), error, error.__traceback__)
            msg = "```python\n{}\n```".format(" ".join(tr).replace('arthur', 'zrunner'))
            if ctx is None:
                await self.senf_err_msg(f"Erreur interne\n{msg}")
            elif ctx.guild is None:
                await self.senf_err_msg(f"DM | {ctx.channel.name}\n{msg}")
            else:
                await self.senf_err_msg(ctx.guild.name+" | "+ctx.channel.name+"\n"+msg)
        except Exception as e:
            self.bot.log.warn(f"[on_error] {e}", exc_info=True)
        try:
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        except Exception as e:
            self.bot.log.warning(f"[on_error] {e}", exc_info=True)


    async def senf_err_msg(self,msg):
        """Envoie un message dans le salon d'erreur"""
        salon = self.bot.get_channel(513370852352327690)
        if salon == None:
            return False
        await salon.send(msg)
        return True


def setup(bot):
    bot.add_cog(ErrorsCog(bot))
