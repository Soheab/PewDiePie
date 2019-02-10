import discord
from discord.ext import commands


class Functions:
    def __init__(self, bot):
        self.bot = bot

    async def add(self):
        d = ["tasks", "econ"]
        for entry in d:
            if not hasattr(self.bot, entry):
                setattr(self.bot, entry, {})

    async def close(self):
        if hasattr(self.bot, "tasks"):
            for tsk in self.bot.tasks:
                tsk.close()


def setup(bot):
    bot.loop.create_task(Functions(bot).add())
    bot.add_cog(Functions(bot))