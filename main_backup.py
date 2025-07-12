import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import uuid
import random

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel tracking
created_channels = {}
channel_lock = asyncio.Lock()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('Bot is ready!')
    print('------')

@bot.command()
async def sidebar(ctx):
    """Create a new AI conversation channel"""
    guild = ctx.guild
    
    # Find or create the 'AIs' category
    category = discord.utils.get(guild.categories, name='AIs')
    if not category:
        category = await guild.create_category('AIs')
    
    # Generate a fun channel name
    channel_names = ['curious-alex', 'thoughtful-sam', 'helpful-taylor', 'wise-jordan']
    channel_name = random.choice(channel_names)
    
    # Create the channel
    channel = await guild.create_text_channel(channel_name, category=category)
    
    # Send notification
    message = await ctx.send(f'Sidebar created in <#{channel.id}>')
    
    # Store channel info
    async with channel_lock:
        if guild.id not in created_channels:
            created_channels[guild.id] = {}
        
        created_channels[guild.id][channel.id] = {
            'original_channel_id': ctx.channel.id,
            'message_id': message.id,
            'sender_message_id': ctx.message.id,
            'user_id': str(ctx.author.id),
            'session_id': str(uuid.uuid4())
        }
    
    # Send welcome message in the new channel
    await channel.send(f"Hello {ctx.author.mention}! I'm ready to help. What would you like to know?")
    await channel.send("*Note: Currently running without AI features. This is a basic Discord bot.*")

@bot.command()
async def exit(ctx):
    """Close the AI conversation channel"""
    channel = ctx.channel
    guild = ctx.guild
    
    # Check if this is an AI channel
    if channel.category and channel.category.name == 'AIs':
        # Clean up from our tracking
        async with channel_lock:
            if guild.id in created_channels and channel.id in created_channels[guild.id]:
                del created_channels[guild.id][channel.id]
        
        # Delete the channel
        await channel.delete()
    else:
        await ctx.send("This command can only be used in a channel under the 'AIs' category.", delete_after=10)

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Check if message contains a command - if so, let it be processed normally
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    guild = message.guild
    if not guild:
        return
    
    guild_id = guild.id
    channel_id = message.channel.id
    
    # Process the message if it is in an AI channel
    if guild_id in created_channels and channel_id in created_channels[guild_id]:
        # Basic echo functionality for now
        await message.channel.send(f"I heard you say: {message.content}\n\n*[This is a basic bot without AI features. ADK integration coming soon!]*")
    
    # Allow other commands to be processed
    await bot.process_commands(message)

if __name__ == '__main__':
    if not DISCORD_TOKEN or DISCORD_TOKEN == '<>' or DISCORD_TOKEN == 'your_discord_bot_token_here':
        print('ERROR: Please set your DISCORD_TOKEN in the .env file.')
    else:
        print('Starting Discord Bot (Basic Mode)...')
        print('Note: This version runs without ADK or Google AI features.')
        print('Commands: !sidebar (create channel), !exit (delete channel)')
        bot.run(DISCORD_TOKEN)