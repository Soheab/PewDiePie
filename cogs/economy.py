import discord
from discord.ext import commands
import random
import datetime


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tcoinimage = "<:bro_coin:541363630189576193>"

    # Cache shovel phrases
    async def shovel_cache(self):
        self.bot.econ["pos"] = await self.bot.pool.fetch("SELECT name, id FROM shovel WHERE fate = true")
        self.bot.econ["neg"] = await self.bot.pool.fetch("SELECT name, id FROM shovel WHERE fate = false")

    # Cache users
    async def user_cache(self):
        users = await self.bot.pool.fetch("SELECT guildid, userid FROM econ")
        self.bot.econ["users"] = {}
        self.bot.econ["users"]["guildid"] = {}
        for member in users:
            if not member["guildid"] in self.bot.econ["users"]["guildid"]:
                self.bot.econ["users"]["guildid"][member["guildid"]] = {}

            self.bot.econ["users"]["guildid"][member["guildid"]][member["userid"]] = {}
            g = self.bot.econ["users"]["guildid"][member["guildid"]][member["userid"]]
            g["guildid"] = member["guildid"]
            g["userid"] = member["userid"]

    # Add user
    async def up_usercache(self, guild: int, user: int):
        self.bot.econ["users"]["guildid"][guild][user] = {}
        g = self.bot.econ["users"]["guildid"][guild][user]
        g["guildid"] = guild
        g["userid"] = user

    # Add user to DB and check
    async def cad_user(ctx): # pylint: disable=no-self-argument
        # pylint: disable=E1101
        if not ctx.guild.id in ctx.bot.econ["users"]["guildid"]:
            ctx.bot.econ["users"]["guildid"][ctx.guild.id] = {}

        dc = ctx.bot.econ["users"]["guildid"][ctx.guild.id]
        if ctx.author.id in dc:
            return True
        else:
            await ctx.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", 0, ctx.author.id, ctx.guild.id)
            await Economy.up_usercache(ctx, ctx.guild.id, ctx.author.id)
            return True
        return False
        # pylint: enable=E1101

    # Economy message
    async def econmsg(self, fate: bool, ctg: int):
        if fate:
            phrases = self.bot.econ["pos"]
        else:
            phrases = self.bot.econ["neg"]
        
        try:
            phrases = random.choice(phrases)
        except IndexError:
            phrases = {}
            phrases["id"] = 1
            phrases["name"] = "You need {ctg} {tcoinimage} to add phrases."

        phraseid = phrases["id"]
        freturnp = phrases["name"].replace("{ctg}", str(format(ctg, ",d"))).replace("{tcoinimage}", self.tcoinimage)

        freturn = (freturnp, phraseid)
        return freturn

    # Shovel command
    @commands.command(aliases = ["shove;", "shove", "shv", "sh", "shb"])
    @commands.check(cad_user)
    @commands.cooldown(5, 10, commands.BucketType.member)
    async def shovel(self, ctx):
        fate = random.choice([True, False, True, False, True])
        if fate:
            ctg = random.randint(1, 1500)
        else:
            ctg = -random.randint(1, 700)
        message = await self.econmsg(fate, ctg)
        if fate:
            em = discord.Embed(color = discord.Color.green())
        else:
            em = discord.Embed(color = discord.Color.red())

        em.add_field(name = "Shovel", value = message[0])
        em.set_footer(text = f"Phrase #{message[1]:,d}")
        await ctx.send(embed = em)

        await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", ctg, ctx.author.id, ctx.guild.id)
        await self.bot.pool.execute("UPDATE econ SET uses = uses + 1 WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)

    # Amount or all
    class AmountConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                return int(argument)
            except:
                pass
            if "all" in argument:
                coins = await ctx.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
                if ctx.command.name == "transfer":
                    coins = round(coins * 0.5)
                return coins
            elif "," in argument:
                return int(argument.replace(",", ""))
            else:
                return 0

    # Pay command
    @commands.command(aliases = ["give", "givemoney", "send", "sendmoney", "add", "addmoney"])
    @commands.check(cad_user)
    async def pay(self, ctx, amount: AmountConverter, *, user: discord.Member):
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot send {self.tcoinimage} that is 0 or smaller")
            await ctx.send(embed = em)
            return

        aucash = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        if aucash >= amount:
            repcheck = await self.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", user.id, ctx.guild.id)
            if repcheck == None:
                await self.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", 0, user.id, ctx.guild.id)
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", amount, user.id, ctx.guild.id)
            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, ctx.guild.id)

            em = discord.Embed(color = discord.Color.dark_green())
            em.add_field(name = f"Sent Bro Coin to {user.name}#{user.discriminator}", value = f"{amount:,d} {self.tcoinimage} was sent to {user.mention}")
            em.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed = em)
        else:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"You do not have enough {self.tcoinimage} to send {amount:,d}")
            await ctx.send(embed = em)

    # Balance command
    @commands.command(aliases = ["bal", "money", "cash", "$", "coins", "coin", "bank"])
    async def balance(self, ctx, *, user: discord.Member = None):
        if user != None:
            uid = user
        else:
            uid = ctx.author
        baluses = await self.bot.pool.fetchrow("SELECT coins, uses FROM econ WHERE userid = $1 AND guildid = $2", uid.id, ctx.guild.id)
        if baluses == None:
            bal = 0
            uses = 0
        else:
            bal = baluses["coins"]
            uses = baluses["uses"]
        if uses == 1:
            u = "use"
        else:
            u = "uses"

        em = discord.Embed(color = discord.Color.blue())
        em.set_author(name = f"{uid.name}#{uid.discriminator}", icon_url = uid.avatar_url)
        em.add_field(name = "Bro Coins", value = f"{bal:,d} {self.tcoinimage}")
        em.add_field(name = "Shovel Uses", value = f"{uses:,d} {u}")
        await ctx.send(embed = em)

    # Leaderboard
    @commands.command(aliases = ["lb", "lead", "board", "leadboard"])
    async def leaderboard(self, ctx, param: str = ""):
        if param.lower() in ["server", "guild"]:
            coins = await self.bot.pool.fetch("SELECT * FROM econ WHERE guildid = $1 ORDER BY coins DESC LIMIT 5", ctx.guild.id)
        else:
            coins = await self.bot.pool.fetch("SELECT * FROM econ ORDER BY coins DESC LIMIT 5")
        em = discord.Embed(color = discord.Color.dark_red())

        if coins == []:
            em.add_field(name = "Leaderboard", value = "No one is using Bro Coin so there is nothing on the leaderboard")
        else:
            if param.lower() in ["server", "guild"]:
                em.set_author(name = f"{ctx.guild.name}'s Leaderboard")
            else:
                em.set_author(name = "Leaderboard")

        lbcount = 0
        for x in coins:
            lbcount += 1
            try:
                uname = self.bot.get_user(x["userid"]).name
            except AttributeError:
                uname = "User Not Found"
            try:
                gname = self.bot.get_guild(x["guildid"]).name
            except AttributeError:
                gname = "Guild Not Found"
            if len(uname) > 17:
                uname = uname[:-5] + "..."
            if len(gname) > 20:
                gname = gname[:-7] + "..."

            coins = format(x["coins"], ",d")
            uses = format(x["uses"], ",d")

            em.add_field(name = f"#{lbcount} - {uname} ({gname})", value = f"Bro Coins: {coins} {self.tcoinimage}\nShovel Uses: {uses}", inline = False)

        prefix = ctx.prefix.replace(self.bot.user.mention, f"@{self.bot.user.name}")
        em.set_footer(text = f"PROTIP: Use {prefix}shovel to collect Bro Coins")
        await ctx.send(embed = em)

    # Gamble command
    @commands.command(aliases = ["bet", "ontheline", "bets", "dice", "die"])
    @commands.check(cad_user)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def gamble(self, ctx, amount: AmountConverter = 5000):
        usercoins = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot gamble {self.tcoinimage} that is 0 or smaller")
            await ctx.send(embed = em)
            self.bot.get_command("gamble").reset_cooldown(ctx)
            return
        if usercoins >= amount:
            choice = random.choice([True, False, False, True, False])
            if choice:
                cm = "Gained"
            else:
                cm = "Lost"
                amount = -amount
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, ctx.guild.id)

            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = f"You {cm} Coins", value = f"You have {cm.lower()} {amount:,d} {self.tcoinimage} from the gamble")
            await ctx.send(embed = em)
        else:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"You do not have {amount:,d} {self.tcoinimage} to gamble")
            await ctx.send(embed = em)

            self.bot.get_command("gamble").reset_cooldown(ctx)

    # Steal command
    @commands.command(aliases = ["rob", "take", "thief", "steel", "theft", "thieves"])
    @commands.check(cad_user)
    @commands.cooldown(1, 7200, commands.BucketType.member)
    async def steal(self, ctx, *, user: discord.Member):
        if user.id == ctx.author.id:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Cannot Steal", value = "You cannot steal from yourself")
            await ctx.send(embed = em)
            self.bot.get_command("steal").reset_cooldown(ctx)
            return

        mu = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", user.id, ctx.guild.id)
        if mu == None:
            mu = 0
        coinchance = random.choice([True, False, True, True, False, False])
        if coinchance:
            giveper = random.randint(1, 5)
            give = round(mu * float(f"0.0{giveper}"))
            if 0 >= give:
                em = discord.Embed(color = discord.Color.dark_teal())
                em.add_field(name = "Not Enough", value = f"{user.mention} does not have enough coins to steal from")
                await ctx.send(embed = em)
                self.bot.get_command("steal").reset_cooldown(ctx)
                return

            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", give, user.id, ctx.guild.id)
            await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", give, ctx.author.id, ctx.guild.id)

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
        if 0 >= amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot transfer {self.tcoinimage} that is 0 or smaller")
            await ctx.send(embed = em)
            return
        guild = discord.utils.get(self.bot.guilds, name = guild)
        if guild == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Guild Not Found", value = f"{self.bot.user.name} could not find the guild")
            await ctx.send(embed = em)
            return
        transfercheck = await self.bot.pool.fetchval("SELECT transfer FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        if transfercheck:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Already Transferred", value = "You have already transferred your Bro Coins from this guild")
            await ctx.send(embed = em)
            return

        coins = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        coins = round(coins * 0.5)

        if coins >= amount:
            gc = await self.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, guild.id)
            if gc == None:
                await self.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", amount, ctx.author.id, guild.id)
            else:
                await self.bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, guild.id)
            await self.bot.pool.execute("UPDATE econ SET transfer = true WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", amount, ctx.author.id, ctx.guild.id)

            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = "Bro Coins Transferred", value = f"{amount:,d} {self.tcoinimage} has been transferred to `{guild.name}`")
            em.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed = em)
        else:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"You do not have enough Bro Coins to transfer {amount:,d} {self.tcoinimage} to `{guild.name}`")
            em.set_footer(text = "NOTE: You are only able to transfer up to 50% of your Bro Coins")
            await ctx.send(embed = em)

    # Statistics command
    @commands.command(aliases = ["stats", "stat"])
    async def statistics(self, ctx):
        econ_info = await self.bot.pool.fetchrow("SELECT COUNT(coins), AVG(coins), SUM(coins) FROM econ")

        tcusbcount = econ_info["count"]
        tcavg = econ_info["avg"]
        tcall = econ_info["sum"]
        tcsuses = await self.bot.pool.fetchval("SELECT SUM(uses) FROM econ")
        if tcsuses == 1:
            u = "use"
        else:
            u = "uses"

        tlu = await self.bot.pool.fetchrow("SELECT userid, coins FROM econ ORDER BY coins DESC LIMIT 1")
        spc = await self.bot.pool.fetchval("SELECT COUNT(name) FROM shovel")
        ft = await self.bot.pool.fetchval("SELECT COUNT(*) FROM shovel WHERE fate = true")
        ff = await self.bot.pool.fetchval("SELECT COUNT(*) FROM shovel WHERE fate = false")
        tluname = self.bot.get_user(tlu["userid"])
        if tluname == None:
            tluname = "User Not Found"

        em = discord.Embed(color = discord.Color.red())
        em.set_author(name = "Bro Coin Statistics")
        em.add_field(name = "Accounts", value = f"{tcusbcount:,d} accounts")
        em.add_field(name = "Average Amount", value = f"{round(tcavg):,d} {self.tcoinimage}")
        em.add_field(name = "Total Amount", value = f"{round(tcall):,d} {self.tcoinimage}")
        em.add_field(name = "Leading User", value = f"{tluname}")
        em.add_field(name = "Leading User Amount", value = f"{tlu['coins']:,d} {self.tcoinimage}")
        em.add_field(name = "Shovel Phrases", value = f"{spc:,d} phrases")
        em.add_field(name = "Shovel Uses", value = f"{round(tcsuses):,d} {u}")
        em.add_field(name = "Positive Phrases", value = f"{ft:,d} phrases")
        em.add_field(name = "Negative Phrases", value = f"{ff:,d} phrases")

        em.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed = em)


def setup(bot):
    bot.loop.create_task(Economy(bot).shovel_cache())
    bot.loop.create_task(Economy(bot).user_cache())
    bot.add_cog(Economy(bot))