import discord
from discord.ext import commands
import config
import random
import datetime
import asyncpg
import aiohttp
import asyncio
import sys

# Supports asyncio subprocesses for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Custom prefixes
async def custom_prefix(bot, message):
    await bot.wait_until_ready()
    default_prefix = [
        "ts!", "ts.", "t.", "t!",
        "Ts!", "tS!", "TS!", "T.", "T!",
        "Ts.", "tS.", "TS."
    ]
    try:
        prefixes = bot.prefixes.get(message.guild.id)
    except AttributeError:
        # Is a DM
        rnd = random.randint(12**13, 12**200)
        return str(rnd)
    if prefixes == None:
        return commands.when_mentioned_or(*default_prefix)(bot, message)
    else:
        return commands.when_mentioned_or(prefixes)(bot, message)

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

    async def on_connect(self):
        await asyncio.sleep(0.5) # Preventing self.pool not being ready yet
        # Custom cachable prefixes
        prefixes = await self.pool.fetch("SELECT * FROM prefixes")
        self.prefixes = {}
        for current_row in prefixes:
            self.prefixes[current_row["guildid"]] = current_row["prefix"]
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
            except Exception as e:
                print(f"There was a problem loading in the {x} extension")
                print()
                print(e)

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
    bot = tseries(config.privtoken)
    bot.run()