"""This cog was only made so that reloading cogs.general will NOT stop the disstrack from being played in VC"""
import discord
from discord.ext import commands


class Disstrack:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command = True)
    async def disstrack(self, ctx):
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

    @disstrack.command(aliases = ["leave", "end", "disconnect"])
    async def stop(self, ctx):
        if ctx.voice_client != None:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected from voice channel")
        else:
            await ctx.send(f"{self.bot.user.name} is not currently in a voice channel")


def setup(bot):
    bot.add_cog(Disstrack(bot))