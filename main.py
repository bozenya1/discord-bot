import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# --- KONFIGURACJA Z .ENV ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Pobieranie i pancerne przetwarzanie listy serwerów
raw_servers = os.getenv('PAID_SERVERS', '')

try:
    # Czyścimy ID ze spacji, cudzysłowów i zamieniamy na liczby (int)
    PAID_SERVERS = [int(s.strip().replace('"', '').replace("'", "")) for s in raw_servers.split(',') if s.strip()]
except ValueError:
    print("❌ BŁĄD: Jeden z ID w PAID_SERVERS w pliku .env nie jest poprawną liczbą!")
    PAID_SERVERS = []

# --- KLASA PRZYCISKU (UI) ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Przycisk nie wygasa po restarcie bota

    @discord.ui.button(label="Otwórz zgłoszenie", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Na razie tylko potwierdzenie działającego przycisku
        await interaction.response.send_message(f"Cześć {interaction.user.mention}! Twoje zgłoszenie jest tworzone...", ephemeral=True)

# --- KONFIGURACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'---')
    print(f'✅ Bot online: {bot.user.name}')
    print(f'💳 Wczytane licencje z .env: {PAID_SERVERS}')
    print(f'---')
    # Rejestrujemy widok przycisku, żeby działał po restarcie bota
    bot.add_view(TicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """Komenda konfigurująca system ticketów u klienta"""
    
    # DEBUG: Wyświetla w terminalu ID serwera, na którym wpisano komendę
    print(f"DEBUG: Próba użycia !setup na serwerze ID: {ctx.guild.id}")
    
    # 1. Sprawdzenie licencji (wymuszamy int dla pewności)
    if int(ctx.guild.id) not in PAID_SERVERS:
        await ctx.send(f"❌ **Brak licencji!**\nTwoje ID serwera (`{ctx.guild.id}`) nie znajduje się na liście opłaconych.")
        return

    # 2. Zarządzanie kategorią
    category = discord.utils.get(ctx.guild.categories, name="TICKETY")
    if not category:
        category = await ctx.guild.create_category("TICKETY")

    # 3. Zarządzanie kanałem - ZABEZPIECZENIE PRZED DUBLOWANIEM
    # Szukamy kanału o tej nazwie W KONKRETNEJ kategorii
    channel = discord.utils.get(category.text_channels, name="pomoc-ticket")
    
    if channel:
        await ctx.send(f"⚠️ System jest już skonfigurowany na kanale {channel.mention}. Jeśli chcesz go zresetować, usuń ten kanał i wpisz komendę ponownie.")
        return

    # 4. Tworzenie kanału (tylko jeśli nie istnieje)
    channel = await ctx.guild.create_text_channel("pomoc-ticket", category=category)

    # 5. Tworzenie i wysyłanie Embedu z PRZYCISKIEM
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
    raw_owner = os.getenv('OWNER_ID', '0')
    owner_id = int(raw_owner.strip().replace('"', '').replace("'", ""))
    
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