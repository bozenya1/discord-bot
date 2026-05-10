import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# --- KONFIGURACJA Z .ENV ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Pobieranie danych z .env
raw_servers = os.getenv('PAID_SERVERS', '')
raw_owner = os.getenv('OWNER_ID', '0')

try:
    PAID_SERVERS = [int(s.strip().replace('"', '').replace("'", "")) for s in raw_servers.split(',') if s.strip()]
    OWNER_ID = int(raw_owner.strip().replace('"', '').replace("'", ""))
except ValueError:
    print("❌ BŁĄD: Format PAID_SERVERS lub OWNER_ID w .env jest niepoprawny!")
    PAID_SERVERS = []
    OWNER_ID = 0

# --- KLASA PRZYCISKU ZAMYKANIA (Wewnątrz Ticketa) ---
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Przycisk trwały

    @discord.ui.button(label="Zamknij zgłoszenie", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Potwierdzenie zamknięcia
        await interaction.response.send_message("🔒 Zgłoszenie zostanie usunięte za 5 sekund...")
        
        # Odliczanie 5 sekund i usunięcie kanału
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- KLASA PRZYCISKU OTWIERANIA (Główny Panel) ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Przycisk trwały

    @discord.ui.button(label="Otwórz zgłoszenie", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        
        # Nazwa kanału (zamiana spacji na myślniki)
        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        
        # Sprawdzanie czy bilet już istnieje
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            return await interaction.response.send_message(f"⚠️ Masz już bilet: {existing_channel.mention}", ephemeral=True)

        # 1. Informacja o tworzeniu (zniknie po 5 sekundach)
        await interaction.response.defer() 
        msg = await interaction.followup.send(f"⏳ {user.mention}, tworzę Twoje zgłoszenie...", ephemeral=False)
        await msg.delete(delay=5)

        # 2. Kategorie
        category = discord.utils.get(guild.categories, name="TICKETY")
        if not category:
            category = await guild.create_category("TICKETY")

        # 3. Uprawnienia (widzi tylko autor i bot)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # 4. Tworzenie kanału
        new_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        
        # 5. Okienko powitalne w nowym kanale z przyciskiem ZAMKNIJ
        embed = discord.Embed(
            title="🎫 Zgłoszenie: " + user.name,
            description=(
                f"Witaj {user.mention}!\n\n"
                "Opisz swój problem poniżej. Możesz załączyć zdjęcia.\n"
                "Gdy sprawa zostanie rozwiązana, użyj przycisku poniżej."
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        
        await new_channel.send(content=f"{user.mention}", embed=embed, view=TicketCloseView())

# --- KONFIGURACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'---')
    print(f'✅ Bot online: {bot.user.name}')
    print(f'💳 Licencje: {PAID_SERVERS}')
    print(f'👑 Właściciel: {OWNER_ID}')
    print(f'---')
    
    # Rejestracja widoków, aby przyciski działały po restarcie
    bot.add_view(TicketView())
    bot.add_view(TicketCloseView())

@bot.command()
async def setup(ctx):
    """Komenda konfigurująca panel"""
    
    # Sprawdzenie licencji
    if int(ctx.guild.id) not in PAID_SERVERS:
        return await ctx.send("❌ Ten serwer nie posiada aktywnej licencji.")

    # Sprawdzenie uprawnień
    if ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Brak uprawnień do użycia tej komendy.")

    category = discord.utils.get(ctx.guild.categories, name="TICKETY")
    if not category:
        category = await ctx.guild.create_category("TICKETY")

    channel = discord.utils.get(category.text_channels, name="pomoc-ticket")
    if channel:
        return await ctx.send(f"⚠️ Panel już istnieje na kanale {channel.mention}")

    channel = await ctx.guild.create_text_channel("pomoc-ticket", category=category)

    embed = discord.Embed(
        title="📩 Centrum Pomocy",
        description="Kliknij przycisk poniżej, aby otworzyć nowe zgłoszenie.",
        color=discord.Color.blue()
    )
    
    await channel.send(embed=embed, view=TicketView())
    await ctx.send(f"✅ System ticketów został poprawnie skonfigurowany!")

@bot.command()
async def wylacz(ctx):
    """Wyłączanie bota"""
    if ctx.author.id == OWNER_ID:
        await ctx.send("🔌 Wyłączanie...")
        await bot.close()
    else:
        await ctx.send("❌ Tylko właściciel może to zrobić.")

# --- START ---
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ BŁĄD: Brak DISCORD_TOKEN w pliku .env!")