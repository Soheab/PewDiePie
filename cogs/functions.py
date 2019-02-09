import discord
from discord.ext import commands


class Functions:
    def __init__(self, bot):
        self.bot = bot

    async def tasks(self):
        if not hasattr(self.bot, "tasks"):
            self.bot.tasks = {}

    async def close(self):
        if hasattr(self.bot, "tasks"):
            for tsk in self.bot.tasks:
                tsk.close()


def setup(bot):
    bot.loop.create_task(Functions(bot).tasks())
    bot.add_cog(Functions(bot))