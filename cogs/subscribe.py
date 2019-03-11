"""
The code here for subgap has been removed while I rewrite the code for the command
"""
import discord
from discord.ext import commands
import aiohttp
import asyncio
import sys
sys.path.append("../")
import config


class Subscribe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        try:
            tsc = tjson["items"][0]["statistics"]["subscriberCount"]
        except KeyError:
            if ctx == None:
                raise KeyError(tjson["error"]["message"])
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = f"Error Code: {tjson['error']['code']}", value = f"```\n{tjson['error']['message']}\n```")
            await ctx.send(embed = em)
            return
        try:
            psc = pjson["items"][0]["statistics"]["subscriberCount"]
        except KeyError:
            if ctx == None:
                raise KeyError(pjson["error"]["message"])
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = f"Error Code: {pjson['error']['code']}", value = f"```\n{pjson['error']['message']}\n```")
            await ctx.send(embed = em)
            return

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


def setup(bot):
    bot.add_cog(Subscribe(bot))