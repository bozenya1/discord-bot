import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# --- KONFIGURACJA Z .ENV ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Pobieranie listy serwerów z licencją
raw_servers = os.getenv('PAID_SERVERS', '')
PAID_SERVERS = [int(s) for s in raw_servers.split(',') if s.strip()]

# --- KLASA PRZYCISKU (UI) ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Przycisk nie wygasa po restarcie bota

    @discord.ui.button(label="Otwórz zgłoszenie", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Na razie tylko potwierdzenie, że działa
        await interaction.response.send_message(f"Cześć {interaction.user.mention}! Twoje zgłoszenie jest tworzone...", ephemeral=True)

# --- KONFIGURACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'---')
    print(f'✅ Bot online: {bot.user.name}')
    print(f'💳 Aktywne licencje (ID): {PAID_SERVERS}')
    print(f'---')
    # Rejestrujemy widok przycisku, żeby działał po restarcie bota
    bot.add_view(TicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """Komenda konfigurująca system ticketów u klienta"""
    
    # 1. Sprawdzenie licencji (zabezpieczenie przed oszustami)
    if ctx.guild.id not in PAID_SERVERS:
        await ctx.send("❌ **Błąd licencji:** Ten serwer nie posiada aktywnej subskrypcji. Skontaktuj się z autorem bota.")
        return

    # 2. Tworzenie kategorii
    category = discord.utils.get(ctx.guild.categories, name="TICKETY")
    if not category:
        category = await ctx.guild.create_category("TICKETY")

    # 3. Tworzenie kanału pod panel
    channel = discord.utils.get(ctx.guild.text_channels, name="pomoc-ticket")
    if not channel:
        channel = await ctx.guild.create_text_channel("pomoc-ticket", category=category)

    # 4. Tworzenie i wysyłanie Embedu z PRZYCISKIEM
    embed = discord.Embed(
        title="📩 Centrum Pomocy i Ticketów",
        description=(
            "Potrzebujesz pomocy? Masz pytanie do administracji?\n\n"
            "**Kliknij przycisk poniżej**, aby otworzyć nowe zgłoszenie. "
            "Zostanie stworzony prywatny kanał widoczny tylko dla Ciebie i obsługi."
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="System obsługi zgłoszeń v1.0")
    
    await channel.send(embed=embed, view=TicketView())
    await ctx.send(f"✅ Pomyślnie skonfigurowano system na kanale {channel.mention}")

@bot.command()
async def wylacz(ctx):
    """Bezpieczne wyłączenie bota przez właściciela"""
    owner_id = int(os.getenv('OWNER_ID', 0))
    if ctx.author.id == owner_id:
        await ctx.send("🔌 Wyłączanie bota...")
        await bot.close()
    else:
        await ctx.send("❌ Tylko właściciel bota może użyć tej komendy.")

# --- START BOTA ---
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ BŁĄD: Nie znaleziono DISCORD_TOKEN w pliku .env!")