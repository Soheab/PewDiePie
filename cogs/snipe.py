import discord
from discord.ext import commands
import datetime


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ta = "ORDER BY time DESC LIMIT 1"

	@commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.content == "":
            return

        try:
            await self.bot.pool.execute("""
            INSERT INTO snipe VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, message.content[:980], message.author.id, message.guild.id,
            message.channel.id, message.id, message.author.bot,
            datetime.datetime.utcnow())
        except Exception as error:
            print(f"\n{error}\n")

    async def data(self, ctx, dta):
        if dta == None:
            await ctx.send("Couldn't find anything to snipe")
            return

        em = discord.Embed(color = discord.Color.green())
        try:
            em.set_author(name = self.bot.get_user(dta["usr"]), icon_url = self.bot.get_user(dta["usr"]).avatar_url)
        except AttributeError:
            deleted_user = "https://discordapp.com/assets/0e291f67c9274a1abdddeb3fd919cbaa.png"
            em.set_author(name = "Missing User", icon_url = deleted_user)
        em.add_field(name = "Message", value = dta["contents"][:980])
        em.timestamp = dta["time"]
        await ctx.send(embed = em)

    @commands.group(invoke_without_command = True)
    async def snipe(self, ctx):
        data = await self.bot.pool.fetchrow(f"SELECT * FROM snipe WHERE guild = $1 AND channel = $2 {self.ta}", ctx.guild.id, ctx.channel.id)
        await self.data(ctx, data)

    @snipe.command(aliases = ["ch"])
    async def channel(self, ctx, chid: discord.TextChannel):
        data = await self.bot.pool.fetchrow(f"SELECT * FROM snipe WHERE guild = $1 AND channel = $2 {self.ta}", ctx.guild.id, chid.id)
        await self.data(ctx, data)

    @snipe.command(aliases = ["user", "u"])
    async def member(self, ctx, *, member: discord.Member):
        data = await self.bot.pool.fetchrow(f"SELECT * FROM snipe WHERE guild = $1 AND channel = $2 AND usr = $3 {self.ta}",
        ctx.guild.id, ctx.channel.id, member.id)
        await self.data(ctx, data)

    @snipe.command(aliases = ["c"])
    async def count(self, ctx, c: int):
        data = await self.bot.pool.fetchrow(f"SELECT * FROM snipe WHERE guild = $1 AND channel = $2 {self.ta} OFFSET $3",
        ctx.guild.id, ctx.channel.id, c)
        await self.data(ctx, data)

    @snipe.command(name = "bot", aliases = ["b", "bots"])
    async def _bot(self, ctx):
        data = await self.bot.pool.fetchrow(f"SELECT * FROM snipe WHERE guild = $1 AND channel = $2 AND bot = true {self.ta}",
        ctx.guild.id, ctx.channel.id)
        await self.data(ctx, data)

    @snipe.command(name = "list", aliases = ["l", "show", "recent"])
    async def _list(self, ctx):
        data = await self.bot.pool.fetch("SELECT * FROM snipe WHERE guild = $1 ORDER BY time DESC LIMIT 5", ctx.guild.id)

        em = discord.Embed(color = discord.Color.green())
        em.set_thumbnail(url = ctx.guild.icon_url)
        
        if data == []:
            em.add_field(name = f"{ctx.guild.name}'s Sniped Messages", value = "Couldn't find anything to snipe in this server")
        else:
            em.set_author(name = f"{ctx.guild.name}'s Sniped Messages")

        for row in data:
            try:
                user = self.bot.get_user(row["usr"]).name
            except AttributeError:
                user = "User Not Found"
            try:
                ch = self.bot.get_channel(row["channel"]).name
            except AttributeError:
                ch = "Channel Not Found"
            if len(user) > 17:
                user = user[:-5] + "..."
            if len(ch) > 19:
                ch = ch[:-8] + "..."

            em.add_field(name = f"**{user}**: #{ch}", value = row["contents"][:230], inline = False)

        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(Snipe(bot))