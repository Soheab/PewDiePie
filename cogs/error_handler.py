import discord
from discord.ext import commands


class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown) == False:
            try:
                self.bot.get_command(ctx.command.name).reset_cooldown(ctx)
            except AttributeError:
                pass

        errors = {
            commands.MissingPermissions: {"msg": "You are missing permissions to run this command.", "ty": "Missing Permissions"},
            commands.BotMissingPermissions: {"msg": "The bot does not have permissions to run this command.", "ty": "Bot Missing Permissions"},
            discord.HTTPException: {"msg": "There was an error connecting to Discord. Please try again.", "ty": "HTTP Exception"},
            commands.CommandInvokeError: {"msg": "There was an issue running the command.\n[ERROR]", "ty": "Command Invoke Error"},
            commands.NotOwner: {"msg": "You are not the owner.", "ty": "Not Owner"}
        }

        ex = (commands.MissingRequiredArgument, commands.CommandOnCooldown, commands.CommandNotFound)

        if not isinstance(error, ex):
            ets = errors.get(error.__class__)
            if ets == None:
                ets["msg"] = "An unexpected error has occurred.\n[ERROR]",
                ets["ty"] = "Unexpected Error"
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = f"Error: {ets['ty']}", value = ets["msg"].replace("[ERROR]", f"```\n{error}\n```"))
            await ctx.send(embed = em)

        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Missing Argument", value = f"""
            I'm missing a parameter, `{str(error.param).partition(':')[0]}`.
            Make sure you ran the command correctly then try again.
            """)
            await ctx.send(embed = em)
        elif isinstance(error, commands.CommandOnCooldown):
            # Time
            seconds = int(error.retry_after)
            seconds = round(seconds, 2)
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            # Timing wording
            if hours > 1:
                hours = f"{hours} hours"
            elif hours == 1:
                hours = f"{hours} hour"
            else:
                hours = ""
            if minutes > 1:
                minutes = f"{minutes} minutes"
            elif minutes == 1:
                minutes = f"{minutes} minute"
            else:
                minutes = ""
            if seconds > 1:
                seconds = f"{seconds} seconds"
            elif seconds == 1:
                seconds = f"{seconds} second"
            else:
                seconds = ""
            # Ist
            if hours != "":
                ist = "and"
            else:
                ist = ""
            if seconds != "":
                if minutes != "":
                    ist1 = "and"
                else:
                    ist1 = ""
            else:
                ist1 = ""

            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Cooldown", value = f"Please wait {hours} {ist} {minutes} {ist1} {seconds} to use `{ctx.command.name}` again")
            if ctx.command.name == "shovel":
                await ctx.send(embed = em, delete_after = error.retry_after)
            else:
                await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))