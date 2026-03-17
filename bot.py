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

# COOLDOWN settings
COOLDOWN = 60

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='.', intents=intents)

CATEGORY_NAME = "═══⊹⊱≼𝙿𝚁𝙸𝚅𝙰𝚃𝙴 𝚁𝙾𝙾𝙼𝚂≽⊰⊹═══"

user_cooldowns = {}
queue = asyncio.Queue()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Checking permissions in guilds...")
    for guild in bot.guilds:
        perms = guild.me.guild_permissions
        print(f"Server: {guild.name}")
        print(f" - Manage Channels: {perms.manage_channels}")
        print(f" - Manage Roles: {perms.manage_roles}")
        if not perms.manage_channels or not perms.manage_roles:
            print("⚠️ WARNING: Bot is missing critical permissions!")

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

            # Set permissions: Everyone and Viewer can view, connect, speak, message, and stream.
            # Author gets full control over their room.
            viewer_role = next((r for r in guild.roles if r.name.lower() == "viewer"), None)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True, connect=True, speak=True, 
                    send_messages=True, stream=True, use_embedded_activities=True,
                    use_voice_activation=True, use_soundboard=True, use_external_sounds=True
                ),
                ctx.author: discord.PermissionOverwrite(
                    view_channel=True, connect=True, speak=True, 
                    send_messages=True, stream=True, use_embedded_activities=True,
                    use_voice_activation=True, use_soundboard=True, use_external_sounds=True,
                    manage_channels=True, manage_permissions=True
                )
            }

            if viewer_role:
                overwrites[viewer_role] = discord.PermissionOverwrite(
                    view_channel=True, connect=True, speak=True, 
                    send_messages=True, stream=True, use_embedded_activities=True,
                    use_voice_activation=True, use_soundboard=True, use_external_sounds=True
                )

            channel = await guild.create_voice_channel(
                name=name,
                category=category,
                user_limit=limit,
                overwrites=overwrites
            )

            # Move user to the new channel if they are still in a voice channel
            if ctx.author.voice:
                try:
                    await ctx.author.move_to(channel)
                except Exception as e:
                    print(f"Could not move user: {e}")

            await asyncio.sleep(2)

            await ctx.send(f"✅ {ctx.author.mention} Room created: **{name}** (Limit: {limit})")

        except discord.Forbidden as e:
            error_msg = f"❌ Permission Error (403): {e.text}. Ensure the bot has 'Manage Channels' and 'Manage Roles' permissions."
            print(error_msg)
            try:
                await ctx.send(error_msg)
            except:
                pass
        except Exception as e:
            error_msg = f"❌ Error: {e}"
            print(error_msg)
            try:
                await ctx.send(error_msg)
            except:
                pass

        queue.task_done()
        await asyncio.sleep(2)


@bot.command(name="pr")
async def create_private_room(ctx, name: str, limit: int):
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
