import discord
from discord.ext import commands


class Help:
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.group(invoke_without_command = True)
    async def help(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        prefix = ctx.prefix.replace(self.bot.user.mention, f"@{self.bot.user.name}")
        em.set_author(name = f"{self.bot.user.name} Commands")

        em.add_field(name = "Main Commands", value = f"{prefix}help main")
        em.add_field(name = "Meta Commands", value = f"{prefix}help normal (meta)")
        em.add_field(name = "Economy Commands", value = f"{prefix}help economy")
        em.add_field(name = "Economy Shop Commands", value = f"{prefix}help shop")
        # em.add_field(name = "Snipe Commands", value = f"{prefix}help snipe")

        await ctx.send(embed = em)

    @help.command(aliases = ["general"])
    async def main(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        prefix = ctx.prefix.replace(self.bot.user.mention, f"@{self.bot.user.name}")
        em.set_author(name = "Main Commands")

        em.add_field(name = f"{prefix}disstrack [leave/stop]", value = f"Plays Bitch Lasagna in a voice channel", inline = False)
        em.add_field(name = f"{prefix}subcount", value = "Shows T-Series' and PewDiePie's subscriber count", inline = False)
        em.add_field(name = f"{prefix}subgap", value = """
        Automatically updates the current subscriber gap between PewDiePie and T-Series every 30 seconds. Your server must be authorized to use this feature.
        Please join the [support server](https://discord.gg/we4DQ5u) to request authorization.
        """, inline = False)
        em.add_field(name = f"{prefix}randomvid", value = "Returns a random PewDiePie or T-Series video", inline = False)
        em.add_field(name = f"{prefix}youtube (yt)", value = "Sends you the link to PewDiePie's and T-Series' YouTube channel", inline = False)
        em.add_field(name = f"{prefix}spoiler [message]", value = "Sends any message you provide as a spoiler in an annoying form", inline = False)

        await ctx.send(embed = em)

    @help.command(aliases = ["meta"])
    async def normal(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        prefix = ctx.prefix.replace(self.bot.user.mention, f"@{self.bot.user.name}")
        em.set_author(name = "Meta Commands")

        em.add_field(name = f"{prefix}botinfo", value = f"Information on {self.bot.user.name}", inline = False)
        em.add_field(name = f"{prefix}invite", value = "Sends the bot invite", inline = False)
        em.add_field(name = f"{prefix}feedback [message]", value = """
        This command will send the developer feedback on this bot. Feel free to send suggestions or issues
        """, inline = False)
        em.add_field(name = f"{prefix}prefixtut", value = f"This will give you a tutorial on how to use custom prefixes on {self.bot.user.name}", inline = False)
        em.add_field(name = f"{prefix}prefix", value = f"Returns the current prefix that {self.bot.user.name} uses in your server", inline = False)
        em.add_field(name = f"{prefix}setprefix (sprefix) [prefix]", value = "Sets the bot prefix or resets it if there is no prefix defined", inline = False)

        await ctx.send(embed = em)

    @help.command()
    async def economy(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        prefix = ctx.prefix.replace(self.bot.user.mention, f"@{self.bot.user.name}")
        em.set_author(name = "Economy Commands")

        em.add_field(name = f"{prefix}shovel", value = "You work all day shoveling for Bro Coins", inline = False)
        em.add_field(name = f"{prefix}balance (bal)", value = "Pays a user with a specified amount of Bro Coins", inline = False)
        em.add_field(name = f"{prefix}leaderboard (lb)", value = "Shows the leaderboard for Bro Coins", inline = False)
        em.add_field(name = f"{prefix}leaderboard server (guild)", value = "Shows the leadreboard of Bro Coins for your server", inline = False)
        em.add_field(name = f"{prefix}gamble [coins/all]", value = "You can gamble a specific amount of Bro Coins", inline = False)
        em.add_field(name = f"{prefix}steal (rob) [@user (or name)]", value = "Steals from a user that you specify", inline = False)
        em.add_field(name = f"{prefix}transfer [coins/all] [server name]", value = """
        Sends Bro Coins to another server. The max amount is 50% of your coins.
        """, inline = False)
        em.add_field(name = f"{prefix}statistics (stats)", value = "Statistics on Bro Coin usage", inline = False)

        await ctx.send(embed = em)

    @help.command()
    async def shop(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        prefix = ctx.prefix.replace(self.bot.user.mention, f"@{self.bot.user.name}")
        em.set_author(name = "Economy Shop Commands")

        em.add_field(name = f"{prefix}shop", value = "View all the items (roles) in the shop", inline = False)
        em.add_field(name = f"{prefix}shop add [amount] [role name]", value = "Adds a role to the shop", inline = False)
        em.add_field(name = f"{prefix}shop edit [amount] [role name]", value = "Edits a roles cost in the shop", inline = False)
        em.add_field(name = f"{prefix}shop delete (remove) [role name]", value = "Removes a role from the shop", inline = False)
        em.add_field(name = f"{prefix}shop buy [role name]", value = "Buys an item from the shop", inline = False)
        em.set_footer(text = "Note: The bot must have the manage roles permission and be higher than the role in the shop to use the shop features")

        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(Help(bot))