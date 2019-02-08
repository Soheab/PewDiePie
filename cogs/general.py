import discord
from discord.ext import commands
import asyncio
import random
import aiohttp
import datetime
import sys
sys.path.append("../")
import config


class General:
    def __init__(self, bot):
        self.bot = bot

    # T-SERIES DISS TRACK
    @commands.command()
    async def disstrack(self, ctx, param: str = "play"):
        if param == "play":
            if ctx.author.voice != None:
                # Connect
                try:
                    await ctx.author.voice.channel.connect()
                except discord.ClientException:
                    pass
                # Get file
                source = discord.FFmpegPCMAudio("lasagna.mp3")
                # Play audio
                try:
                    ctx.voice_client.play(source)
                except discord.ClientException:
                    await ctx.send("Already playing audio")
                    return
                # Tell user
                await ctx.send(f"Connected to `{ctx.voice_client.channel.name}`")
            else:
                await ctx.send("You must be connected to a voice channel")
        elif param == "stop" or param == "leave":
            if ctx.voice_client != None:
                await ctx.voice_client.disconnect()
                await ctx.send("Disconnected from voice channel")
            else:
                await ctx.send(f"{self.bot.user.name} is not currently in a voice channel")
        else:
            await ctx.send("That is not a valid parameter")

    # Gets a random T-Series or PewDiePie video
    @commands.command()
    async def randomvid(self, ctx):
        await ctx.channel.trigger_typing()
        base = "https://www.googleapis.com/youtube/v3"
        apikey = config.ytdapi
        end = "&key=" + apikey
        pci = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        tci = "UCq-Fj5jknLsUf-MWSy4_brA"
        # ====T-SERIES SECTION====

        # Use aiohttp to make GET requests all in one session
        async with aiohttp.ClientSession() as cs:
            async with cs.get(base + "/channels?part=snippet,contentDetails&id=" + tci + end) as tureq:
                # Get T-Series upload playlist
                tujson = await tureq.json()
            tupl = tujson["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            async with cs.get(base + "/playlistItems?playlistId=" + tupl + "&maxResults=15&part=snippet,contentDetails" + end) as tuvids:
                # Get the first 15 videos
                tuvidsjson = await tuvids.json()
        tuvidslist = []
        vid = 0
        # Iterate through the list and append them to tuvidslist
        while vid < len(tuvidsjson["items"]):
            tvidid = tuvidsjson["items"][vid]["snippet"]["resourceId"]["videoId"]
            tuvidslist.append(tvidid)
            vid += 1
        # ====PEWDIEPIE SECTION====

        # Use aiohttp to make GET requests all in one session
        async with aiohttp.ClientSession() as pcs:
            async with pcs.get(base + "/channels?part=snippet,contentDetails&id=" + pci + end) as pureq:
                # Get T-Series upload playlist
                pujson = await pureq.json()
            pupl = pujson["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            async with pcs.get(base + "/playlistItems?playlistId=" + pupl + "&maxResults=15&part=snippet,contentDetails" + end) as puvids:
                # Get the first 15 videos
                puvidsjson = await puvids.json()
        puvidslist = []
        vid = 0
        # Iterate through the list and append them to puvidslist
        while vid < len(puvidsjson["items"]):
            pvidid = puvidsjson["items"][vid]["snippet"]["resourceId"]["videoId"]
            puvidslist.append(pvidid)
            vid += 1
        # ====COMPARE AND SEND====

        # Compine both lists together
        ptuvidslist = tuvidslist + puvidslist
        # Get random video
        rndptvids = random.choice(ptuvidslist)
        # Make the video ID a URL
        rndptvidsed = "https://www.youtube.com/watch?v=" + rndptvids
        # Get video thumbnail
        rndptvidthumb = "https://img.youtube.com/vi/" + rndptvids + "/maxresdefault.jpg"
        # Send as embed
        em = discord.Embed(color = discord.Color.green())
        em.add_field(name = "YouTube Video", value = rndptvidsed)
        em.set_image(url = rndptvidthumb)
        await ctx.send(embed = em)

    # YouTube channels command
    @commands.command(aliases = ["yt"])
    async def youtube(self, ctx):
        # Sends T-Series and PewDiePie's channel
        em = discord.Embed(color = discord.Color.light_grey())
        em.add_field(name = "PewDiePie", value = "https://www.youtube.com/user/PewDiePie")
        em.add_field(name = "T-Series", value = "https://www.youtube.com/user/tseries")
        await ctx.send(embed = em)

    # Bot information command
    @commands.command(aliases = ["info", "bot", "information", "botinformation", "support"])
    async def botinfo(self, ctx):
        # Get bot latency
        botlat = f"{self.bot.latency * 1000:.3f}"
        # Bot info embed
        em = discord.Embed(title = f"{self.bot.user.name} Bot Information", color = discord.Color.green())
        em.add_field(name = "Bot Creator", value = "A Discord User#4063")
        em.add_field(name = "Bot Library", value = "discord.py rewrite")
        em.add_field(name = "Support Server", value = "https://discord.gg/we4DQ5u")
        em.add_field(name = "Bot Latency", value = str(botlat) + " ms")
        await ctx.send(embed = em)

    # Invite command
    @commands.command()
    async def invite(self, ctx):
        # Embed
        em = discord.Embed(color = discord.Color.orange())
        em.add_field(name = "Invite", value = "[Invite me here!](https://discordapp.com/oauth2/authorize?client_id=500868806776979462&scope=bot&permissions=72710)")
        await ctx.send(embed = em)

    # Feedback command
    @commands.command()
    async def feedback(self, ctx, *, message: str):
        # Feedback embed
        em = discord.Embed(color = discord.Color.blue())
        em.add_field(name = "Feedback", value = f"""
        Your feedback for {self.bot.user.name} has been submitted
        If you abuse this command, you could lose your ability to send feedback.
        """)
        await ctx.send(embed = em)
        # Send in PewDiePie Support
        feedbackchannel = self.bot.get_channel(518603886483996683)
        emb = discord.Embed(title = "Feedback", color = discord.Color.blue())
        emb.set_thumbnail(url = ctx.author.avatar_url)
        emb.add_field(name = "User", value = str(ctx.author))
        emb.add_field(name = "User ID", value = str(ctx.author.id))
        emb.add_field(name = "Issue / Suggestion", value = message, inline = False)
        emb.add_field(name = "Guild Name", value = ctx.guild.name)
        emb.add_field(name = "Guild ID", value = str(ctx.guild.id))
        # Timestamp
        emb.timestamp = datetime.datetime.utcnow()
        # Send
        await feedbackchannel.send(embed = emb)

    # Spoiler command
    @commands.command()
    async def spoiler(self, ctx, *, spoiler: str):
        x = ""
        for b in spoiler:
            x += f"||{b}||"
        await ctx.send(x)


def setup(bot):
    bot.add_cog(General(bot))