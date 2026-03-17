import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents (message_content gerek yok artık)
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


CATEGORY_NAME = "Private Rooms"


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


# 🔥 SLASH COMMAND
@bot.tree.command(name="pr", description="Create a private voice room")
async def create_private_room(interaction: discord.Interaction, name: str, limit: int):
    guild = interaction.guild
    user = interaction.user

    # Limit check
    if limit < 1 or limit > 99:
        await interaction.response.send_message("❌ Limit must be between 1 and 99.", ephemeral=True)
        return

    # Check if user is in voice
    if not user.voice:
        await interaction.response.send_message("❌ You must join a voice channel first!", ephemeral=True)
        return

    # Find or create category
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(CATEGORY_NAME)

    # Permissions (everyone can join, creator manages)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=True),
        user: discord.PermissionOverwrite(
            manage_channels=True,
            move_members=True
        )
    }

    try:
        # Create channel
        channel = await guild.create_voice_channel(
            name=name,
            category=category,
            user_limit=limit,
            overwrites=overwrites
        )

        # Move user
        await user.move_to(channel)

        await interaction.response.send_message(
            f"✅ Room created: **{name}** (Limit: {limit})",
            ephemeral=True
        )

        print(f"Room created: {name}")

    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        print(e)


# Auto delete empty rooms
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        channel = before.channel

        if channel.category and channel.category.name == CATEGORY_NAME:
            if len(channel.members) == 0:
                try:
                    await channel.delete()
                    print(f"Deleted empty room: {channel.name}")
                except Exception as e:
                    print(e)


if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("DISCORD_TOKEN not found!")
