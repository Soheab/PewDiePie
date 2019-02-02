import discord
from discord.ext import commands
import datetime


class EconomyOwner:
    def __init__(self, bot):
        self.bot = bot
        self.tcoinimage = "<:tseries_coin:529144538225311774>"

    # Amount or all
    class AmountConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                return int(argument)
            except:
                pass
            if "all" in argument:
                # Get users coins
                coins = await ctx.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
                return coins
            elif "," in argument:
                return int(argument.replace(",", ""))
            else:
                return 0

    # Add T-Coins command (REQ_BOT_OWNER)
    @commands.command()
    @commands.is_owner()
    async def addcoins(self, ctx, amount: AmountConverter, *, user: discord.Member):
        # Check if the amount specified is too small
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot add T-Coins to users that is 0 or smaller")
            await ctx.send(embed = em)
            return
        # Check if the user is in the DB
        usercheck = await self.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", user.id, ctx.guild.id)
        if usercheck == None:
            # Add user (INSERT)
            await self.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", amount, user.id, ctx.guild.id)
        else:
            # Add user (UPDATE)
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", amount, user.id, ctx.guild.id)
        # Tell user
        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Coins Added", value = f"{amount:,d} {self.tcoinimage} has been added to {user.mention}")
        em.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed = em)

    # Remove T-Coins command (REQ_BOT_OWNER)
    @commands.command()
    @commands.is_owner()
    async def removecoins(self, ctx, amount: AmountConverter, *, user: discord.Member):
        # Check if the amount specified is too small
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot remove T-Coins to users that is 0 or smaller")
            await ctx.send(embed = em)
            return
        # Check if the user is in the DB
        usercheck = await self.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", user.id, ctx.guild.id)
        if usercheck == None:
            # Remove user (INSERT)
            await self.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", -amount, user.id, ctx.guild.id)
        else:
            # Remove user (UPDATE)
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", -amount, user.id, ctx.guild.id)
        # Tell user
        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Coins Removed", value = f"{amount:,d} {self.tcoinimage} has been removed from {user.mention}")
        em.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(EconomyOwner(bot))