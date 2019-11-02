import discord, sys, traceback, re, random
from discord.ext import commands

class ErrorsCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file = "errors"

    async def on_cmd_error(self,ctx,error):
        """The event triggered when an error is raised while invoking a command."""
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return
        
        ignored = (commands.CommandNotFound,commands.CheckFailure,commands.ConversionError,commands.BotMissingPermissions,discord.errors.Forbidden)
        
        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return
        elif isinstance(error,commands.CommandOnCooldown):
            await ctx.send("Cette commande est en cooldown, vous devez attendre encore {} secondes !".format(round(error.retry_after,2)))
            return
        elif isinstance(error,(commands.BadArgument,commands.BadUnionArgument)):
            # Could not convert "limit" into int. OR Converting to "int" failed for parameter "number".
            r = re.search(r'Could not convert \"(?P<arg>[^\"]+)\" into (?P<type>[^.\n]+)',str(error))
            if r == None:
                r = re.search(r'Converting to \"(?P<type>[^\"]+)\" failed for parameter \"(?P<arg>[^.\n]+)\"',str(error))
            if r!=None:
                return await ctx.send("Oups, impossible de convertir le paramètre `{}` en type \"{}\" :confused:".format(r.group('arg'),r.group('type')))
            # zzz is not a recognised boolean option
            r = re.search(r'(?P<arg>[^\"]+) is not a recognised (?P<type>[^.\n]+) option',str(error))
            if r!=None:
                return await ctx.send("`{}` n'est pas une option valide pour {}".format(r.group(1),r.group(2)))
            # Member "Z_runner" not found
            r = re.search(r'Member \"([^\"]+)\" not found',str(error))
            if r != None:
                return await ctx.send("Impossible de trouver le membre {} :confused:".format(r.group(1)))
            # User "Z_runner" not found
            r = re.search(r'User \"([^\"]+)\" not found',str(error))
            if r!=None:
                return await ctx.send("Impossible de trouver l'utilisateur {}".format(r.group(1)))
            print('errors -',error)
        elif isinstance(error,commands.MissingRequiredArgument):
            await ctx.send("Oups, il manque l'argument \"{}\" {}".format(error.param.name,random.choice([':eyes:','',':confused:',':thinking:',''])))
            return
        elif isinstance(error,commands.DisabledCommand):
            await ctx.send("La commande {} est désactivée".format(ctx.invoked_with))
            return
        elif isinstance(error,commands.errors.NoPrivateMessage):
            await ctx.send("La commande {} n'est pas autorisée en Messages Privés".format(ctx.invoked_with))
            return
        else:
            try:
                await ctx.send("`ERREUR:` "+str(error))
            except:
                print("[on_cmd_error] Impossible d'envoyer l'erreur dans le salon {}".format(ctx.channel.id))
        # All other Errors not returned come here... And we can just print the default TraceBack.
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        #traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await self.on_error(error,ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await self.on_cmd_error(ctx,error)

    @commands.Cog.listener()
    async def on_error(self,error,ctx):
        try:
            tr = traceback.format_exception(type(error), error, error.__traceback__)
            msg = "```python\n{}\n```".format(" ".join(tr))
            if ctx == None:
                await self.senf_err_msg(f"Erreur interne\n{msg}")
            elif ctx.guild == None:
                await self.senf_err_msg(f"DM | {ctx.channel.recipient.name}\n{msg}")
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
