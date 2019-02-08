import discord
from discord.ext import commands
import dbl
import datetime
import asyncio
import sys
sys.path.append("../")
import config


class Events:
    def __init__(self, bot):
        self.bot = bot
        self.token = config.dbltoken
        self.dblpy = dbl.Client(self.bot, self.token, loop = self.bot.loop)

    # Log command completion
    async def on_command_completion(self, ctx):
        print()
        print(f"COMPLETED COMMAND: {ctx.command.name}. Invoked by: {ctx.author.name}#{ctx.author.discriminator}")
        print(f"GUILD: {ctx.guild.name} | GUILD ID: {ctx.guild.id} | USER ID: {ctx.author.id}")

    # On guild join
    async def on_guild_join(self, guild):
        print(f"Joined guild named '{guild.name}' with {guild.member_count} members")
        # Log guild join into T-Series log channel
        logchannel = self.bot.get_channel(501089724421767178)
        em = discord.Embed(title = "Joined Guild", color = discord.Color.teal())
        em.set_thumbnail(url = guild.icon_url)
        em.add_field(name = "Name", value = guild.name)
        em.add_field(name = "ID", value = str(guild.id))
        em.add_field(name = "Owner", value = str(guild.owner))
        em.add_field(name = "Member Count", value = str(guild.member_count))
        em.add_field(name = "Verification Level", value = str(guild.verification_level))
        em.add_field(name = "Channel Count", value = str(len(guild.channels)))
        em.add_field(name = "Creation Time", value = guild.created_at)
        # Add timestamp
        em.timestamp = datetime.datetime.utcnow()
        # Send to channel
        await logchannel.send(embed = em)

    # On guild remove (leave)
    async def on_guild_remove(self, guild):
        print(f"Left guild named '{guild.name}' that had {guild.member_count} members")
        # Log guild remove into T-Series log channel
        logchannel = self.bot.get_channel(501089724421767178)
        em = discord.Embed(title = "Left Guild", color = discord.Color.purple())
        em.set_thumbnail(url = guild.icon_url)
        em.add_field(name = "Name", value = guild.name)
        em.add_field(name = "ID", value = str(guild.id))
        em.add_field(name = "Owner", value = str(guild.owner))
        em.add_field(name = "Member Count", value = str(guild.member_count))
        em.add_field(name = "Verification Level", value = str(guild.verification_level))
        em.add_field(name = "Channel Count", value = str(len(guild.channels)))
        em.add_field(name = "Creation Time", value = guild.created_at)
        # Add timestamp
        em.timestamp = datetime.datetime.utcnow()
        # Send to channel
        await logchannel.send(embed = em)

    # Push guild count to Discord Bot List
    async def update_dblservercount(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.dblpy.post_server_count()
                print("Posted server count on DBL")
            except Exception as e:
                print("Failed to post the server count on DBL")
                print("Error: " + str(e))
            await asyncio.sleep(1800)

    async def autostatus(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = f"for p.help in {len(self.bot.guilds):,d} servers"))
            await asyncio.sleep(30)
            await self.bot.change_presence(activity = discord.Game(name = "Subscribe to PewDiePie!"))
            await asyncio.sleep(30)

    async def on_ready(self):
        try:
            self.bot.loop.create_task(self.update_dblservercount())
        except:
            print("There was an issue updating the DBL server count")
        try:
            self.bot.loop.create_task(self.autostatus())
        except:
            print("There was an issue updating the bot status")

    async def close(self):
        # Close dblpy client session
        await self.dblpy.close()


def setup(bot):
    bot.add_cog(Events(bot))