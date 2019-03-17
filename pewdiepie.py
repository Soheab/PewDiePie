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

async def custom_prefix(bot, message):
    await bot.wait_until_ready()

    try:
        prefix = bot.prefixes.get(message.guild.id)
    except AttributeError:
        rnd = random.randint(12**2, 12**4)
        return str(rnd)

    if prefix == None:
        return commands.when_mentioned_or(*bot.default_prefixes)(bot, message)
    else:
        return commands.when_mentioned_or(prefix)(bot, message)

extensions = (
    "cogs.functions", "jishaku", "cogs.economy", "cogs.general",
    "cogs.subscribe", "cogs.owner", "cogs.error_handler",
    "cogs.events", "cogs.economy_phrases", "cogs.economy_shop",
    "cogs.economy_owner", "cogs.help", "cogs.disstrack", "cogs.snipe"
)

class PewDiePie(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix = custom_prefix,
            case_insensitive = True,
            max_messages = 500,
            fetch_offline_members = False,
            reconnect = True
        )

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.utcnow()
        
        print(f"{self.user.name} is ready!")

    async def on_connect(self):
        if not hasattr(self, "pool"):
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
                print(f"\n{error}")
            
        with open("schema.sql", "r") as schema:
            await self.pool.execute(schema.read())

        prefixes = await self.pool.fetch("SELECT * FROM prefixes")
        self.prefixes = {}
        for current_row in prefixes:
            self.prefixes[current_row["guildid"]] = current_row["prefix"]

        self.default_prefixes = [
            "p.", "P.", "p!", "P!",
            "t.", "t!", "ts!", "ts.",
            "Ts!", "tS!", "TS!", "T.", "T!",
            "Ts.", "tS.", "TS."
        ]

        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as error:
                print(f"There was a problem loading in the {extension} extension")
                print(f"\n{error}")

    async def start(self):
        await self.login(config.pubtoken) # pylint: disable=no-member
        try:
            await self.connect()
        except KeyboardInterrupt:
            await self.stop()

    async def stop(self):
        for cog in self.cogs:
            self.unload_extension(cog)

        await self.pool.close()
        await super().logout()

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            loop.run_until_complete(self.stop())


if __name__ == "__main__":
    PewDiePie().run()