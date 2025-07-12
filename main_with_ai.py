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

# Set the API key for Google AI
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

# Import ADK components (we know these work!)
from google.adk.agents import LlmAgent
from google.genai import types

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel tracking
created_channels = {}
channel_lock = asyncio.Lock()

# Create a simple AI agent
ai_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='discord_helper',
    description='A helpful Discord assistant',
    instruction='You are a friendly AI assistant. Keep responses brief and helpful.'
)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('Bot with AI is ready!')
    print('------')

@bot.command()
async def ai(ctx, *, question):
    """Ask the AI a question! Usage: !ai your question here"""
    async with ctx.typing():
        try:
            # Use Runner to execute the agent
            from google.adk.runners import Runner
            # Create a runner
            runner = Runner(
                agent=ai_agent,
                app_name="DiscordBot"
            )
            # Create a message
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=question)]
            )
            # Run and get response
            response_text = ""
            for event in runner.run(user_id="discord_user", new_message=user_message):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        break
            # Send the response
            if response_text:
                await ctx.send(f"🤖 {response_text}")
            else:
                await ctx.send("🤖 I couldn't generate a response. Please try again.")
        except Exception as e:
            print(f"AI Error: {e}")
            await ctx.send("Sorry, I encountered an error. Please try again later.")

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
            'user_id': str(ctx.author.id),
        }
    # Send welcome message
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
    # Process commands
    await bot.process_commands(message)

if __name__ == '__main__':
    if not DISCORD_TOKEN or DISCORD_TOKEN == '<>' or DISCORD_TOKEN == 'your_discord_bot_token_here':
        print('ERROR: Please set your DISCORD_TOKEN in the .env file.')
    elif not GOOGLE_API_KEY or GOOGLE_API_KEY == '<>' or GOOGLE_API_KEY == 'your_google_ai_studio_api_key_here':
        print('ERROR: Please set your GOOGLE_API_KEY in the .env file.')
    else:
        print('Starting Discord Bot with AI...')
        bot.run(DISCORD_TOKEN)