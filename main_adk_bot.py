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

# Set API key
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

# Import ADK components
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel tracking
created_channels = {}
channel_lock = asyncio.Lock()

# Initialize ADK Agent
adk_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='discord_agent',
    description='A helpful assistant for user questions in Discord channels.',
    instruction='''Your name is {channel_name}. You are talking with a person named {user}. 
    Answer user questions to the best of your knowledge and engage in helpful conversation.
    When users ask about current events, stock prices, news, or anything that might have changed recently,
    use the web search tool to find current information.''',
    tools=[google_search]
)

# Initialize Session Service
session_service = InMemorySessionService()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('ADK Discord Agent is ready with web search!')
    print('------')

@bot.command()
async def sidebar(ctx):
    """Create a new AI conversation channel"""
    print(f"Creating channel for user: {ctx.author.name}")
    
    guild = ctx.guild
    
    category = discord.utils.get(guild.categories, name='AIs')
    if not category:
        category = await guild.create_category('AIs')
    
    channel_names = ['curious-alex', 'thoughtful-sam', 'helpful-taylor', 'wise-jordan']
    channel_name = random.choice(channel_names)
    
    channel = await guild.create_text_channel(channel_name, category=category)
    
    message = await ctx.send(f'Sidebar created in <#{channel.id}>')
    
    # Create ADK session
    user_id = str(ctx.author.id)
    session_id = str(uuid.uuid4())
    
    initial_state = {
        "user": ctx.author.display_name,
        "channel_name": channel.name,
    }
    
    # Create session
    adk_session = await session_service.create_session(
        app_name="DiscordBot",
        user_id=user_id,
        session_id=session_id,
        state=initial_state,
    )
    
    # Store channel info
    async with channel_lock:
        if guild.id not in created_channels:
            created_channels[guild.id] = {}
        
        created_channels[guild.id][channel.id] = {
            'original_channel_id': ctx.channel.id,
            'message_id': message.id,
            'adk_session_id': adk_session.id
        }
    
    await channel.send(f"Hello {ctx.author.mention}! I'm {channel_name}. I can search the web for current information. Just talk to me naturally - no commands needed!")

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
    
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    guild = message.guild
    if not guild:
        return
    
    guild_id = guild.id
    channel_id = message.channel.id
    
    # Process messages in AI channels
    if guild_id in created_channels and channel_id in created_channels[guild_id]:
        channel_info = created_channels[guild_id][channel_id]
        
        if 'adk_session_id' in channel_info:
            adk_session_id = channel_info['adk_session_id']
            user_id = str(message.author.id)
            
            # Create runner
            runner = Runner(
                agent=adk_agent,
                app_name="DiscordBot",
                session_service=session_service,
            )
            
            # Create message
            new_message = types.Content(
                role="user", 
                parts=[types.Part(text=message.content)]
            )
            
            try:
                response_text = ""
                
                async with message.channel.typing():
                    # Run the agent
                    for event in runner.run(
                        user_id=user_id, 
                        session_id=adk_session_id, 
                        new_message=new_message
                    ):
                        if event.is_final_response():
                            if event.content and event.content.parts:
                                response_text = event.content.parts[0].text
                                break
                
                if response_text:
                    if len(response_text) > 2000:
                        chunks = [response_text[i:i+2000] for i in range(0, len(response_text), 2000)]
                        for chunk in chunks:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(response_text)
                        
            except Exception as e:
                print(f"Error: {e}")
    
    await bot.process_commands(message)

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print('ERROR: Please set your DISCORD_TOKEN in the .env file.')
    elif not GOOGLE_API_KEY:
        print('ERROR: Please set your GOOGLE_API_KEY in the .env file.')
    else:
        print('Starting Discord ADK Agent...')
        bot.run(DISCORD_TOKEN) 