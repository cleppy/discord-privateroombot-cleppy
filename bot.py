import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

ALLOWED_ROLES = ["Member", "VIP"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORY_NAME = "Private Rooms"


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="pr")
@commands.cooldown(1, 600, commands.BucketType.user)
async def create_private_room(ctx, name: str, limit: int):
    guild = ctx.guild

    # role check
    user_roles = [role.name for role in ctx.author.roles]
    if not any(role in ALLOWED_ROLES for role in user_roles):
        await ctx.send("❌ You are not allowed to create private rooms.")
        return

    # limit validation
    if limit < 1 or limit > 99:
        await ctx.send("❌ Limit must be between 1 and 99.")
        return

    # user must be in voice
    if not ctx.author.voice:
        await ctx.send("❌ You must join a voice channel first.")
        return

    # get or create category
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(CATEGORY_NAME)

    # permissions
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=True),
        ctx.author: discord.PermissionOverwrite(
            manage_channels=True,
            move_members=True
        )
    }

    try:
        channel = await guild.create_voice_channel(
            name=name,
            category=category,
            user_limit=limit,
            overwrites=overwrites
        )

        await ctx.author.move_to(channel)

        await ctx.send(f"✅ Room created: **{name}** (Limit: {limit})")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(e)


@create_private_room.error
async def pr_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes = int(error.retry_after // 60)
        seconds = int(error.retry_after % 60)
        await ctx.send(f"⏳ Wait {minutes}m {seconds}s before creating another room.")


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        channel = before.channel

        if channel.category and channel.category.name == CATEGORY_NAME:
            if len(channel.members) == 0:
                try:
                    await channel.delete()
                except Exception as e:
                    print(e)


if __name__ == "__main__":
    bot.run(TOKEN)
