import aiohttp
import os
from dotenv import load_dotenv
import disnake
from disnake.ext import commands

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = commands.Bot(help_command=None,
                   command_prefix=">",
                   command_sync_flags=commands.CommandSyncFlags.all(),
                   intents = disnake.Intents.all(),
                   reload=True)

@bot.event
async def on_ready():
    await bot.change_presence(activity=disnake.Activity(
        type=disnake.ActivityType.custom, name="custom", state="testing"
    ))
    print(f"logged in as\n{bot.user.name}\n{bot.user.id}\n----")


if __name__ =="__main__":
    bot.run(BOT_TOKEN)