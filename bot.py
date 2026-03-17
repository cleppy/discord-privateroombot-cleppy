import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot ayarları
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

CATEGORY_NAME = "Private Rooms"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')

@bot.command(name='pr')
async def create_private_room(ctx, name: str, limit: int):
    """
    Creates a private voice room with a specified name and member limit.
    Example: !pr "My Room" 5
    """
    guild = ctx.guild
    
    # Find or create "Private Rooms" category
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(CATEGORY_NAME)
        print(f'Category "{CATEGORY_NAME}" created.')

    # Create voice channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=True),
        ctx.author: discord.PermissionOverwrite(manage_channels=True, move_members=True)
    }

    try:
        new_channel = await guild.create_voice_channel(
            name=name,
            category=category,
            user_limit=limit,
            overwrites=overwrites
        )
        await ctx.send(f'✅ Room **{name}** created! (Limit: {limit})')
        print(f'New room created: {name} by {ctx.author}')
    except Exception as e:
        await ctx.send(f'❌ Error creating room: {e}')
        print(f'Error: {e}')

@bot.event
async def on_voice_state_update(member, before, after):
    """
    Monitors voice channels and deletes empty ones in the "Private Rooms" category.
    """
    if before.channel is not None:
        channel = before.channel
        
        if channel.category and channel.category.name == CATEGORY_NAME:
            if len(channel.members) == 0:
                try:
                    await channel.delete(reason="Room deleted automatically because it was empty.")
                    print(f'Empty room deleted: {channel.name}')
                except Exception as e:
                    print(f'Error deleting room ({channel.name}): {e}')

if __name__ == '__main__':
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Hata: DISCORD_TOKEN bulunamadı. Lütfen .env dosyasını kontrol edin.")
