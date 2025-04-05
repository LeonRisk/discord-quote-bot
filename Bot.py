#Discord Quote Bot

import os
import discord
from discord.ext import commands
import sqlite3
import random
from datetime import datetime

DB_FILE = "quotes.db"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# ----------------------------
# DATABASE SETUP
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            channel TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            guild TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ----------------------------
# SAVE A QUOTE
# ----------------------------
def save_quote(author, content, channel, timestamp, guild):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO quotes (author, content, channel, timestamp, guild)
        VALUES (?, ?, ?, ?, ?)
    ''', (author, content, channel, timestamp, guild))
    conn.commit()
    c.execute("SELECT last_insert_rowid()")
    last_id = c.fetchone()[0]
    conn.close()
    return last_id

# ----------------------------
# GET RANDOM QUOTES
# ----------------------------
def get_random_quote():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM quotes')
    rows = c.fetchall()
    conn.close()
    return random.choice(rows) if rows else None

# ----------------------------
# GET QUOTES BY AUTHOR
# ----------------------------
def get_quotes_by_author(author_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM quotes WHERE author LIKE ?', (f"%{author_name}%",))
    rows = c.fetchall()
    conn.close()
    return rows

# ----------------------------
# GET QUOTES BY ID
# ----------------------------
def get_quote_by_id(quote_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM quotes WHERE id = ?', (quote_id,))
    row = c.fetchone()
    conn.close()
    return row



# ----------------------------
# DISCORD BOT EVENTS & COMMANDS
# ----------------------------
@bot.event
async def on_ready():
    init_db()
    print(f'I Exist! \nYou may call me **{bot.user}**!')

@bot.group(invoke_without_command=True)
async def quote(ctx):
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        quote_id = save_quote(
            str(replied_message.author),
            replied_message.content,
            ctx.channel.name,
            replied_message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ctx.guild.name
        )
        await ctx.reply(f'📌 Saved quote `#{quote_id}` from **{replied_message.author.display_name}**:\n"> {replied_message.content}"')
    else:
        await ctx.reply("❗ You need to reply to a message to quote it.")

@quote.command(name="random")
async def quote_random(ctx):
    q = get_random_quote()
    if q:
        await ctx.reply(f'🎲 Random quote `#{q[0]}` from **{q[1]}** in #{q[3]} on {q[4]}:\n"> {q[2]}"')
    else:
        await ctx.reply("No quotes yet!")

@quote.command(name="list")
async def quote_list(ctx, member: discord.Member):
    quotes = get_quote_by_author(member.name)
    
    if not quotes:
        await ctx.reply(f"No quotes found for {member.display_name}.")
        return
    elif len(quotes) <= 5:
        await ctx.reply(f"you have {len(quotes)} quotes. Here they are:\n" + "\n".join([f'`#{quote[0]}`: "{quote[2]}" in the channel #{quote[3]} and recorded on {quote[4]}' for quote in quotes]))
    elif len(quotes) > 5:
        await ctx.reply(f"You have {len(quotes)} quotes. Here are the first 5:\n" + "\n".join([f'`#{quote[0]}`: "{quote[2]}" in the channel #{quote[3]} and recorded on {quote[4]}' for quote in quotes[:5]]) + f"\n...and {len(quotes) - 5} more.")

@quote.command(name="delete")
async def quote_delete(ctx, quote_id: int):
    if ctx.guild is None or ctx.author.id != ctx.guild.owner_id:
        await ctx.reply("⛔ Only the server owner can delete quotes.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
    row = c.fetchone()

    if row:
        c.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
        conn.commit()
        await ctx.reply(f"🗑️ Quote `#{quote_id}` deleted successfully.")
    else:
        await ctx.reply(f"⚠️ Quote `#{quote_id}` not found.")

    conn.close()

@quote.command(name="quote#")
async def quote_show_by_id(ctx, quote_id: int):
    quote = get_quote_by_id(quote_id)
    
    if quote:
        await ctx.reply(f'Quote `#{quote[0]}` from **{quote[1]}**:\n"> {quote[2]}"')
    else:
        await ctx.reply(f"Quote `#{quote_id}` not found.")
        
@quote.command(name="help")
async def quote_help(ctx):
    help_message = (
        "Here are the commands you can use:\n"
        "`$quote` - Reply to a message to save it as a quote.\n"
        "`$quote random` - Get a random quote.\n"
        "`$quote list @member` - List all quotes from a specific member.\n"
        "`$quote delete <quote_id>` - Delete a quote (only for server owner).\n"
        "`$quote# <quote_id>` - Show a specific quote by its ID.\n"
    )
    await ctx.reply(help_message)

# ----------------------------
# RUN THE BOT
# ----------------------------
# Replace with your bot token in the .env file
if os.getenv("DISCORD_TOKEN") is None:
    print("❌ Please set the DISCORD_TOKEN environment variable")
    exit(1)
bot.run(os.getenv("DISCORD_TOKEN"))
