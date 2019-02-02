import discord
from discord.ext import commands


class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown) == False:
            # Reset cooldown if there is one
            try:
                self.bot.get_command(ctx.command.name).reset_cooldown(ctx)
            except AttributeError:
                pass
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Missing Permissions", value = "You are missing permissions to run this command")
            await ctx.send(embed = em)
        elif isinstance(error, commands.BotMissingPermissions):
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Bot Missing Permissions", value = f"{self.bot.user.name} doesn't have permissions to run this command")
            await ctx.send(embed = em)
        elif isinstance(error, discord.HTTPException):
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: HTTP Exception", value = "There was an error connecting to Discord. Please try again")
            await ctx.send(embed = em)
        elif isinstance(error, commands.CommandInvokeError):
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Command Invoke Error", value = f"There was an issue running the command.\nError: `{error}`")
            await ctx.send(embed = em)
        elif isinstance(error, commands.MissingRequiredArgument):
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Missing Argument", value = f"""
            I'm missing a parameter, specifically `{error.param}`. Please make sure you entered the command in correctly then try again.
            """)
            await ctx.send(embed = em)
        elif isinstance(error, commands.NotOwner):
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Not Owner", value = "You are not the owner")
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
            # Send embed
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Error: Cooldown", value = f"Please wait {hours} {ist} {minutes} {ist1} {seconds} to use `{ctx.command.name}` again")
            if ctx.command.name == "shovel":
                await ctx.send(embed = em, delete_after = error.retry_after)
            else:
                await ctx.send(embed = em)
        else:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Unknown Error", value = f"An unexpected error occurred.\nError: `{error}`")
            await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))