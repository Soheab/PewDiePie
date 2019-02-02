import discord
from discord.ext import commands
import random
import datetime


class Economy:
    def __init__(self, bot):
        self.bot = bot
        self.tcoinimage = "<:bro_coin:541363630189576193>"

    async def on_ready(self):
        # Cache shovel phrases
        self.bot.pos = await self.bot.pool.fetch("SELECT * FROM shovel WHERE fate = true")
        self.bot.neg = await self.bot.pool.fetch("SELECT * FROM shovel WHERE fate = false")
    
    # Add user to DB and check
    async def cad_user(ctx): # pylint: disable=E0213
        dbcheck = await ctx.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id) # pylint: disable=E1101
        if dbcheck == None or dbcheck == []:
            await ctx.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3, $4)", 0, ctx.author.id, ctx.guild.id, 0) # pylint: disable=E1101
            return True
        else:
            return True
        return False

    # Economy message
    async def econmsg(self, fate: bool, ctg: int):
        # Check fate to determine which phrase to get
        if fate:
            phrases = self.bot.pos
        else:
            phrases = self.bot.neg
        # Get random asyncpg.Record object
        phrases = random.choice(phrases)
        # Get phrase ID
        phraseid = phrases["id"]
        # Convert
        freturnp = phrases["name"].replace("{ctg}", str(format(ctg, ",d"))).replace("{tcoinimage}", self.tcoinimage)
        # Make dictionary
        freturn = {
            "phrase": freturnp,
            "phraseid": phraseid
        }
        # Return
        return freturn

    # Shovel command
    @commands.command(aliases = ["shove;", "shove", "shv", "sh", "shb"])
    @commands.check(cad_user)
    @commands.cooldown(5, 10, commands.BucketType.member)
    async def shovel(self, ctx):
        # Pick users fate
        fate = random.choice([True, False, True, False, True])
        # Check fate
        if fate:
            ctg = random.randint(1, 1500)
        else:
            ctg = -random.randint(1, 700)
        # Get message
        message = await self.econmsg(fate, ctg)
        # Tell the user
        if fate:
            em = discord.Embed(color = discord.Color.green())
        else:
            em = discord.Embed(color = discord.Color.red())
        em.add_field(name = "Shovel", value = message["phrase"])
        em.set_footer(text = f"Phrase #{message['phraseid']:,d}")
        await ctx.send(embed = em)
        # Change values for the user in the database
        await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", ctg, ctx.author.id, ctx.guild.id)
        # Update shovel uses
        await self.bot.pool.execute("UPDATE econ SET uses = uses + 1 WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)

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

    # Pay command
    @commands.command(aliases = ["give", "givemoney", "send", "sendmoney", "add", "addmoney"])
    @commands.check(cad_user)
    async def pay(self, ctx, amount: AmountConverter, *, user: discord.Member):
        # Check if the amount is negative
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot send {self.tcoinimage} that is 0 or smaller")
            await ctx.send(embed = em)
            return
        # Check if the user has enough money
        aucash = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        if aucash >= amount:
            # Check if recipient is in the DB
            repcheck = await self.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", user.id, ctx.guild.id)
            if repcheck == None:
                # If they're not, add them
                await self.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", 0, user.id, ctx.guild.id)
            # Update value for recipient
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", amount, user.id, ctx.guild.id)
            # Update values for sender
            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, ctx.guild.id)
            # Tell the user
            em = discord.Embed(color = discord.Color.dark_green())
            em.add_field(name = f"Sent Bro Coin to {user.name}#{user.discriminator}", value = f"{amount:,d} {self.tcoinimage} was sent to {user.mention}")
            em.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed = em)
        else:
            # They do not have enough
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"You do not have enough {self.tcoinimage} to send {amount:,d}")
            await ctx.send(embed = em)

    # Balance command
    @commands.command(aliases = ["bal", "money", "cash", "$", "coins", "coin", "bank"])
    async def balance(self, ctx, *, user: discord.Member = None):
        # Get user balance
        if user != None:
            uid = user
        else:
            uid = ctx.author
        bal = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", uid.id, ctx.guild.id)
        if bal == None:
            bal = 0
        # Tell the user
        em = discord.Embed(color = discord.Color.blue())
        em.set_author(name = f"{uid.name}#{uid.discriminator}", icon_url = uid.avatar_url)
        em.add_field(name = "Bro Coins", value = f"{bal:,d} {self.tcoinimage}")
        await ctx.send(embed = em)

    # Leaderboard
    @commands.command(aliases = ["lb", "lead", "board", "leadboard"])
    async def leaderboard(self, ctx):
        # Get coins by order
        coins = await self.bot.pool.fetch("SELECT * FROM econ ORDER BY coins DESC LIMIT 5")
        # Make embed
        em = discord.Embed(color = discord.Color.dark_red())
        # Make sure something is in the embed
        if coins == []:
            em.add_field(name = "Leaderboard", value = "No one is using Bro Coin so there is nothing on the leaderboard :(")
        else:
            em.set_author(name = "Leaderboard")
        # Loop
        lbcount = 0
        for x in coins:
            lbcount += 1
            try:
                uname = self.bot.get_user(x["userid"]).name
                gname = self.bot.get_guild(x["guildid"]).name
            except AttributeError:
                uname = "User Not Found"
                gname = "Guild Not Found"
            # Check if names are too big
            if len(uname) > 17:
                uname = uname[:-5] + "..."
            if len(gname) > 20:
                gname = gname[:-7] + "..."
            # Put coins in a human readable format
            coins = format(x["coins"], ",d")
            # Shovel command uses
            uses = format(x["uses"], ",d")
            # Add field to embed
            em.add_field(name = f"#{lbcount} - {uname} ({gname})", value = f"Bro Coins: {coins} {self.tcoinimage} Shovel Uses: {uses}", inline = False)
        # Set footer
        em.set_footer(text = "PROTIP: Use p.shovel to collect Bro Coins")
        # Send
        await ctx.send(embed = em)

    # Gamble command
    @commands.command(aliases = ["bet", "ontheline", "bets", "dice", "die"])
    @commands.check(cad_user)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def gamble(self, ctx, amount: AmountConverter):
        # Get user stuff
        usercoins = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        # Check if the user is using negatives
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot gamble {self.tcoinimage} that is 0 or smaller")
            await ctx.send(embed = em)
            self.bot.get_command("gamble").reset_cooldown(ctx)
            return
        # See if they have enough coins
        if usercoins >= amount:
            # Gamble (all or nothing)
            choice = random.choice([True, False, False, False, False])
            if choice:
                cm = "Gained"
            else:
                cm = "Lost"
                amount = -amount
            # Update coins
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, ctx.guild.id)
            # Tell user
            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = f"You {cm} Coins", value = f"You have {cm.lower()} {amount:,d} {self.tcoinimage} from the gamble")
            await ctx.send(embed = em)
        else:
            # User does not have enough coins
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"You do not have {amount:,d} {self.tcoinimage} to gamble")
            await ctx.send(embed = em)
            # Reset cooldown
            self.bot.get_command("gamble").reset_cooldown(ctx)

    # Steal command
    @commands.command(aliases = ["rob", "take", "thief", "steel", "theft", "thieves"])
    @commands.check(cad_user)
    @commands.cooldown(1, 7200, commands.BucketType.member)
    async def steal(self, ctx, *, user: discord.Member):
        # Check if the user is themselves
        if user.id == ctx.author.id:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Cannot Steal", value = "You cannot steal from yourself")
            await ctx.send(embed = em)
            # Reset cooldown
            self.bot.get_command("steal").reset_cooldown(ctx)
            # Return
            return
        # Get mentioned users coins
        mu = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", user.id, ctx.guild.id)
        if mu == None:
            mu = 0
        # Create chance of actually getting coins from them
        coinchance = random.choice([True, False, True, True, False, False])
        if coinchance:
            # Random number for negative
            giveper = random.randint(1, 5)
            # Calculate how much to give
            give = round(mu * float(f"0.0{giveper}"))
            # Check if the amount is negative
            if 0 >= give:
                em = discord.Embed(color = discord.Color.dark_teal())
                em.add_field(name = "Not Enough", value = f"{user.mention} does not have enough coins to steal from")
                await ctx.send(embed = em)
                # Reset cooldown
                self.bot.get_command("steal").reset_cooldown(ctx)
                # Return
                return
            # Remove coins from mentioned user
            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", give, user.id, ctx.guild.id)
            # Add coins to author
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", give, ctx.author.id, ctx.guild.id)
            # Tell the user
            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = f"Stole from {user.name}", value = f"You stole {give:,d} {self.tcoinimage} from {user.mention}")
            em.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed = em)
        else:
            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = "Caught by the Police", value = f"Looks like this time {user.mention} got off the hook since the police showed up")
            await ctx.send(embed = em)

    # Guild Bro Coin transfer command
    @commands.command()
    @commands.check(cad_user)
    async def transfer(self, ctx, amount: AmountConverter, *, guild: str):
        # Check if amount is 0 or below
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot transfer {self.tcoinimage} that is 0 or smaller")
            await ctx.send(embed = em)
            return
        # Check for guild
        guild = discord.utils.get(self.bot.guilds, name = guild)
        # Guild Not Found
        if guild == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Guild Not Found", value = f"{self.bot.user.name} could not find the guild")
            await ctx.send(embed = em)
            return
        # Transferred already
        transfercheck = await self.bot.pool.fetchval("SELECT transfer FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        if transfercheck:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Already Transferred", value = "You have already transferred your Bro Coins to this guild")
            await ctx.send(embed = em)
            return
        # Get user coins
        coins = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        # Calculate 50% of users coins
        coins = round(coins * 0.5)
        # Check if the user has enough coins
        if coins >= amount:
            # User has enough coins
            # Check if the user is already in the DB for the guild
            gc = await self.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, guild.id)
            if gc == None:
                # Add
                await self.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", amount, ctx.author.id, guild.id)
            else:
                # Update
                await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, guild.id)
            # Set transfer as true
            await self.bot.pool.execute("UPDATE econ SET transfer = true WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
            # Remove coins from the user which this command is being invoked in
            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, ctx.guild.id)
            # Tell the user
            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = "Bro Coins Transferred", value = f"{amount:,d} {self.tcoinimage} has been transferred to `{guild.name}`")
            em.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed = em)
        else:
            # User does not have enough coins
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"You do not have enough Bro Coins to transfer {amount:,d} {self.tcoinimage} to `{guild.name}`")
            em.set_footer(text = "NOTE: You are only able to transfer up to 50% of your Bro Coins")
            await ctx.send(embed = em)
    
    # Statistics command
    @commands.command(aliases = ["stats", "stat"])
    async def statistics(self, ctx):
        # Get tables from the economy table that are needed here
        econ_info = await self.bot.pool.fetchrow("SELECT COUNT(coins), AVG(coins), SUM(coins) FROM econ")
        # Bro Coin userbase count
        tcusbcount = econ_info["count"]
        # Average Bro Coins
        tcavg = econ_info["avg"]
        # All Bro Coins
        tcall = econ_info["sum"]
        # Leading economy user
        tlu = await self.bot.pool.fetchrow("SELECT userid, coins FROM econ ORDER BY coins DESC LIMIT 1")
        # Shovel phrases count
        spc = await self.bot.pool.fetchval("SELECT COUNT(name) FROM shovel")
        try:
            tluname = self.bot.get_user(tlu["userid"])
        except AttributeError:
            tluname = "User Not Found"
        # Embed
        em = discord.Embed(color = discord.Color.red())
        em.set_author(name = "Bro Coin Statistics")
        em.add_field(name = "Accounts", value = f"{tcusbcount:,d} accounts")
        em.add_field(name = "Average Amount", value = f"{round(tcavg):,d} {self.tcoinimage}")
        em.add_field(name = "Total Amount", value = f"{round(tcall):,d} {self.tcoinimage}")
        em.add_field(name = "Leading User", value = f"{tluname}")
        em.add_field(name = "Leading User Amount", value = f"{tlu['coins']:,d} {self.tcoinimage}")
        em.add_field(name = "Shovel Phrases", value = f"{spc:,d} phrases")
        # Timestamp
        em.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(Economy(bot))