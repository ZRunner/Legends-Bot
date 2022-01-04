import importlib
from nextcord.ext import commands

admins_id = [279568324260528128, 375598088850505728,
             281404141841022976, 552273019020771358]
#Z_runner - Aragorn - reddemoon - Z_Jumper


async def check_admin(ctx):
    if type(ctx) == commands.Context:
        user = ctx.author
    else:
        user = ctx
    if type(user) == str and user.isnumeric():
        user = int(user)
    elif type(user) != int:
        user = user.id
    return user in admins_id


class ReloadsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "reloads"

    async def reload_cogs(self, ctx: commands.Context, cogs):
        errors_cog = self.bot.cogs["ErrorsCog"]
        if len(cogs) == 1 and cogs[0] == 'all':
            cogs = sorted([x.file for x in self.bot.cogs.values()])
        reloaded_cogs = list()
        for cog in cogs:
            fcog = cog
            if not cog.startswith("fcts."):
                fcog = "fcts." + fcog
            try:
                self.bot.reload_extension(fcog)
            except commands.errors.ExtensionNotLoaded:
                try:
                    fcog = importlib.import_module(cog)
                    importlib.reload(fcog)
                except:
                    await ctx.send("Le module {} n'a pas été chargé".format(cog))
                else:
                    await ctx.send(f"La lib {cog} a été rechargée")
            except ModuleNotFoundError:
                await ctx.send("Le module {} est introuvable".format(cog))
            except Exception as e:
                await errors_cog.on_error(e, ctx)
                await ctx.send(f'**`ERREUR:`** {type(e).__name__} - {e}')
            else:
                print("Module {} rechargé".format(cog))
                reloaded_cogs.append(cog)
                self.bot.log.debug("Module {} rechargé".format(cog))
        await ctx.bot.cogs['UtilitiesCog'].count_lines_code()
        if len(reloaded_cogs) > 0:
            await ctx.send("Ces modules ont été correctement rechargés : {}".format(", ".join(reloaded_cogs)))

    @commands.command(name="add_cog")
    @commands.check(check_admin)
    async def add_cog(self, ctx: commands.Context, name):
        """Ajouter un cog au bot"""
        if not ctx.author.id in admins_id:
            return
        try:
            self.bot.load_extension('fcts.'+name)
            await ctx.send("Cog '{}' ajouté !".format(name))
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name="del_cog", aliases=['remove_cog'])
    @commands.check(check_admin)
    async def rm_cog(self, ctx: commands.Context, name):
        """Enlever un cog au bot"""
        if not ctx.author.id in admins_id:
            return
        try:
            self.bot.unload_extension('fcts.'+name)
            await ctx.send("Cog '{}' désactivé !".format(name))
        except Exception as e:
            await ctx.send(str(e))


def setup(bot):
    bot.add_cog(ReloadsCog(bot))
