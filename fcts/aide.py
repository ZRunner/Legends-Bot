import nextcord, re, inspect
from nextcord.ext import commands

class HelpCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file = "aide"
        bot.remove_command("help")
        self._mentions_transforms = {
    '@everyone': '@\u200beveryone',
    '@here': '@\u200bhere'}
        self._mention_pattern = re.compile('|'.join(self._mentions_transforms.keys()))
        self.send_in_dm = True

    
    @commands.command(name="help")
    @commands.cooldown(1,5,commands.BucketType.user)
    async def help_cmd(self, ctx: commands.Context,*commands : str):
        """Obtenir de l'aide sur une commande"""
        try:
            if len(commands) == 0:
                await self.help_command(ctx)
            else:
                await self.help_command(ctx,commands)
        except Exception as e:
            await self.bot.cogs["ErrorsCog"].on_error(e,ctx)
            if len(commands) == 0:
                await self._default_help_command(ctx)
            else:
                await self._default_help_command(ctx,commands)


    async def help_command(self, ctx: commands.Context, commands=()):
        """Main command for the creation of the help message
If the bot can't send the new command format, it will try to send the old one. Enable "Embed Links" permission for better rendering."""
        if self.send_in_dm:
            destination = ctx.message.author.dm_channel
            if destination == None:
                await ctx.message.author.create_dm()
                destination = ctx.message.author.dm_channel
            await self.bot.cogs["UtilitiesCog"].suppr(ctx.message)
        else:
            destination = ctx.message.channel
        
        def repl(obj):
            return self._mentions_transforms.get(obj.group(0), '')

        if len(commands) == 0:  #aucune commande
            pages = await self.all_commands(ctx)
        elif len(commands) == 1:    #Nom de cog/commande unique ?
            name = self._mention_pattern.sub(repl, commands[0])
            command = None
            if name in self.bot.cogs:
                cog = self.bot.cogs[name]
                pages = await self.cog_commands(ctx,cog)
            else:
                command = self.bot.all_commands.get(name)
                if command is None:
                    await destination.send(await self.bot._(ctx, "help.cmd_not_found", cmd=name))
                    return
                pages = await self.cmd_help(ctx,command)
        else:  #nom de sous-commande ?
            name = self._mention_pattern.sub(repl, commands[0])
            command = self.bot.all_commands.get(name)
            if command is None:
                await destination.send(await self.bot._(ctx, "help.cmd_not_found", cmd=name))
                return
            for key in commands[1:]:
                try:
                    key = self._mention_pattern.sub(repl, key)
                    command = command.all_commands.get(key)
                    if command is None:
                        await destination.send(await self.bot._(ctx, "help.subcmd_not_found", cmd=key))
                        return
                except AttributeError:
                    await destination.send(await self.bot._(ctx, "help.no_subcmd", cmd=command))
                    return
            pages = await self.cmd_help(ctx,command)

        me = destination.me if type(destination)==nextcord.DMChannel else destination.guild.me
        ft = await self.bot._(ctx, 'help.more_info', p=ctx.prefix)
        if destination.permissions_for(me).embed_links:
            for page in pages:
                embed = self.bot.cogs["EmbedCog"].Embed(desc=page,footer_text=ft.format(await self.bot.get_prefix(ctx.message)),fields=[]).update_timestamp().discord_embed()
                if ctx.guild != None:
                    embed.colour = ctx.guild.me.color if ctx.guild.me.color != nextcord.Colour(16295964).default() else nextcord.Colour(16295964)
                else:
                    embed.colour = nextcord.Colour(16295964)
                await destination.send(embed=embed)
        else:
            for page in pages:
                await destination.send(page)
        if self.send_in_dm:
            try:
                await ctx.message.delete()
            except:
                pass

    async def display_cmd(self, cmd):
        return "• **{}**\t\t*{}*".format(cmd.name,cmd.short_doc.strip()) if len(cmd.short_doc)>0 else "• **{}**".format(cmd.name)

    def sort_by_name(self,cmd):
            return cmd.name

    async def all_commands(self, ctx: commands.Context):
        """Create pages for every bot command"""        
        cmds = sorted([c for c in ctx.bot.commands],key=self.sort_by_name)
        helpmsg = ""
        for cmd in cmds:
            try:
                if (await cmd.can_run(ctx))==False or cmd.hidden==True or cmd.enabled==False:
                    continue
            except Exception as e:
                if not "nextcord.ext.commands.errors" in str(type(e)):
                    await ctx.send("`Error:` {}".format(e))
                    await self.bot.cogs['ErrorsCog'].on_error(e,ctx)
                    return []
                else:
                    continue
            helpmsg += "\n"+await self.display_cmd(cmd)
        #tr = ["Administration","Autres"]
        #if len(modhelp+otherhelp)<1900:
        #    return ["__• **{}**__\n{}".format(tr[0],modhelp) + "\n\n__• **{}**__\n{}".format(tr[1],otherhelp)]
        #else:
        #    return ["__• **{}**__\n{}".format(tr[0],modhelp) , "\n\n__• **{}**__\n{}".format(tr[1],otherhelp)]
        title = await self.bot._(ctx, 'help.cmds_list')
        return ["__**{}**__\n{}".format(title, helpmsg)]

    async def cog_commands(self, ctx: commands.Context, cog):
        """Create pages for every command of a cog"""
        description = inspect.getdoc(cog)
        page = ""
        form = "**{}**\n\n {} \n{}"
        pages = list()
        cog_name = cog.__class__.__name__
        if description == None:
            description = await self.bot._(ctx, 'help.no_desc_cog')
        for cmd in sorted([c for c in self.bot.commands],key=self.sort_by_name):
            try:
                if (await cmd.can_run(ctx))==False or cmd.hidden==True or cmd.enabled==False or cmd.cog_name != cog_name:
                    continue
            except Exception as e:
                if not "nextcord.ext.commands.errors" in str(type(e)):
                    await self.bot.cogs['ErrorsCog'].on_cmd_error(ctx, e)
                    return []
                else:
                    continue
            text = await self.display_cmd(cmd)
            if len(page+text)>1900:
                pages.append(form.format(cog_name,description,page))
                page = text
            else:
                page += "\n"+text
        pages.append(form.format(cog_name,description,page))
        return pages
    
    async def cmd_help(self, ctx: commands.Context,cmd):
        """Create pages for a command explanation"""
        desc = cmd.description if cmd.description not in [None,''] else await self.bot._(ctx, 'help.no_desc_cmd')
        if desc=='':
            desc = cmd.help
        prefix = await self.bot.get_prefix(ctx.message)
        syntax = cmd.signature.replace(" ","** ",1) if " " in cmd.signature else cmd.signature+"**"
        if type(cmd)==commands.core.Group:
            subcmds = "\n\n__{}__".format(await self.bot._(ctx, 'help.subcmds_list'))
            sublist = list()
            for x in sorted(cmd.all_commands.values(),key=self.sort_by_name):
                if x.enabled==False:
                    continue
                if x.hidden==False and x.name not in sublist:
                    subcmds += "\n- {} {}".format(x.name,"*({})*".format(x.short_doc) if len(x.short_doc)>0 else "")
                    sublist.append(x.name)
        else:
            subcmds = ""
        return ["**{}{}\n\n{}\n*Cog: {}*{}".format(prefix,syntax,desc,cmd.cog_name,subcmds)]


    async def _default_help_command(self, ctx: commands.Context, commands=()):
        bot = ctx.bot
        if self.send_in_dm:
            destination = ctx.message.author
            await bot.cogs["UtilitiesCog"].suppr(ctx.message)
        else :
            destination = ctx.message.channel
        def repl(obj):
            return self._mentions_transforms.get(obj.group(0), '')

            # help by itself just lists our own commands.
        if len(commands) == 0:
            pages = await bot.formatter.format_help_for(ctx, bot)
        elif len(commands) == 1:
            # try to see if it is a cog name
            name = self._mention_pattern.sub(repl, commands[0])
            command = None
            if name in bot.cogs:
                command = bot.cogs[name]
            else:
                command = bot.all_commands.get(name)
                if command is None:
                    await destination.send(bot.command_not_found.format(name))
                    return

            pages = await bot.formatter.format_help_for(ctx, command)
        else:
            name = self._mention_pattern.sub(repl, commands[0])
            command = bot.all_commands.get(name)
            if command is None:
                await destination.send(bot.command_not_found.format(name))
                return

            for key in commands[1:]:
                try:
                    key = self._mention_pattern.sub(repl, key)
                    command = command.all_commands.get(key)
                    if command is None:
                        await destination.send(bot.command_not_found.format(key))
                        return
                except AttributeError:
                    await destination.send(await self.bot._(ctx, "help.no_subcmd", cmd=command))
                    return

            pages = await bot.formatter.format_help_for(ctx, command)

        if bot.pm_help is None:
            characters = sum(map(len, pages))
            # modify destination based on length of pages.
            if characters > 1000:
                destination = ctx.message.author

        for page in pages:
            await destination.send(page)


def setup(bot):
    bot.add_cog(HelpCog(bot))
