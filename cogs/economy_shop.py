import discord
from discord.ext import commands
import datetime


class EconomyShop:
    def __init__(self, bot):
        self.bot = bot
        self.tcoinimage = "<:bro_coin:541363630189576193>"

    # Add user to DB and check
    async def cad_user(ctx): # pylint: disable=E0213
        dbcheck = await ctx.bot.pool.fetchrow("SELECT * FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id) # pylint: disable=E1101
        if dbcheck == None or dbcheck == []:
            await ctx.bot.pool.execute("INSERT INTO econ VALUES ($1, $2, $3)", 0, ctx.author.id, ctx.guild.id) # pylint: disable=E1101
            return True
        else:
            return True
        return False

    # Amount or all
    class AmountConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                return int(argument)
            except:
                pass
            if "all" in argument:
                # Get users coins
                coins = await ctx.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
                return coins
            elif "," in argument:
                return int(argument.replace(",", ""))
            else:
                return 0

    # SHOP: Show roles (REQ_NONE)
    @commands.group(invoke_without_command = True)
    async def shop(self, ctx):
        # Get shop roles for the current guild
        roles = await self.bot.pool.fetch("SELECT * FROM econshop WHERE guildid = $1", ctx.guild.id)
        # Check if no roles in the guild
        if roles == None or roles == []:
            # No roles
            em = discord.Embed(color = discord.Color.dark_red())
            em.set_thumbnail(url = ctx.guild.icon_url)
            em.add_field(name = "No Roles", value = f"No roles have been found for {ctx.guild.name}")
            await ctx.send(embed = em)
            return
        # Create an embed
        em = discord.Embed(color = discord.Color.dark_red())
        em.set_thumbnail(url = ctx.guild.icon_url)
        em.set_author(name = f"{ctx.guild.name}'s Shop")
        for x in roles:
            # Get role object
            role = ctx.guild.get_role(x["roleid"])
            # Add field to embed
            em.add_field(name = f"Role: {role.name}", value = f"Required amount: {x['reqamount']:,d} {self.tcoinimage}", inline = False)
        await ctx.send(embed = em)

    # SHOP: Add roles (REQ_MANAGE_ROLES)
    @shop.command(aliases = ["role", "make"])
    @commands.bot_has_permissions(manage_roles = True)
    @commands.has_permissions(manage_roles = True)
    async def add(self, ctx, req_amount: AmountConverter, *, role: discord.Role):
        # Check if role is already in the DB
        rolecheck = await self.bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        if rolecheck != None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Found", value = "This role is already in the shop. Use the `shop edit` command to edit it")
            await ctx.send(embed = em)
            return
        # Check if amount is less than or equal to 0
        if 0 >= req_amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot set the amount at 0 or below")
            await ctx.send(embed = em)
            return
        # Add to DB
        await self.bot.pool.execute("INSERT INTO econshop VALUES ($1, $2, $3)", role.id, ctx.guild.id, req_amount)
        # Tell the user
        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Role Added", value = f"`{role.name}` has been added to the shop and requires {req_amount:,d} {self.tcoinimage} to purchase")
        await ctx.send(embed = em)

    # SHOP: Buy roles (REQ_ENOUGH_COINS)
    @shop.command(aliases = ["purchase", "spend", "get"])
    @commands.bot_has_permissions(manage_roles = True)
    @commands.check(cad_user)
    async def buy(self, ctx, *, role: discord.Role):
        # Check if the user already has the role
        if role in ctx.author.roles:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role in Possession", value = f"You already have the `{role.name}` role therefore you cannot buy it")
            await ctx.send(embed = em)
            return
        # Get the amount of coins that the role requires
        req_amount = await self.bot.pool.fetchval("SELECT reqamount FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        # Check if the role exists
        if req_amount == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Not Found", value = "This role has not been added to this shop. Use the `shop add` command to add it")
            await ctx.send(embed = em)
            return
        # Get the users coins
        user_amount = await self.bot.pool.fetchval("SELECT coins FROM econ WHERE userid = $1 AND guildid = $2", ctx.author.id, ctx.guild.id)
        # Check if the user has enough coins to complete the purchase
        if user_amount >= req_amount:
            # Give the user the role
            try:
                await ctx.author.add_roles(role, reason = f"Purchased from the shop costing {req_amount:,d} Bro Coins")
            except:
                em = discord.Embed(color = discord.Color.dark_teal())
                em.add_field(name = "Forbidden", value = f"""
                It looks like I am not able to give the user this role. Please check that my role is **above** the role you are trying to give.
                """)
                await ctx.send(embed = em)
                return
            # Remove coins from the user
            await self.bot.pool.execute("UPDATE econ SET coins = coins - $1 WHERE userid = $2 AND guildid = $3", req_amount, ctx.author.id, ctx.guild.id)
            # Tell the user
            em = discord.Embed(color = discord.Color.dark_red())
            em.add_field(name = "Purchased Role", value = f"{ctx.author.mention} bought the `{role.name}` role costing {req_amount:,d} {self.tcoinimage}")
            em.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed = em)
        else:
            # User does not have enough
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Not Enough", value = f"""
            You need {req_amount - user_amount:,d} more {self.tcoinimage} to buy the `{role.name}` role.
            """)
            await ctx.send(embed = em)

    # SHOP: Edit existing shop item (REQ_MANAGE_ROLES)
    @shop.command(aliases = ["change", "adjust"])
    @commands.has_permissions(manage_roles = True)
    async def edit(self, ctx, req_amount: AmountConverter, *, role: discord.Role):
        # Check if the role does NOT exist
        rolecheck = await self.bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        if rolecheck == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Not Found", value = "This role could not be found in the shop. You can create on using the `shop add` command")
            await ctx.send(embed = em)
            return
        # Check if amount is less than or equal to 0
        if 0 >= req_amount:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Too Small", value = f"You cannot set the amount at 0 or below")
            await ctx.send(embed = em)
            return
        # Edit the role
        await self.bot.pool.execute("UPDATE econshop SET reqamount = $1 WHERE roleid = $2 AND guildid = $3", req_amount, role.id, ctx.guild.id)
        # Tell the user
        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Role Updated", value = f"`{role.name}`'s required amount to purchase has been changed to {req_amount:,d} {self.tcoinimage}")
        await ctx.send(embed = em)

    # SHOP: Delete existing shop item (REQ_MANAGE_ROLES)
    @shop.command(aliases = ["remove"])
    @commands.has_permissions(manage_roles = True)
    async def delete(self, ctx, *, role: discord.Role):
        # Check if the role does NOT exist
        rolecheck = await self.bot.pool.fetchrow("SELECT * FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        if rolecheck == None:
            em = discord.Embed(color = discord.Color.dark_teal())
            em.add_field(name = "Role Not Found", value = "This role could not be found in the shop. You can create on using the `shop add` command")
            await ctx.send(embed = em)
            return
        # Delete role from the DB
        await self.bot.pool.execute("DELETE FROM econshop WHERE roleid = $1 AND guildid = $2", role.id, ctx.guild.id)
        # Tell the user
        em = discord.Embed(color = discord.Color.dark_red())
        em.add_field(name = "Role Deleted", value = f"`{role.name}` has been removed from the shop")
        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(EconomyShop(bot))