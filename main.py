import os
import sys
import traceback
from dotenv import load_dotenv
import disnake
from disnake.ext import commands


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = commands.InteractionBot(
    intents=disnake.Intents.default(),
    reload=True,
)

# noinspection PyBroadException
try:
    bot.load_extension("cogs.radio")
except Exception:
    print("Failed to load extension radio", file=sys.stderr)
    traceback.print_exc()


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=disnake.Activity(type=disnake.ActivityType.listening, name="/radio")
    )
    print(f"logged in as\n{bot.user.name}\n{bot.user.id}\n----")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
