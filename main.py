import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Ładowanie ustawień z pliku .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Konfiguracja bota
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user.name} jest gotowy!')

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """Komenda konfigurująca system u klienta"""
    
    # 1. Sprawdzanie lub tworzenie kategorii
    category = discord.utils.get(ctx.guild.categories, name="TICKETY")
    if not category:
        category = await ctx.guild.create_category("TICKETY")

    # 2. Tworzenie kanału pod panel
    channel = discord.utils.get(ctx.guild.text_channels, name="pomoc-ticket")
    if not channel:
        channel = await ctx.guild.create_text_channel("pomoc-ticket", category=category)

    # 3. Prosty komunikat (Tu klient może sobie zmienić tekst)
    embed = discord.Embed(
        title="Centrum Obsługi",
        description="Kliknij przycisk poniżej, aby otworzyć nowe zgłoszenie.",
        color=discord.Color.blue()
    )
    
    await channel.send(embed=embed)
    await ctx.send(f"✅ System gotowy na kanale {channel.mention}")

@bot.command()
async def wylacz(ctx):
    """Komenda wyłączenia - sprawdzająca tylko czy to Ty przez .env"""
    owner_id = int(os.getenv('OWNER_ID', 0))
    if ctx.author.id == owner_id:
        await ctx.send("🔌 Wyłączanie bota...")
        await bot.close()

bot.run(TOKEN)