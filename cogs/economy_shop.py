import discord
from discord.ext import commands
import datetime


class EconomyShop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tcoinimage = "<:bro_coin:541363630189576193>"

    async def cad_user(ctx): # pylint: disable=E0213
        dbcheck = await ctx.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id) # pylint: disable=E1101
        if dbcheck == None or dbcheck == []:
            await ctx.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", 0, ctx.author.id, ctx.guild.id) # pylint: disable=E1101
            return True
        else:
            return True
        return False

    class AmountConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                return int(argument)
            except:
                pass
            if "all" in argument:
                coins = await ctx.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
                return coins
            elif "," in argument:
                return int(argument.replace(",", ""))
            else:
                return 0

    @commands.group(invoke_without_command = True)
    async def shop(self, ctx):
        roles = await self.bot.pool.fetch("""
        SELECT * FROM econshop WHERE guildid = $1 ORDER BY reqamount DESC
        """, ctx.guild.id)

        em = discord.Embed(color = discord.Color.dark_red())
        em.set_thumbnail(url = ctx.guild.icon_url)
        em.set_author(name = f"{ctx.guild.name}'s Shop")

        for r in roles:
            role = ctx.guild.get_role(r["roleid"])
            if role == None:
                await self.bot.pool.execute("DELETE FROM econshop WHERE roleid = $1", r["roleid"])
                continue

            em.add_field(name = f"Role: {role.name}", value = f"Required amount: {r['reqamount']:,d} {self.tcoinimage}", inline = False)

        if len(em.fields) == 0:
            em.set_author(name = "")
            em.add_field(name = "No Roles", value = f"No roles have been found for {ctx.guild.name}")

        await ctx.send(embed = em)

    @shop.command(aliases = ["role", "make"])
    @commands.bot_has_permissions(manage_roles = True)
    @commands.has_permissions(manage_roles = True)
    async def add(self, ctx, req_amount: AmountConverter, *, role: discord.Role):
        rolecheck = await self.bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        if rolecheck != None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Found", value = "This role is already in the shop. Use the `shop edit` command to edit it")
            await ctx.send(embed = em)
            return

        if 0 >= req_amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot set the amount at 0 or below")
            await ctx.send(embed = em)
            return

        await self.bot.pool.execute("INSERT INTO econshop VALUES ($1, $2, $3)", role.id, ctx.guild.id, req_amount)

        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Role Added", value = f"`{role.name}` has been added to the shop and requires {req_amount:,d} {self.tcoinimage} to purchase")
        await ctx.send(embed = em)

    @shop.command(aliases = ["purchase", "spend", "get"])
    @commands.bot_has_permissions(manage_roles = True)
    @commands.check(cad_user)
    async def buy(self, ctx, *, role: discord.Role):
        if role in ctx.author.roles:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role in Possession", value = f"You already have the `{role.name}` role therefore you cannot buy it")
            await ctx.send(embed = em)
            return

        req_amount = await self.bot.pool.fetchval("SELECT reqamount FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)

        if req_amount == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Not Found", value = "This role has not been added to this shop. Use the `shop add` command to add it")
            await ctx.send(embed = em)
            return

        user_amount = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)

        if user_amount >= req_amount:
            try:
                await ctx.author.add_roles(role, reason = f"Purchased from the shop costing {req_amount:,d} Bro Coins")
            except:
                em = discord.Embed(color = discord.Color.dark_teal())
                em.add_field(name = "Forbidden", value = f"""
                It looks like I am not able to give the user this role. Please check that my role is **above** the role you are trying to give.
                """)
                await ctx.send(embed = em)
                return

            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", req_amount, ctx.author.id, ctx.guild.id)

            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = "Purchased Role", value = f"{ctx.author.mention} bought the `{role.name}` role costing {req_amount:,d} {self.tcoinimage}")
            em.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed = em)
        else:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"""
            You need {req_amount - user_amount:,d} more {self.tcoinimage} to buy the `{role.name}` role.
            """)
            await ctx.send(embed = em)

    @shop.command(aliases = ["change", "adjust"])
    @commands.has_permissions(manage_roles = True)
    async def edit(self, ctx, req_amount: AmountConverter, *, role: discord.Role):
        rolecheck = await self.bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        if rolecheck == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Not Found", value = "This role could not be found in the shop. You can create on using the `shop add` command")
            await ctx.send(embed = em)
            return

        if 0 >= req_amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot set the amount at 0 or below")
            await ctx.send(embed = em)
            return

        await self.bot.pool.execute("UPDATE econshop SET reqamount = $1 WHERE roleid = $2 AND guildid = $3", req_amount, role.id, ctx.guild.id)

        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Role Updated", value = f"`{role.name}`'s required amount to purchase has been changed to {req_amount:,d} {self.tcoinimage}")
        await ctx.send(embed = em)

    @shop.command(aliases = ["remove"])
    @commands.has_permissions(manage_roles = True)
    async def delete(self, ctx, *, role: discord.Role):
        rolecheck = await self.bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        if rolecheck == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Not Found", value = "This role could not be found in the shop. You can create on using the `shop add` command")
            await ctx.send(embed = em)
            return

        await self.bot.pool.execute("DELETE FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)

        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Role Deleted", value = f"`{role.name}` has been removed from the shop")
        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(EconomyShop(bot))