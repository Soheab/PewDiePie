from discord.ext import commands
import discord
import random
import asyncio

# I did not make this cog. Xua#4427 made it for me.

class AuthSupport:
    def __init__(self, bot):
        self.bot = bot
        self.rules_channel = 499363307497717760
        self.mod_role = 529131523442606081
        self.bots_role = 527324384906575872
        self.guild = 499357399690379264
        self.unauth_role = 533413153866907663
        self.auth_channel = 533413474303213596

        self.questions = {
            # "question": "answer"
            "What is the result of posting anything NSFW?": ("ban", "bamboozled"),
            "Ghost pinging is the 5th rule. True or False?": ("false",),
            "What is the age requirement mentally?": ("13",),
            "What is the age requirement physically?": ("13",),
            "Where are you allowed to advertise?": ("nowhere", "you aren't", "you arent", "no where", "prohibited"),
            "Is it fine to hoist your name to the top of the list? True or False": ("no", "false", "nowhere", "ofc not"),
            "What were to happen if you cuss out the mods?": ("ban", "have a sad life", "you get rekt", "rekt"),
            "What happens if you spam?": ("ban", "rekt", "mute", "you can't", "life happens")
        }

    async def on_message(self, message: discord.Message):
        await self.bot.wait_until_ready()
        if message.guild.id != self.guild:
            return
        if message.channel.id != self.auth_channel:
            return
        say = ["i have read the rules and accept the terms.", "i have read the rules and accept the terms"]
        if message.content.lower() in say:
            question = random.choice(list(self.questions.keys()))
            answer = self.questions[question]
            await message.channel.send(question)

            def check(m):
                if m.channel.id == self.auth_channel:
                    if m.author == message.author:
                        return any(i in m.content.lower() for i in answer)
                    return False
                return False

            await self.bot.wait_for("message", check=check)
            await message.author.remove_roles(message.guild.get_role(self.unauth_role))

    async def on_member_join(self, member: discord.Member):
        if member.guild.id != self.guild:
            return
        await member.add_roles(member.guild.get_role(self.unauth_role))
        await asyncio.sleep(1.3)
        await self.bot.http.send_message(
            self.auth_channel,
            (f"{member.mention}, please read <#499363307497717760> before you may proceed into the server. "
             "After reading the rules, please send `I have read the rules and accept the terms.`")
        )


def setup(bot):
    bot.add_cog(AuthSupport(bot))
