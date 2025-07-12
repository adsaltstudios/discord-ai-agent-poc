import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import uuid
from google.adk import Agent, InMemorySessionService, Runner, google_search
from google.cloud import aiplatform
import google.genai as genai
from google.genai import types

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure Google AI
if int(os.getenv('GOOGLE_GENAI_USE_VERTEXAI', '0')):
    # Use Vertex AI
    aiplatform.init()
else:
    # Use Google AI Studio
    genai.configure(api_key=GOOGLE_API_KEY)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel tracking
created_channels = {}
channel_lock = asyncio.Lock()

# Initialize ADK Agent
adk_agent = Agent(
    model='gemini-2.0-flash',
    name='discord_agent',
    description='A helpful assistant for user questions in Discord channels.',
    instruction='''Your name is {channel_name}. You are talking with a person named {user}. 
    Answer user questions to the best of your knowledge and engage in helpful conversation.
    You have access to web search when needed to provide current information.''',
    tools=[google_search]
)

# Initialize Session Service
session_service_stateful = InMemorySessionService()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def sidebar(ctx):
    """Create a new AI conversation channel"""
    guild = ctx.guild
    
    # Find or create the 'AIs' category
    category = discord.utils.get(guild.categories, name='AIs')
    if not category:
        category = await guild.create_category('AIs')
    
    # Generate a fun channel name (you can customize this)
    channel_names = ['curious-alex', 'thoughtful-sam', 'helpful-taylor', 'wise-jordan']
    import random
    channel_name = random.choice(channel_names)
    
    # Create the channel
    channel = await guild.create_text_channel(channel_name, category=category)
    
    # Send notification
    message = await ctx.send(f'Sidebar created in <#{channel.id}>')
    
    # Create a new ADK session for the Discord channel
    user_id = str(ctx.author.id)
    session_id = str(uuid.uuid4())
    
    initial_state = {
        "user": ctx.author.display_name,
        "channel_name": channel.name,
        "user_preferences": "The user is interacting via Discord.",
    }
    
    # Create session
    adk_session = await session_service_stateful.create_session(
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
            'sender_message_id': ctx.message.id,
            'adk_session_id': adk_session.id
        }
    
    # Send welcome message in the new channel
    await channel.send(f"Hello {ctx.author.mention}! I'm ready to help. What would you like to know?")

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
        channel_info = created_channels[guild_id][channel_id]
        
        if 'adk_session_id' in channel_info:
            adk_session_id = channel_info['adk_session_id']
            user_id = str(message.author.id)
            
            # Create runner for this interaction
            runner = Runner(
                agent=adk_agent,
                app_name="DiscordBot",
                session_service=session_service_stateful,
            )
            
            # Create message for ADK
            new_message = types.Content(
                role="user", 
                parts=[types.Part(text=message.content)]
            )
            
            try:
                response_text = ""
                
                # Show typing indicator
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
                
                # Send response
                if response_text:
                    # Split long messages if needed
                    if len(response_text) > 2000:
                        chunks = [response_text[i:i+2000] for i in range(0, len(response_text), 2000)]
                        for chunk in chunks:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(response_text)
                        
            except Exception as e:
                print(f"Error running ADK Agent: {e}")
                await message.channel.send("I encountered an error while processing your request. Please try again.")
    
    # Allow other commands to be processed
    await bot.process_commands(message)

if __name__ == '__main__':
    if not DISCORD_TOKEN or DISCORD_TOKEN == '<>' or DISCORD_TOKEN == 'your_discord_bot_token_here':
        print('ERROR: Please set your DISCORD_TOKEN in the .env file.')
    elif not GOOGLE_API_KEY or GOOGLE_API_KEY == '<>' or GOOGLE_API_KEY == 'your_google_ai_studio_api_key_here':
        print('ERROR: Please set your GOOGLE_API_KEY in the .env file.')
    else:
        print('Starting Discord ADK Agent...')
        bot.run(DISCORD_TOKEN)