import discord
from discord.ext import commands


class Prefixes:
    def __init__(self, bot):
        self.bot = bot

    # Set prefix tutorial command
    @commands.command(aliases = ["prefixtutorial", "tutprefix"])
    async def prefixtut(self, ctx):
        em = discord.Embed(color = discord.Color.dark_green())
        em.add_field(name = "Command Use", value = f"""
        Sets the prefix for the current server. You must have the manage messages permission to use this command.
        **Set or change prefix**
        `p.setprefix [prefix here]`
        **Revert back to default prefix**
        `p.setprefix`
        **Show current prefix**
        `p.prefix` (does not require any special permissions to view)
        """)
        await ctx.send(embed = em)

    # Returns bot prefix in the current guild
    @commands.command(aliases = ["currentprefix", "botprefix", "serverprefix", "guildprefix"])
    async def prefix(self, ctx):
        # Get prefix
        prefixes = await self.bot.pool.fetchval("SELECT prefix FROM prefixes WHERE guildid = $1", ctx.guild.id)
        if prefixes == None:
            prefix = ""
            formatted = []
            for x in self.bot.default_prefixes:
                formatted.append(x.lower())
            formatted = list(dict.fromkeys(formatted))
            for x in formatted:
                prefix += f"{x}, "
            if prefix.endswith(", "):
                prefix = prefix[:-2]
        else:
            prefix = prefixes
        # Send
        em = discord.Embed(color = discord.Color.red())
        em.add_field(name = "Current Prefix", value = f"The current prefix for {self.bot.user.mention} is `{prefix}`")
        await ctx.send(embed = em)

    # Custom prefix
    @commands.command(aliases = ["sprefix"])
    @commands.has_permissions(manage_messages = True)
    async def setprefix(self, ctx, *, prefix: str = None):
        # Check if custom prefix exceeds the 30 character limit
        if prefix != None:
            if len(prefix) > 30:
                em = discord.Embed(color = discord.Color.dark_teal())
                em.add_field(name = "Prefix Character Limit Exceeded", value = "Prefixes can only be 30 characters or less")
                await ctx.send(embed = em)
                return
        # Check if prefix is already in the database
        gchck = await self.bot.pool.fetchrow("SELECT * FROM prefixes WHERE guildid = $1", ctx.guild.id)
        # Checking and setting
        if gchck == None:
            if prefix != None:
                # Insert into row
                await self.bot.pool.execute("INSERT INTO prefixes VALUES ($1, $2)", ctx.guild.id, prefix)
                # Tell user
                em = discord.Embed(color = discord.Color.red())
                em.add_field(name = "Set Prefix", value = f"{self.bot.user.mention}'s prefix has been set to `{prefix}`")
                await ctx.send(embed = em)
            else:
                # Tell user
                em = discord.Embed(color = discord.Color.dark_teal())
                em.add_field(name = "Error: Prefix Not Set", value = "Please specify a prefix to use")
                await ctx.send(embed = em)
                return
        else:
            if prefix == None:
                # Delete from database
                await self.bot.pool.execute("DELETE FROM prefixes WHERE guildid = $1", ctx.guild.id)
                # Tell user
                em = discord.Embed(color = discord.Color.red())
                em.add_field(name = "Prefix Removed", value = f"{self.bot.user.mention}'s prefix has been set back to the default")
                await ctx.send(embed = em)
            else:
                # Update row
                await self.bot.pool.execute("UPDATE prefixes SET prefix = $1 WHERE guildid = $2", prefix, ctx.guild.id)
                # Tell user
                em = discord.Embed(color = discord.Color.red())
                em.add_field(name = "Set Prefix", value = f"{self.bot.user.mention}'s prefix has been set to `{prefix}`")
                await ctx.send(embed = em)
        # Update the prefix cache
        if prefix != None:
            self.bot.prefixes[ctx.guild.id] = prefix
        else:
            self.bot.prefixes.pop(ctx.guild.id)


def setup(bot):
    bot.add_cog(Prefixes(bot))