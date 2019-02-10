import discord
from discord.ext import commands
import aiohttp
import asyncio
import sys
sys.path.append("../")
import config


class Subscribe:
    def __init__(self, bot):
        self.bot = bot

    # Cache subgap information
    async def subgcache(self):
        self.bot.subgap = {"guild": {}}
        information = await self.bot.pool.fetch("SELECT * FROM subgap")
        for x in information:
            self.bot.subgap["guild"][x["guildid"]] = {}
            guild = self.bot.subgap["guild"][x["guildid"]]
            guild["channelid"] = x["channelid"]
            guild["guildid"] = x["guildid"]
            guild["msgid"] = x["msgid"]
            guild["count"] = x["count"]

        if "subgap" in self.bot.tasks:
            self.bot.tasks["subgap"].cancel()

        self.bot.tasks["subgap"] = self.bot.loop.create_task(self.subgtask())

    # Update subgap cache command
    async def subgupcache(self, message: int, guild: int, channel: int, count: int):
        self.bot.subgap["guild"][guild] = {}
        gdict = self.bot.subgap["guild"][guild]
        gdict["channelid"] = channel
        gdict["guildid"] = guild
        gdict["msgid"] = message
        gdict["count"] = count

    # Gets the PewDiePie and T-Series subcount
    @commands.command(aliases = ["subscribercount"])
    async def subcount(self, ctx, p: str = "", stping: bool = True):
        if stping:
            await ctx.channel.trigger_typing()
        base = "https://www.googleapis.com/youtube/v3"
        apikey = config.ytdapi
        end = "&key=" + apikey
        pci = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        tci = "UCq-Fj5jknLsUf-MWSy4_brA"

        async with aiohttp.ClientSession() as sccs:
            async with sccs.get(base + "/channels?part=snippet,contentDetails,statistics&id=" + tci + end) as treq:
                tjson = await treq.json()

        async with aiohttp.ClientSession() as anccs:
            async with anccs.get(base + "/channels?part=snippet,contentDetails,statistics&id=" + pci + end) as preq:
                pjson = await preq.json()

        tsc = tjson["items"][0]["statistics"]["subscriberCount"]
        psc = pjson["items"][0]["statistics"]["subscriberCount"]

        tscint = int(tsc)
        pscint = int(psc)
        trf = format(tscint, ",d")
        prf = format(pscint, ",d")

        if pscint >= tscint:
            pscp = pscint - tscint
            pscpts = f"PewDiePie is leading with {pscp:,d} more subscribers than T-Series"
        else:
            pscp = tscint - pscint
            pscpts = f"T-Series is leading with {pscp:,d} more subscribers than PewDiePie"

        if p.lower() == "retint":
            retdict = {
                "t": tscint,
                "p": pscint,
                "l": pscpts
            }
            return retdict
        else:
            em = discord.Embed(color = discord.Color.red())
            if pscint >= tscint:
                em.add_field(name = "PewDiePie Sub Count", value = prf)
                em.add_field(name = "T-Series Sub Count", value = trf)
            else:
                em.add_field(name = "T-Series Sub Count", value = trf)
                em.add_field(name = "PewDiePie Sub Count", value = prf)
            em.add_field(name = "Leading Channel", value = pscpts, inline = False)
            em.add_field(name = "Real Time Subcount Websites", value = """
            [T-Series](https://socialblade.com/youtube/user/tseries/realtime) | [PewDiePie](https://socialblade.com/youtube/user/pewdiepie/realtime)
            """, inline = False)
            await ctx.send(embed = em)

    # Authorization checking
    async def authcheck(self, gid: int):
        chck = await self.bot.pool.fetch("SELECT * FROM authorized")
        for c in chck:
            if str(gid) in str(c["guildid"]):
                return True
            else:
                continue
        return False

    # Update subgap background task
    async def subgtask(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            run = True
            amount = 10
            while run:
                try:
                    for guild_id in self.bot.subgap["guild"]:
                        message = self.bot.subgap["guild"][guild_id]["msgid"]
                        guild = guild_id
                        channel = self.bot.subgap["guild"][guild_id]["channelid"]
                        await self.subgloop(message, guild, channel)
                    run = False
                    amount = 10
                except RuntimeError:
                    if amount == 0:
                        print("Subgap tries exceeded. Restarting background task")
                        await self.subgcache()
                    else:
                        await asyncio.sleep(1)
                        amount -= 1
                        continue
            await asyncio.sleep(30)

    # Subcount gap command
    @commands.command(name = "subgap")
    @commands.has_permissions(administrator = True)
    async def subgstart(self, ctx, r: int = 10000000):
        # ====START CHECKS====

        check = await self.authcheck(ctx.guild.id)
        if check:
            pass
        else:
            emb = discord.Embed(color = discord.Color.dark_teal())
            emb.add_field(name = "Not Authorized", value = """
            Your guild is not authorized to use this command. Visit the [support server](https://discord.gg/we4DQ5u) to request authorization.
            """)
            await ctx.send(embed = emb)
            return

        sgchck = await self.bot.pool.fetchrow("SELECT * FROM subgap WHERE guildid = $1", ctx.guild.id)
        if sgchck != None:
            emd = discord.Embed(color = discord.Color.dark_teal())
            emd.add_field(name = "Subgap Command In Use", value = """
            The subgap command is already being used in your server. Please delete the message containing the subgap command then try again after 30 seconds.
            """)
            await ctx.send(embed = emd)
            return

        # ====END CHECKS====

        # ====START ORIGINAL MESSAGE====

        stsubinfo = await ctx.invoke(self.bot.get_command("subcount"), p = "retint", stping = False)

        em = discord.Embed(color = discord.Color.blurple())
        em.add_field(name = "Leading Channel", value = stsubinfo["l"])
        stmsg = await ctx.send(embed = em)

        # ====END ORIGINAL MESSAGE====

        await self.bot.pool.execute("INSERT INTO subgap VALUES ($1, $2, $3, $4)", stmsg.id, ctx.channel.id, ctx.guild.id, r)
        await asyncio.sleep(30)
        await self.subgupcache(stmsg.id, ctx.guild.id, ctx.channel.id, r)

    # SUBGAP LOOP
    async def subgloop(self, message: int, guild: int, channel: int):
        try:
            guildobj = self.bot.get_guild(guild)
            channel = guildobj.get_channel(channel)
            await channel.get_message(message)
        except (AttributeError, discord.DiscordException, commands.CommandError):
            self.bot.subgap["guild"].pop(guild)
            await self.bot.pool.execute("DELETE FROM subgap WHERE msgid = $1 AND guildid = $2", message, guild)
            return False

        subinfo = await self.subcount.callback(None, None, "retint", False) # pylint: disable=no-member
        await self.subgedit(channel.id, message, subinfo["l"])
        await self.bot.pool.execute("UPDATE subgap SET count = count - 1 WHERE msgid = $1 AND guildid = $2 AND channelid = $3", message, guild, channel.id)

    # SUBGAP EDIT
    async def subgedit(self, c: int, m: int, lndmsg: str):
        em = discord.Embed(color = discord.Color.blurple())
        em.add_field(name = "Leading Channel", value = lndmsg)

        channel = self.bot.get_channel(c)
        message = await channel.get_message(m)
        await message.edit(embed = em)

    # Log subgap tasks to the console
    async def on_ready(self):
        for x in self.bot.subgap["guild"]:
            g = self.bot.subgap
            print(f"Started subgap! Msg ID: {g['guild'][x]['msgid']}  Guild ID: {x}  Channel ID: {g['guild'][x]['channelid']}")


def setup(bot):
    bot.loop.create_task(Subscribe(bot).subgcache())
    bot.add_cog(Subscribe(bot))
