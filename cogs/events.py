import discord
from discord.ext import commands
import datetime
import asyncio
import aiohttp
import sys
sys.path.append("../")
import config


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Log command completion
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        print()
        print(f"COMPLETED COMMAND: {ctx.command.name}. Invoked by: {ctx.author.name}#{ctx.author.discriminator}")
        print(f"GUILD: {ctx.guild.name} | GUILD ID: {ctx.guild.id}\nUSER ID: {ctx.author.id} | CHANNEL ID: {ctx.channel.id}")

    # On guild join
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"Joined guild named '{guild.name}' with {guild.member_count} members")

        logchannel = self.bot.get_channel(501089724421767178)
        em = discord.Embed(title = "Joined Guild", color = discord.Color.teal())
        bot_count = len([b for b in guild.members if b.bot])
        em.set_thumbnail(url = guild.icon_url)
        em.add_field(name = "Name", value = guild.name)
        em.add_field(name = "ID", value = str(guild.id))
        em.add_field(name = "Owner", value = str(guild.owner))
        em.add_field(name = "Member Count", value = f"{guild.member_count:,d}")
        em.add_field(name = "Bot Count", value = format(bot_count, ",d"))
        em.add_field(name = "Human Count", value = format(guild.member_count - bot_count, ",d"))
        em.add_field(name = "Verification Level", value = str(guild.verification_level))
        em.add_field(name = "Channel Count", value = f"{len(guild.channels):,d}")
        em.add_field(name = "Creation Time", value = guild.created_at)

        em.timestamp = datetime.datetime.utcnow()
        await logchannel.send(embed = em)

    # On guild remove (leave)
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f"Left guild named '{guild.name}' that had {guild.member_count} members")

        logchannel = self.bot.get_channel(501089724421767178)
        em = discord.Embed(title = "Left Guild", color = discord.Color.purple())
        bot_count = len([b for b in guild.members if b.bot])
        em.set_thumbnail(url = guild.icon_url)
        em.add_field(name = "Name", value = guild.name)
        em.add_field(name = "ID", value = str(guild.id))
        em.add_field(name = "Owner", value = str(guild.owner))
        em.add_field(name = "Member Count", value = f"{guild.member_count:,d}")
        em.add_field(name = "Bot Count", value = format(bot_count, ",d"))
        em.add_field(name = "Human Count", value = format(guild.member_count - bot_count, ",d"))
        em.add_field(name = "Verification Level", value = str(guild.verification_level))
        em.add_field(name = "Channel Count", value = f"{len(guild.channels):,d}")
        em.add_field(name = "Creation Time", value = guild.created_at)

        em.timestamp = datetime.datetime.utcnow()
        await logchannel.send(embed = em)

    async def update_dblservercount(self):
        await self.bot.wait_until_ready()
        base = "https://discordbots.org/api"
        while not self.bot.is_closed():
            if config.dbltoken == None:
                break

            async with aiohttp.ClientSession() as cs:
                post = await cs.post(f"{base}/bots/{self.bot.user.id}/stats",
                headers = {"Authorization": config.dbltoken}, data = {"server_count": len(self.bot.guilds)})
                post = await post.json()

                if "error" in post:
                    print(f"Couldn't post server count, {post['error']}")
                else:
                    print("Posted server count on DBL")

            await asyncio.sleep(3600)

    async def autostatus(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            watching = ["Pew News", f"for p.help in {len(self.bot.guilds):,d} servers"]

            for w in watching:
                await self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = w))
                await asyncio.sleep(30)

            await self.bot.change_presence(activity = discord.Game(name = "Banning T-Series subscribers"))
            await asyncio.sleep(30)

    async def bkg_start(self):
        if "status" in self.bot.tasks:
            self.bot.tasks["status"].cancel()
        if "dbl_gc" in self.bot.tasks:
            self.bot.tasks["dbl_gc"].cancel()

        self.bot.tasks["dbl_gc"] = self.bot.loop.create_task(self.update_dblservercount())
        self.bot.tasks["status"] = self.bot.loop.create_task(self.autostatus())


def setup(bot):
    bot.loop.create_task(Events(bot).bkg_start())
    bot.add_cog(Events(bot))