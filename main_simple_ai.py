import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import google.generativeai as genai
import asyncio
import random

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure Google AI
genai.configure(api_key=GOOGLE_API_KEY)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel tracking (keeping your existing features)
created_channels = {}
channel_lock = asyncio.Lock()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('Bot with simple AI is ready!')
    print('Commands: !sidebar, !exit, !ai')
    print('------')

@bot.command()
async def ai(ctx, *, question):
    """Ask the AI a question! Usage: !ai your question here"""
    async with ctx.typing():
        try:
            # Use Google AI directly (no ADK)
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(question)
            
            # Send the response
            await ctx.send(f"🤖 {response.text}")
            
        except Exception as e:
            print(f"AI Error: {e}")
            await ctx.send("Sorry, I couldn't get a response from the AI.")

@bot.command()
async def sidebar(ctx):
    """Create a new AI conversation channel"""
    guild = ctx.guild
    
    category = discord.utils.get(guild.categories, name='AIs')
    if not category:
        category = await guild.create_category('AIs')
    
    channel_names = ['curious-alex', 'thoughtful-sam', 'helpful-taylor', 'wise-jordan']
    channel_name = random.choice(channel_names)
    
    channel = await guild.create_text_channel(channel_name, category=category)
    
    message = await ctx.send(f'Sidebar created in <#{channel.id}>')
    
    async with channel_lock:
        if guild.id not in created_channels:
            created_channels[guild.id] = {}
        
        created_channels[guild.id][channel.id] = {
            'original_channel_id': ctx.channel.id,
            'message_id': message.id,
            'user_id': str(ctx.author.id),
        }
    
    await channel.send(f"Hello {ctx.author.mention}! I'm {channel_name}. Try the `!ai` command to ask me questions!")

@bot.command()
async def exit(ctx):
    """Close the AI conversation channel"""
    channel = ctx.channel
    guild = ctx.guild
    
    if channel.category and channel.category.name == 'AIs':
        async with channel_lock:
            if guild.id in created_channels and channel.id in created_channels[guild.id]:
                del created_channels[guild.id][channel.id]
        await channel.delete()
    else:
        await ctx.send("This command can only be used in a channel under the 'AIs' category.", delete_after=10)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == '__main__':
    if not DISCORD_TOKEN or DISCORD_TOKEN == '<>':
        print('ERROR: Please set your DISCORD_TOKEN in the .env file.')
    elif not GOOGLE_API_KEY or GOOGLE_API_KEY == '<>':
        print('ERROR: Please set your GOOGLE_API_KEY in the .env file.')
    else:
        print('Starting Discord Bot with Simple AI...')
        bot.run(DISCORD_TOKEN) 