import discord
from discord.ext import commands
import datetime


class Help:
    def __init__(self, bot):
        self.bot = bot
        # Remove default help command
        self.bot.remove_command("help")

    # Help command
    @commands.group(invoke_without_command = True)
    async def help(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        em.set_author(name = f"{self.bot.user.name} Help Page")
        # Main commands
        em.add_field(name = "Main Commands", value = """
        `disstrack`: Plays Bitch Lasagna in a voice channel. To disconnect, run `p.disstrack stop` or `p.disstrack leave`
        `subcount`: Shows T-Series' and PewDiePie's subscriber count
        `subgap`: Automatically updates the current subscriber gap between PewDiePie and T-Series every 30 seconds. Your server must be authorized to use this feature.
        Please join the [support server](https://discord.gg/we4DQ5u) to request authorization.
        `randomvid`: Returns a random PewDiePie or T-Series video
        `youtube (yt)`: Sends you the link to PewDiePie's and T-Series' YouTube channel
        `spoiler`: Sends any message you provide as a spoiler in an annoying form
        """, inline = False)
        # Bro Coin (economy) commands
        em.add_field(name = "Bro Coin (economy)", value = """
        Run `p.help economy` to view the list of commands for Bro Coin
        """)
        # Meta commands
        em.add_field(name = "Meta Commands", value = f"""
        `botinfo`: Information on {self.bot.user.name}
        `invite`: Sends the bot invite
        `feedback`: This command will send the developer feedback on this bot. Feel free to send suggestions or issues
        `prefixtut`: This will give you a tutorial on how to use custom prefixes on {self.bot.user.name}
        `prefix`: Returns the current prefix that {self.bot.user.name} uses in your server
        """, inline = False)
        # Timestamp
        em.timestamp = datetime.datetime.utcnow()
        em.set_footer(icon_url = ctx.author.avatar_url, text = f"{ctx.author.name}#{ctx.author.discriminator}")
        await ctx.send(embed = em)

    # Help: economy
    @help.command()
    async def economy(self, ctx):
        em = discord.Embed(color = discord.Color.gold())
        em.set_author(name = f"{self.bot.user.name} Economy Help Page")
        em.add_field(name = "Bro Coin Commands", value = """
        `shovel`: You work all day shoveling for Bro Coins
        `balance (bal)`: Informs you on how many Bro Coins you have
        `pay`: Pays a user with a specified amount of Bro Coins
        `leaderboard (lb)`: Shows the leaderboard for Bro Coins
        `gamble`: You can gamble a specific amount of Bro Coins
        `steal (rob)`: Steals from a user that you specify
        `transfer`: Sends Bro Coins to another server. The max amount is 50% of your coins.
        `statistics (stats)`: Statistics on Bro Coin usage
        """, inline = False)
        em.add_field(name = "Shop", value = """
        `shop`: View all the items (roles) in the shop
        `shop add`: Adds a role to the shop (you must have the manage roles permission)
        `shop edit`: Edits a role (eg. changes the cost) in the shop (manage roles permission required by user)
        `shop delete (remove)`: Removes a role from the shop (manage roles permission required by user)
        `shop buy`: Buys an item from the shop (you must have enough coins)
        **Please note: The bot must have the manage roles permission and be higher than the role in the shop to use the shop feature**
        """, inline = False)
        # Timestamp
        em.timestamp = datetime.datetime.utcnow()
        em.set_footer(icon_url = ctx.author.avatar_url, text = f"{ctx.author.name}#{ctx.author.discriminator}")
        await ctx.send(embed = em)


def setup(bot):
    bot.add_cog(Help(bot))