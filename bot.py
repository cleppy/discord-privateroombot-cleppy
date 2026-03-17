import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Intents (🔥 EN ÖNEMLİ KISIM)
intents = discord.Intents.default()
intents.message_content = True  # 🔥 BU ŞART
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

CATEGORY_NAME = "Private Rooms"


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')


@bot.command(name='pr')
async def create_private_room(ctx, name: str, limit: int):
    guild = ctx.guild

    # Limit check
    if limit < 1 or limit > 99:
        await ctx.send("❌ Limit must be between 1 and 99.")
        return

    # Must be in voice
    if not ctx.author.voice:
        await ctx.send("❌ You must join a voice channel first!")
        return

    # Get or create category
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(CATEGORY_NAME)

    # Permissions (everyone can join)
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

        # Move user
        await ctx.author.move_to(channel)

        await ctx.send(f"✅ Room created: **{name}** (Limit: {limit})")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
        print(e)


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
