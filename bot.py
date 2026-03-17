import os
import time
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Role settings (Case-insensitive)
roles_env = os.getenv("ALLOWED_ROLES", "")
ALLOWED_ROLES = [r.strip().lower() for r in roles_env.split(",") if r.strip()]

bypass_env = os.getenv("BYPASS_ROLES", "")
BYPASS_ROLES = [r.strip().lower() for r in bypass_env.split(",") if r.strip()]

cmd_channel_raw = os.getenv("COMMAND_CHANNEL_ID")
COMMAND_CHANNEL_ID = int(cmd_channel_raw) if cmd_channel_raw else None

COOLDOWN = 60

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORY_NAME = "Private Rooms"

user_cooldowns = {}
queue = asyncio.Queue()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Check if worker is already running to avoid duplicates on reconnect
    if not hasattr(bot, 'worker_started'):
        bot.loop.create_task(queue_worker())
        bot.worker_started = True


async def queue_worker():
    while True:
        ctx, name, limit = await queue.get()
        try:
            guild = ctx.guild

            category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
            if category is None:
                category = await guild.create_category(CATEGORY_NAME)
                await asyncio.sleep(1)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True),
                ctx.author: discord.PermissionOverwrite(
                    manage_channels=True,
                    move_members=True
                )
            }

            await guild.create_voice_channel(
                name=name,
                category=category,
                user_limit=limit,
                overwrites=overwrites
            )

            await asyncio.sleep(2)

            await ctx.send(f"✅ Room created: **{name}** (Limit: {limit})")

        except Exception as e:
            try:
                await ctx.send(f"❌ Error: {e}")
            except:
                pass

        queue.task_done()
        await asyncio.sleep(2)


@bot.command(name="pr")
async def create_private_room(ctx, name: str, limit: int):

    if ctx.channel.id != COMMAND_CHANNEL_ID:
        return

    user = ctx.author
    user_roles = [role.name.lower() for role in user.roles]

    if not any(role in ALLOWED_ROLES for role in user_roles):
        await ctx.send("❌ You are not allowed to create private rooms (Missing Role).")
        return

    has_bypass = any(role in BYPASS_ROLES for role in user_roles)

    if not has_bypass:
        now = time.time()
        last = user_cooldowns.get(user.id, 0)
        remaining = COOLDOWN - (now - last)

        if remaining > 0:
            await ctx.send(f"⏳ Wait {int(remaining)} seconds.")
            return

        user_cooldowns[user.id] = int(now)

    if limit < 1 or limit > 99:
        await ctx.send("❌ Limit must be between 1 and 99.")
        return

    if not ctx.author.voice:
        await ctx.send("❌ You must join a voice channel first.")
        return

    await queue.put((ctx, name, limit))
    await ctx.send("⏳ Creating your room...")


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        channel = before.channel
        if channel.category and channel.category.name == CATEGORY_NAME:
            if len(channel.members) == 0:
                try:
                    await channel.delete()
                except:
                    pass


if __name__ == "__main__":
    bot.run(TOKEN)
