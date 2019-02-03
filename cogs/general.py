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
        # Remove default help command
        self.bot.remove_command("help")

    # PewDiePie Command (Hates on Pewds)
    @commands.command()
    async def pewdiepie(self, ctx):
        await ctx.send("PewDiePie अद्भुत है! आपको उसकी सदस्यता लेनी चाहिए।")
        await ctx.send("https://translate.google.com")

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
                print(f"Started playing BL in VC. Guild: {ctx.guild.name}")
            else:
                await ctx.send("You must be connected to a voice channel")
        elif param == "stop" or param == "leave":
            if ctx.voice_client != None:
                await ctx.voice_client.disconnect()
                await ctx.send("Disconnected from voice channel")
                print(f"Disconnected from VC in {ctx.guild.name}")
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
        print("Got a random video. Video ID: " + rndptvids)

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
        print("Sent bot info. Ping time: " + str(botlat))

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

    # Returns bot prefix in the current guild
    @commands.command(aliases = ["currentprefix", "botprefix", "serverprefix", "guildprefix"])
    async def prefix(self, ctx):
        # Get prefix
        prefixes = await self.bot.pool.fetchval("SELECT prefix FROM prefixes WHERE guildid = $1", ctx.guild.id)
        if prefixes == None:
            prefix = "ts!, ts., t., and t!"
        else:
            prefix = prefixes
        # Send
        em = discord.Embed(color = discord.Color.red())
        em.add_field(name = "Current Prefix", value = f"The current prefix for {self.bot.user.mention} is `{prefix}`")
        await ctx.send(embed = em)

    # Invite command
    @commands.command()
    async def invite(self, ctx):
        # Embed
        em = discord.Embed(color = discord.Color.orange())
        em.add_field(name = "Invite", value = "[Invite me here!](https://discordapp.com/oauth2/authorize?client_id=500868806776979462&scope=bot&permissions=72710)")
        await ctx.send(embed = em)
        print("Sent bot invite!")

    # Set prefix tutorial command
    @commands.command(aliases = ["prefixtutorial", "tutprefix"])
    async def prefixtut(self, ctx):
        em = discord.Embed(color = discord.Color.dark_green())
        em.add_field(name = "Command Use", value = f"""
        Sets the prefix for the current server. You must have the manage messages permission to use this command.
        **Set or change prefix**
        `ts!setprefix [prefix here]`
        **Revert back to default prefix**
        `ts!setprefix`
        **Show current prefix**
        `ts!prefix` (does not require any special permissions to view)
        """)
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

    # Help command
    @commands.group(invoke_without_command = True)
    async def help(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        em.set_author(name = f"{self.bot.user.name} Help Page")
        # Main commands
        em.add_field(name = "Main Commands", value = """
        `pewdiepie`: Tells you what I think of PewDiePie in Hindi
        `disstrack`: Plays Bitch Lasagna in a voice channel. To disconnect, run `ts!disstrack stop` or `ts!disstrack leave`
        `subcount`: Shows T-Series' and PewDiePie's subscriber count
        `subgap`: Automatically updates the current subscriber gap between PewDiePie and T-Series every 30 seconds. Your server must be authorized to use this feature.
        Please join the [support server](https://discord.gg/we4DQ5u) to request authorization.
        `randomvid`: Returns a random PewDiePie or T-Series video
        `youtube (yt)`: Sends you the link to PewDiePie's and T-Series' YouTube channel
        `spoiler`: Sends any message you provide as a spoiler in an annoying form
        """, inline = False)
        # Bro Coin (economy) commands
        em.add_field(name = "Bro Coin (economy)", value = """
        Run `p.help economy` to view the list of commands for Bro Coin
        """)
        # Meta commands
        em.add_field(name = "Meta Commands", value = f"""
        `botinfo`: Information on {self.bot.user.name}
        `invite`: Sends the bot invite
        `feedback`: This command will send the developer feedback on this bot. Feel free to send suggestions or issues
        `prefixtut`: This will give you a tutorial on how to use custom prefixes on {self.bot.user.name}
        `prefix`: Returns the current prefix that {self.bot.user.name} uses in your server
        """, inline = False)
        # Timestamp
        em.timestamp = datetime.datetime.utcnow()
        em.set_footer(icon_url = ctx.author.avatar_url, text = f"{ctx.author.name}#{ctx.author.discriminator}")
        await ctx.send(embed = em)

    # Help: economy
    @help.command()
    async def economy(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        em.set_author(name = f"{self.bot.user.name} Economy Help Page")
        em.add_field(name = "Bro Coin Commands", value = """
        `shovel`: You work all day shoveling for Bro Coins
        `balance (bal)`: Informs you on how many Bro Coins you have
        `pay`: Pays a user with a specified amount of Bro Coins
        `leaderboard (lb)`: Shows the leaderboard for Bro Coins
        `gamble`: You can gamble a specific amount of Bro Coins
        `steal (rob)`: Steals from a user that you specify
        `transfer`: Sends Bro Coins to another server. The max amount is 50% of your coins.
        `statistics (stats)`: Statistics on Bro Coin usage
        """, inline = False)
        em.add_field(name = "Shop", value = """
        `shop`: View all the items (roles) in the shop
        `shop add`: Adds a role to the shop (you must have the manage roles permission)
        `shop edit`: Edits a role (eg. changes the cost) in the shop (manage roles permission required by user)
        `shop delete (remove)`: Removes a role from the shop (manage roles permission required by user)
        `shop buy`: Buys an item from the shop (you must have enough coins)
        **Please note: The bot must have the manage roles permission and be higher than the role in the shop to use the shop feature**
        """, inline = False)
        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(General(bot))