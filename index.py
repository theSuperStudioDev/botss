import discord
from discord.ext import commands
import sqlite3
import random 
import json
import os

intents = discord.Intents.default()
intents.message_content = True

my_secret = os.environ['Bot_Token']

bot = commands.Bot(command_prefix='$', intents=intents)

bot_owner_id = '994014906359742504'

# File path for the status configuration file
status_config_file = 'bot_status.json'

# Load the status from the configuration file or use default if the file doesn't exist
try:
    with open(status_config_file, 'r') as file:
        bot_status = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    bot_status = {'status': 'Default Status'}
    # Create the JSON file with default status
    with open(status_config_file, 'w') as file:
        json.dump(bot_status, file, indent=4)

# Connect to the SQLite database (create the database if it doesn't exist)
conn = sqlite3.connect('conversation_history.db')
cursor = conn.cursor()

# Create a table to store conversation history if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        user_id INTEGER,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Function to save a message to the database
def save_message(user_id, message):
    cursor.execute('INSERT INTO conversations (user_id, message) VALUES (?, ?)', (user_id, message))
    conn.commit()

# Function to retrieve conversation history for a user
def get_conversation_history(user_id):
    cursor.execute('SELECT message FROM conversations WHERE user_id = ? ORDER BY timestamp ASC', (user_id,))
    return [row[0] for row in cursor.fetchall()]

# Function to simulate a chatbot's response
def chat_with_bot(user_message, conversation_history):
    user_message = user_message.lower()  # Convert user's message to lowercase for easier matching
    if user_message.startswith('$'):
        return None
  
    greetings = ['Hello there!', 'Hi!', 'Hey!', 'Greetings!', 'How can I help you today?']
    farewells = ['Goodbye!', 'Farewell!', 'See you later!', 'Take care!', 'Have a great day!']
    how_are_you = ["I'm just a bot, but I'm here to assist you.", "I'm doing well. Thanks for asking.", "I'm here to help, what can I do for you?"]
    jokes = [
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why don't scientists trust atoms? Because they make up everything!",
    "Parallel lines have so much in common. It's a shame they'll never meet.",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "What do you get when you cross a snowman and a vampire? Frostbite.",
    "Why did the bicycle fall over? Because it was two-tired.",
    "I used to play piano by ear, but now I use my hands.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
    "I told my computer I needed a break, and now it won't stop laughing.",
    "I couldn't figure out why the baseball kept getting larger. Then it hit me.",
    "I used to be a baker, but I couldn't make enough dough.",
    "I'm on a seafood diet. I see food, and I eat it.",
    "Why don't skeletons fight each other? They don't have the guts.",
    "I'm writing a book on reverse psychology. Please don't buy it.",
    "Why don't oysters donate to charity? Because they are shellfish.",
    "I used to be a baker, but I couldn't make enough dough.",
    "Why did the tomato turn red? Because it saw the salad dressing!",
    "I'm friends with all electricians. We have such great current connections.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
    "Did you hear about the kidnapping at the playground? They woke up.",
    "Why did the math book look sad? Because it had too many problems.",
    "I'm friends with all electricians. We have such great current connections.",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "I couldn't figure out why the baseball kept getting larger. Then it hit me.",
    "I'm friends with all electricians. We have such great current connections.",
    "Why did the bicycle fall over? Because it was two-tired.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
    "I used to be a baker, but I couldn't make enough dough.",
    "Why did the tomato turn red? Because it saw the salad dressing!",
    "I'm friends with all electricians. We have such great current connections."
]
    creators = ["I was created by a team of developers at Supers Studio.", "My creators are talented individuals from Supers Studio.", "Supers Studio. brilliant minds are responsible for my existence."]
    help_responses = ["I can assist with various tasks. Try commands like `$help` to see available options.", "You can ask me for help with various commands. Type `$help` to get started."]
    
    # Define responses based on keywords or patterns in the user's message
    if 'hello' in user_message:
        return random.choice(greetings)
    elif 'how are you' in user_message:
        return random.choice(how_are_you)
    elif 'bye' in user_message:
        return random.choice(farewells)
    elif 'help' in user_message:
        return random.choice(help_responses)
    elif 'tell me a joke' in user_message:
        return random.choice(jokes)
    elif 'who created you' in user_message:
        return random.choice(creators)
    else:
        # If no specific keyword is matched, provide a generic response
        return "I didn't quite catch that. Can you please rephrase your message?"
  
    # You can add more response patterns based on your bot's specific purpose and functionality
    # For simplicity, we'll echo the user's message and display conversation history
    history_str = '\n'.join(conversation_history)
    response = f'You said: "{user_message}"\n\nConversation history:\n{history_str}'
    return response

# Set the bot's status to the one from the configuration file
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    
    # Set the bot's status
    game = discord.Game(name=bot_status['status'])
    await bot.change_presence(activity=game)

# Function to save the bot's status to the configuration file
def save_bot_status():
    with open(status_config_file, 'w') as file:
        json.dump(bot_status, file, indent=4)

@bot.command()
async def admin(ctx):
    bot_owner_id = bot_owner_id  # Replace with the actual bot owner's user ID
    
    if str(ctx.message.author.id) == bot_owner_id:
        await ctx.send("Admin Panel\nPlease select an option: 'Set Status', 'Set Nickname'")
        
        try:
            response = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The admin panel has timed out.")
            return
        
        if response.content.lower() == 'set status':
            await ctx.send("You selected 'Set Status'. Please enter the new status:")
            try:
                new_status = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond. The admin panel has timed out.")
                return
            
            # Update the bot's status
            bot_status['status'] = new_status.content
            save_bot_status()
            
            # Set the bot's status
            game = discord.Game(name=bot_status['status'])
            await bot.change_presence(activity=game)
            
            await ctx.send(f"Bot status set to '{new_status.content}'.")
        elif response.content.lower() == 'set nickname':
            await ctx.send("You selected 'Set Nickname'. Please enter the new nickname:")
            try:
                new_nickname = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond. The admin panel has timed out.")
                return
            
            # Set the bot's nickname
            guild = ctx.guild
            me = guild.me
            await me.edit(nick=new_nickname.content)
            
            await ctx.send(f"Bot nickname set to '{new_nickname.content}'.")
        else:
            await ctx.send("Invalid option. Available options: 'Set Status', 'Set Nickname'")
    else:
        await ctx.send("You don't have permission to access the admin panel.")
  
# Command to set the bot's status (only accessible by the bot owner)
@bot.command()
async def setstatus(ctx, *, status):
    if str(ctx.message.author.id) == bot_owner_id:
        await bot.change_presence(activity=discord.Game(name=status))
        await ctx.send(f"Bot status set to '{status}'.")
    else:
        await ctx.send("You don't have permission to change the bot's status.")

# Function to generate a response to the bot owner's message
def generate_bot_owner_response(message_content):
    # Implement your logic to generate a response to the bot owner here
    # For example, you can use conditional statements to trigger specific responses
    if 'hello' in message_content.lower():
        return 'Hello, Bot Owner!'
    else:
        return 'I received your message, Bot Owner.'

@bot.command()
async def ban(ctx, user: discord.Member):
    if ctx.author.guild_permissions.ban_members:
        try:
            await user.ban()
            await ctx.send(f'{user.name} has been banned.')
        except discord.Forbidden as e:  # Import and use 'discord.Forbidden'
            await ctx.send(f"Error: {e}")
    else:
        await ctx.send("You don't have the required permissions to ban members.")

@bot.command()
async def purge(ctx, amount: int):
    if ctx.author.guild_permissions.manage_messages:
        try:
            await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
            await ctx.send(f'{amount} messages have been purged.')
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage messages.")
    else:
        await ctx.send("You don't have the required permissions to manage messages.")

# Add more commands as needed

bot.run(my_secret)
