import discord
from discord.ext import commands
import aiohttp
import asyncio
import textwrap
from datetime import datetime as dt
import sys
sys.path.append("../")
import config


class Subscribe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def subgcache(self):
        self.bot.subgap = {"guild": {}}
        self.bot.subgap["rmusr"] = {"time": [], "delete": False, "t_time": 0}
        information = await self.bot.pool.fetch("SELECT * FROM subgap")

        for info in information:
            self.bot.subgap["guild"][info["guildid"]] = {}
            guild = self.bot.subgap["guild"][info["guildid"]]
            guild["channelid"] = info["channelid"]
            guild["guildid"] = info["guildid"]
            guild["msgid"] = info["msgid"]

        if "subgap" in self.bot.tasks:
            self.bot.tasks["subgap"].cancel()
        if "subgap_ovpt" in self.bot.tasks:
            self.bot.tasks["subgap_ovpt"].cancel()

        self.bot.tasks["subgap"] = self.bot.loop.create_task(self.subgtask())
        self.bot.tasks["subgap_ovpt"] = self.bot.loop.create_task(self.subgovpt())

    async def subgupcache(self, channel: int, guild: int, message: int):
        gdict = self.bot.subgap["guild"][guild] = {}
        gdict["channelid"] = channel
        gdict["guildid"] = guild
        gdict["msgid"] = message

    async def subgremove(self, guild: int):
        rmusr = self.bot.subgap["rmusr"]

        if rmusr["delete"]:
            rmusr["t_time"] += 1
            return True
        if len(rmusr["time"]) > 1:
            if rmusr["time"][-2:][1] - rmusr["time"][-2:][0] <= 3:
                rmusr["delete"] = True
                rmusr["time"].clear()
                return True
        if "keep_alive" in self.bot.subgap["guild"][guild]:
            return False

        await self.bot.pool.execute("INSERT INTO subgapbackup SELECT * FROM subgap WHERE guildid = $1", guild)
        await self.bot.pool.execute("DELETE FROM subgap WHERE guildid = $1", guild)
        self.bot.subgap["guild"].pop(guild)
        rmusr["time"].append(round(dt.timestamp(dt.utcnow())))

        return True

    async def subgovpt(self):
        while not self.bot.is_closed():
            if self.bot.subgap["rmusr"]["delete"]:
                if self.bot.subgap["rmusr"]["t_time"] >= 5:
                    self.bot.tasks["subgap"].cancel()
                else:
                    await asyncio.sleep(5)
                    if self.bot.subgap["rmusr"]["t_time"] <= 5:
                        self.bot.subgap["rmusr"]["delete"] = False
                    else:
                        self.bot.tasks["subgap"].cancel()

            await asyncio.sleep(15)

    async def subgcheck(self, channel: int, guild: int, message: int, submsg: str):
        g = self.bot.get_guild(guild)
        if g == None:
            if await self.subgremove(guild): return
        channel = g.get_channel(channel)
        if channel == None:
            if await self.subgremove(g.id): return
        try:
            await channel.get_message(message)
        except (discord.NotFound, discord.Forbidden):
            if await self.subgremove(g.id): return

        await self.subgedit(channel.id, g.id, message, submsg)

    async def subgedit(self, channel: int, guild: int, message: int, msg: str):
        em = discord.Embed(color = discord.Color.blurple())
        em.add_field(name = "Leading Channel", value = msg)

        guild = self.bot.get_guild(guild)
        channel = guild.get_channel(channel)
        message = await channel.get_message(message)
        await message.edit(embed = em)

    async def subgtask(self):
        await self.bot.wait_until_ready()
        cont = True
        while cont:
            while True:
                try:
                    try:
                        info = await self.subcount.callback(None, None, False) # pylint: disable=no-member
                    except KeyError:
                        cont = False
                        return
                    for sub in self.bot.subgap["guild"]:
                        guild = self.bot.subgap["guild"][sub]
                        await self.subgcheck(guild["channelid"], sub, guild["msgid"], info)
                    break
                except RuntimeError:
                    await asyncio.sleep(1)
                    continue

            await asyncio.sleep(30)

    @commands.group(invoke_without_command = True)
    @commands.has_permissions(manage_guild = True)
    async def subgap(self, ctx):
        ch = await self.bot.pool.fetchrow("SELECT * FROM authorized WHERE guildid = $1", ctx.guild.id)
        if ch == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            g = "https://github.com/joshuapatel/PewDiePie/#how-do-i-get-authorized-for-the-subgap-command"
            em.add_field(name = "Not Authorized",
            value = f"Your server is not authorized to use this command. Please read the [guidelines]({g}) for getting authorized.")
            await ctx.send(embed = em)
            return

        chtwo = await self.bot.pool.fetchrow("SELECT * FROM subgap WHERE guildid = $1", ctx.guild.id)
        if chtwo != None:
            prefix = ctx.prefix.replace(self.bot.user.mention, f"@{self.bot.user.name}")
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Subscriber Gap in Use",
            value = f"The subgap command is being used in your server already. Please delete the subgap message or run `{prefix}subgap stop`.")
            await ctx.send(embed = em)
            return

        info = await self.subcount.callback(None, None, False) # pylint: disable=no-member
        em = discord.Embed(color = discord.Color.blurple())
        em.add_field(name = "Leading Channel", value = info)
        stmsg = await ctx.send(embed = em)

        await self.bot.pool.execute("INSERT INTO subgap VALUES ($1, $2, $3)", stmsg.id, ctx.channel.id, ctx.guild.id)
        await self.subgupcache(ctx.channel.id, ctx.guild.id, stmsg.id)

    @subgap.command(aliases = ["remove", "delete"])
    @commands.has_permissions(manage_guild = True)
    async def stop(self, ctx):
        c = await self.bot.pool.fetchrow("SELECT * FROM subgap WHERE guildid = $1", ctx.guild.id)

        if c == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Subscriber Gap Not Running", value = "The subgap command is not currently being used in your server.")
            await ctx.send(embed = em)
            return

        if not await self.subgremove(ctx.guild.id): return

        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Subscriber Gap Stopped", value = "The subgap message has stopped updating in your server.")
        await ctx.send(embed = em)

    @commands.command(aliases = ["subscribercount", "sc"])
    async def subcount(self, ctx, _type: bool = True):
        if _type: await ctx.channel.trigger_typing()
        
        base_uri = "https://www.googleapis.com/youtube/v3/channels"
        pew_chid = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        ts_chid = "UCq-Fj5jknLsUf-MWSy4_brA"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_uri}?part=snippet,contentDetails,statistics&id={pew_chid}&key={config.ytdapi}") as p:
                pew_json = await p.json()
            async with session.get(f"{base_uri}?part=snippet,contentDetails,statistics&id={ts_chid}&key={config.ytdapi}") as t:
                ts_json = await t.json()

        pew_count = int(pew_json["items"][0]["statistics"]["subscriberCount"])
        ts_count = int(ts_json["items"][0]["statistics"]["subscriberCount"])

        if pew_count >= ts_count:
            sg = f"PewDiePie is leading with {pew_count - ts_count:,d} more subscribers than T-Series"
        else:
            sg = f"T-Series is leading with {ts_count - pew_count:,d} more subscribers than PewDiePie"

        if not _type: return sg

        em = discord.Embed(color = discord.Color.red())
        em.add_field(name = "PewDiePie", value = f"{pew_count:,d}")
        em.add_field(name = "T-Series", value = f"{ts_count:,d}")
        em.add_field(name = "Leading Channel", value = sg, inline = False)
        em.add_field(name = "Live Count Websites", value = textwrap.dedent("""
        [PewDiePie](https://socialblade.com/youtube/user/pewdiepie/realtime) | [T-Series](https://socialblade.com/youtube/user/tseries/realtime)
        """), inline = False)
        await ctx.send(embed = em)


def setup(bot):
    bot.loop.create_task(Subscribe(bot).subgcache())
    bot.add_cog(Subscribe(bot))