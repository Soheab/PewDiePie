"""
Rename this file to config.py. You will need PostgreSQL, git, discord.py rewrite, and asyncpg.

Download PostgreSQL: https://www.postgresql.org/download/

Download git: https://git-scm.com/download/

discord.py rewrite: `pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]`

asyncpg: `pip install -U asyncpg`
"""

privtoken = "" # Use this token for testing on your development bot
pubtoken = "" # Use this token on your live bot

# The bot will automatically start with the pubtoken token.
# You can search for "config.pubtoken" in the pewdiepie.py file and change that

dbltoken = "" # This is your Discord Bot List token. If you don't have one, change "" to None

ytdapi = "" # This is your token for accessing YouTube's API. You MUST have this to use the subcount command

db_user = "" # Username for logging into your database
db_password = "" # Password for your database

# Please note that you must have a database called tseries