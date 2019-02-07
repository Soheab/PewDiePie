import discord
from discord.ext import commands
from contextlib import redirect_stdout
import textwrap
import io
import traceback
import asyncio
import re


class Owner:
    def __init__(self, bot):
        self.bot = bot

    # Command authorization check
    async def cmdauthcheck(ctx): # pylint: disable=E0213
        # Get guild
        guild = ctx.bot.get_guild(499357399690379264)
        # Get role
        role = guild.get_role(531176653184040961)
        # Get member
        user = guild.get_member(ctx.author.id) # pylint: disable=E1101
        # Check if user has role
        try:
            if role in user.roles:
                return True
            else:
                return False
        except AttributeError:
            return False

    # Authorize command
    @commands.command()
    @commands.check(cmdauthcheck)
    async def authorize(self, ctx):
        # Check if guild is already in the database
        gchck = await self.bot.pool.fetchrow("SELECT * FROM authorized WHERE guildid = $1", ctx.guild.id)
        if gchck != None:
            emb = discord.Embed(color = discord.Color.dark_teal())
            emb.add_field(name = "Already Authorized", value = f"`{ctx.guild.name}` is already authorized")
            await ctx.send(embed = emb)
            return
        # Add guild to authorization database
        await self.bot.pool.execute("INSERT INTO authorized VALUES ($1)", ctx.guild.id)
        # Send message saying that it has been authorized
        em = discord.Embed(color = discord.Color.dark_purple())
        em.add_field(name = "Authorized", value = f"`{ctx.guild.name}` has been authorized")
        await ctx.send(embed = em)

    # Deauthorize command
    @commands.command()
    @commands.check(cmdauthcheck)
    async def deauthorize(self, ctx):
        # Check if guild is already in the database
        gchck = await self.bot.pool.fetchrow("SELECT * FROM authorized WHERE guildid = $1", ctx.guild.id)
        if gchck == None:
            emb = discord.Embed(color = discord.Color.dark_teal())
            emb.add_field(name = "Never Authorized", value = f"`{ctx.guild.name}` was never authorized")
            await ctx.send(embed = emb)
            return
        # Remove guild from authorization database
        await self.bot.pool.execute("DELETE FROM authorized WHERE guildid = $1", ctx.guild.id)
        # Send message saying that it has been authorized
        em = discord.Embed(color = discord.Color.dark_purple())
        em.add_field(name = "Deauthorized", value = f"`{ctx.guild.name}` has been deauthorized")
        await ctx.send(embed = em)

    # Update command
    @commands.command()
    @commands.is_owner()
    async def update(self, ctx):
        pro = await asyncio.create_subprocess_exec(
            "git", "pull",
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE
        )
        try:
            com = await asyncio.wait_for(pro.communicate(), timeout = 10)
            com = com[0].decode() + "\n" + com[1].decode()
        except asyncio.TimeoutError:
            await ctx.send("Took too long to respond")
            return
        reg = r"(.*?)\.py"
        found = re.findall(reg, com)
        if found:
            updated = []
            final_string = ""
            for x in found:
                extension = re.sub(r"\s+", "", x)
                extension = extension.replace("/", ".")
                try:
                    self.bot.unload_extension(extension)
                    self.bot.load_extension(extension)
                except ModuleNotFoundError:
                    continue
                updated.append(extension)
            for b in updated:
                final_string += f"`{b}` "
            await ctx.send(f"Updated cogs: {final_string}")
        else:
            await ctx.send("No cogs were updated")

    # Eval command
    @commands.command(name = "eval")
    @commands.is_owner()
    async def ev(self, ctx, *, code: str):
        """From R. Danny. I did not make this command"""
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message
        }
        env.update(globals())
        stdout = io.StringIO()
        to_compile = f"async def func():\n{textwrap.indent(code, '  ')}"
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")
        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                _last_result = ret
                await ctx.send(f"```py\n{value}{ret}\n```")


def setup(bot):
    bot.add_cog(Owner(bot))