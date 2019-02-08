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
        # Check if current task is running then cancel if it is
        if hasattr(self.bot, "subgap_task"):
            self.bot.subgap_task.cancel()
        # Start updating subgap messages again
        self.bot.subgap_task = self.bot.loop.create_task(self.subgtask())

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
        # Use aiohttp to make GET requests for T-Series
        async with aiohttp.ClientSession() as sccs:
            # T-Series
            async with sccs.get(base + "/channels?part=snippet,contentDetails,statistics&id=" + tci + end) as treq:
                tjson = await treq.json()
        # Use aiohttp to make GET requests for PewDiePie
        async with aiohttp.ClientSession() as anccs:
            # PewDiePie
            async with anccs.get(base + "/channels?part=snippet,contentDetails,statistics&id=" + pci + end) as preq:
                pjson = await preq.json()
        # Get T-Series sub count
        tsc = tjson["items"][0]["statistics"]["subscriberCount"]
        # Get PewDiePie sub count
        psc = pjson["items"][0]["statistics"]["subscriberCount"]
        # Create sub count variables with an int value
        tscint = int(tsc)
        pscint = int(psc)
        # Turn the sub counts into a more human readable format
        trf = format(tscint, ",d")
        prf = format(pscint, ",d")
        # Compare both subcounts
        if pscint >= tscint:
            pscp = pscint - tscint
            pscpts = f"PewDiePie is leading with {pscp:,d} more subscribers than T-Series"
        else:
            pscp = tscint - pscint
            pscpts = f"T-Series is leading with {pscp:,d} more subscribers than PewDiePie"
        # Check if they only want the sub gap
        if p.lower() == "retint":
            retdict = {
                "t": tscint,
                "p": pscint,
                "l": pscpts
            }
            return retdict
        else:
            # Send sub count in embed
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
        counter = 0
        r = 1000000
        while counter < r:
            run = True
            amount = 10
            # Get subgap information
            while run:
                try:
                    for guild_id in self.bot.subgap["guild"]:
                        message = self.bot.subgap["guild"][guild_id]["msgid"]
                        guild = guild_id
                        channel = self.bot.subgap["guild"][guild_id]["channelid"]
                        await self.subgloop(message, guild, channel)
                    run = False
                    amount = 0
                except RuntimeError:
                    if amount == 0:
                        await self.bot.get_channel(519378596104765442).send("""
                        <@498678645716418578> Subgap update task has been killed (RUNTIME ERROR)
                        """)
                        return
                    else:
                        amount -= 1
                        continue
            # Add one to counter
            counter += 1
            # Wait
            await asyncio.sleep(30)
        # Delete from database after everything is done
        await self.bot.pool.execute("DELETE FROM subgap WHERE msgid = $1 AND guildid = $2 AND channelid = $3", message, guild, channel)
        return

    # Subcount gap command
    @commands.command(name = "subgap")
    @commands.has_permissions(administrator = True)
    async def subgstart(self, ctx, r: int = 10000000):
        # ====START CHECKS====

        # Before doing anything, check if the guild is authorized
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
        # Check if guild is already using subgap
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

        # Sub info 1
        stsubinfo = await ctx.invoke(self.bot.get_command("subcount"), p = "retint", stping = False)
        # Create embed then send
        em = discord.Embed(color = discord.Color.blurple())
        em.add_field(name = "Leading Channel", value = stsubinfo["l"])
        stmsg = await ctx.send(embed = em)

        # ====END ORIGINAL MESSAGE====

        # Add the subgap to the database
        await self.bot.pool.execute("INSERT INTO subgap VALUES ($1, $2, $3, $4)", stmsg.id, ctx.channel.id, ctx.guild.id, r)
        # Wait 30 seconds to update
        await asyncio.sleep(30)
        # Update cache
        await self.subgupcache(stmsg.id, ctx.guild.id, ctx.channel.id, r)

    # SUBGAP LOOP -- THIS IS NOT A COMMAND BECAUSE OF NO CONTEXT IN ON_READY
    async def subgloop(self, message: int, guild: int, channel: int):
        try:
            # Get guild
            guildobj = self.bot.get_guild(guild)
            # Get channel
            channel = guildobj.get_channel(channel)
            # Check if the message exists or not
            await channel.get_message(message)
        except (AttributeError, discord.DiscordException):
            # Remove from cache
            self.bot.subgap["guild"].pop(guild)
            # Delete message from database
            await self.bot.pool.execute("DELETE FROM subgap WHERE msgid = $1 AND guildid = $2", message, guild)
            # Return
            return False
        # Get subscriber count information
        subinfo = await self.subcount.callback(None, None, "retint", False) # pylint: disable=no-member
        # Edit embed
        await self.subgedit(channel.id, message, subinfo["l"])
        # Take away one from count
        await self.bot.pool.execute("UPDATE subgap SET count = count - 1 WHERE msgid = $1 AND guildid = $2 AND channelid = $3", message, guild, channel.id)

    # SUBGAP EDIT -- THIS IS NOT A COMMAND DUE TO THERE BEING NO CONTEXT PASSED FROM SUBGLOOP
    async def subgedit(self, c: int, m: int, lndmsg: str):
        # Embed
        em = discord.Embed(color = discord.Color.blurple())
        em.add_field(name = "Leading Channel", value = lndmsg)
        # Get channel
        channel = self.bot.get_channel(c)
        # Get message
        message = await channel.get_message(m)
        # Edit message
        await message.edit(embed = em)

    # Start background tasks on ready
    async def on_ready(self):
        # Print to the console for the sole purpose of telling me that it works
        for x in self.bot.subgap["guild"]:
            g = self.bot.subgap
            print(f"Started subgap! Msg ID: {g['guild'][x]['msgid']}  Guild ID: {x}  Channel ID: {g['guild'][x]['channelid']}")


def setup(bot):
    bot.loop.create_task(Subscribe(bot).subgcache())
    bot.add_cog(Subscribe(bot))