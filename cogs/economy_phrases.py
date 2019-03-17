import discord
from discord.ext import commands


class EconomyPhrases(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_shovel(self):
        if "pos" in self.bot.econ and "neg" in self.bot.econ:
            self.bot.econ["pos"] = await self.bot.pool.fetch("SELECT * FROM shovel WHERE fate = true")
            self.bot.econ["neg"] = await self.bot.pool.fetch("SELECT * FROM shovel WHERE fate = false")
        else:
            print("Cog not loaded in")

    @commands.group(invoke_without_command = True)
    async def phrase(self, ctx, pid: int):
        pcheck = await self.bot.pool.fetchrow("SELECT * FROM shovel WHERE id = $1", pid)
        if pcheck == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Phrase Not Found", value = f"Phrase #{pid} could not be found")
            await ctx.send(embed = em)
            return

        fate = pcheck["fate"]
        p = pcheck["name"]

        if fate:
            em = discord.Embed(color = discord.Color.green())
        else:
            em = discord.Embed(color = discord.Color.red())

        em.add_field(name = "Shovel - Raw", value = p)
        em.set_footer(text = f"Phrase #{pid}")
        await ctx.send(embed = em)

    @phrase.command()
    @commands.is_owner()
    async def add(self, ctx, fate: bool, *, phrase: str):
        await self.bot.pool.execute("INSERT INTO shovel VALUES ($1, $2)", phrase, fate)
        pid = await self.bot.pool.fetchval("SELECT id FROM shovel WHERE name = $1 AND fate = $2", phrase, fate)

        if fate:
            em = discord.Embed(color = discord.Color.green())
        else:
            em = discord.Embed(color = discord.Color.red())

        em.add_field(name = "Added Phrase", value = f"The phrase has been added to the shovel command. Fate: {fate}")
        em.set_footer(text = f"Phrase #{pid}")
        await ctx.send(embed = em)

        await self.update_shovel()

    @phrase.command()
    @commands.is_owner()
    async def edit(self, ctx, pid: int, *, phrase: str):
        pcheck = await self.bot.pool.fetchrow("SELECT * FROM shovel WHERE id = $1", pid)
        if pcheck == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Phrase Not Found", value = f"Phrase #{pid} could not be found")
            await ctx.send(embed = em)
            return

        await self.bot.pool.execute("UPDATE shovel SET name = $1 WHERE id = $2", phrase, pid)

        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Phrase Updated", value = f"Phrase #{pid} has been updated")
        await ctx.send(embed = em)

        await self.update_shovel()

    @phrase.command(aliases = ["remove"])
    @commands.is_owner()
    async def delete(self, ctx, pid: int):
        pcheck = await self.bot.pool.fetchrow("SELECT * FROM shovel WHERE id = $1", pid)
        if pcheck == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Phrase Not Found", value = f"Phrase #{pid} could not be found")
            await ctx.send(embed = em)
            return

        await self.bot.pool.execute("DELETE FROM shovel WHERE id = $1", pid)

        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Phrase Removed", value = f"Phrase #{pid} has been removed")
        await ctx.send(embed = em)

        await self.update_shovel()


def setup(bot):
    bot.add_cog(EconomyPhrases(bot))