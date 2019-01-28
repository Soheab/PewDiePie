import discord
from discord.ext import commands
import config
import random
import datetime
import asyncpg
import aiohttp
import asyncio
import sys

# Support asyncio subprocesses for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Custom prefixes
async def custom_prefix(bot, message):
    await bot.wait_until_ready()
    default_prefix = ["ts!", "ts.", "t.", "t!", "T."]
    try:
        prefixes = await bot.pool.fetchrow("SELECT * FROM prefixes WHERE guildid = $1", message.guild.id)
    except AttributeError:
        # Is a DM
        rnd = random.randint(12**13, 12**200)
        return str(rnd)
    if prefixes == None or prefixes == []:
        return commands.when_mentioned_or(*default_prefix)(bot, message)
    else:
        g = prefixes["guildid"]
        cp = prefixes["prefix"]
        prefixes = {
            g: [cp]
        }
        return commands.when_mentioned_or(*prefixes.get(message.guild.id, []))(bot, message)

# Extensions
extensions = (
    "economy", "general", "subscribe", "owner",
    "error_handler", "events", "economy_phrases", "economy_shop",
    "economy_owner"
    )

# Important extensions
important = ("jishaku", "authsupport")

# Bot
class tseries(commands.AutoShardedBot):
    def __init__(self, token):
        self.custom_prefix = custom_prefix
        self.token = token
        super().__init__(
            command_prefix = self.custom_prefix,
            case_insensitive = True,
            max_messages = 500,
            fetch_offline_members = False,
            reconnect = True
        )
        # Client session
        self.session = aiohttp.ClientSession(loop = self.loop)
        # Load in important extensions
        for x in important:
            try:
                self.load_extension(x)
            except:
                print(f"There was a problem loading in the {x} extension")
        # Load in extensions
        for x in extensions:
            try:
                self.load_extension("cogs." + x)
            except:
                print(f"There was a problem loading in the {x} extension")

    async def on_ready(self):
        if hasattr(self, "uptime") == False:
            self.uptime = datetime.datetime.utcnow()

        print(f"{self.user.name} is ready!")

    async def database(self):
        if hasattr(self, "pool") == False:
            pool_creds = {
                "user": config.db_user,
                "password": config.db_password,
                "port": 5432,
                "host": "localhost",
                "database": "tseries"
            }
            try:
                self.pool = await asyncpg.create_pool(**pool_creds)
            except Exception as error:
                print("There was a problem connecting to the database")
                print("\n", error)

    async def close(self):
        # Close pool
        await self.pool.close()
        # Close aiohttp client session
        await self.session.close()
        # Close bot
        await super().close()
        # Print to console
        print("\n", "Closed")

    def run(self):
        try:
            self.loop.create_task(self.database())
        except:
            print("There was a problem creating the database task")
        try:
            super().run(self.token)
        except Exception as error:
            print("There was a problem running the bot")
            print("\n", error)


if __name__ == "__main__":
    bot = tseries(config.pubtoken)
    bot.run()