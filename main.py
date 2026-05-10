import discord
from discord.ext import commands
import os
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

# --- KLASA PRZYCISKU (UI) ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Otwórz zgłoszenie", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        
        # Nazwa kanału
        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        
        # Sprawdzanie czy bilet istnieje
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            # Informacja o istniejącym kanale (ta może zostać ukryta, żeby nie robić spamu)
            return await interaction.response.send_message(f"⚠️ Masz już bilet: {existing_channel.mention}", ephemeral=True)

        # 1. Wysyłamy informację na kanale (widoczną dla wszystkich, ale zaraz zniknie)
        # Musimy użyć followups, bo chcemy mieć obiekt wiadomości do usunięcia
        await interaction.response.defer() # Bot "myśli..."
        msg = await interaction.followup.send(f"⏳ {user.mention}, tworzę Twoje zgłoszenie...", ephemeral=False)
        
        # Usuwamy tę wiadomość po 5 sekundach
        await msg.delete(delay=5)

        # 2. Tworzenie kategorii i kanału
        category = discord.utils.get(guild.categories, name="TICKETY")
        if not category:
            category = await guild.create_category("TICKETY")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        new_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        
        # 3. Wysyłamy "Okienko" (Embed) w nowym kanale
        embed = discord.Embed(
            title="🎫 Zgłoszenie: " + user.name,
            description=(
                f"Witaj {user.mention} w swoim zgłoszeniu!\n\n"
                "**Jak możesz nam pomóc?**\n"
                "1. Opisz dokładnie swój problem.\n"
                "2. Załącz zrzuty ekranu, jeśli je masz.\n"
                "3. Poczekaj cierpliwie na odpowiedź administracji."
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=user.display_avatar.url) # Miniaturka z awatarem użytkownika
        embed.set_footer(text="ID Użytkownika: " + str(user.id))
        
        await new_channel.send(content=f"{user.mention}", embed=embed)
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
    bot.add_view(TicketView())

@bot.command()
async def setup(ctx):
    """Komenda dostępna tylko dla właściciela bota lub osób z licencją"""
    
    # 1. Sprawdzenie licencji serwera
    if int(ctx.guild.id) not in PAID_SERVERS:
        return await ctx.send("❌ Ten serwer nie ma wykupionej licencji.")

    # 2. Sprawdzenie uprawnień (Tylko Ty jako Owner lub Admin serwera może to odpalić)
    if ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Nie masz uprawnień do konfiguracji panelu (musisz być właścicielem bota lub adminem serwera).")

    category = discord.utils.get(ctx.guild.categories, name="TICKETY")
    if not category:
        category = await ctx.guild.create_category("TICKETY")

    channel = discord.utils.get(category.text_channels, name="pomoc-ticket")
    if channel:
        return await ctx.send(f"⚠️ Panel już istnieje: {channel.mention}")

    channel = await ctx.guild.create_text_channel("pomoc-ticket", category=category)

    embed = discord.Embed(
        title="📩 Centrum Pomocy",
        description="Kliknij przycisk poniżej, aby otworzyć bilet.",
        color=discord.Color.blue()
    )
    
    await channel.send(embed=embed, view=TicketView())
    await ctx.send(f"✅ Skonfigurowano system!")

# --- START ---
if __name__ == "__main__":
    bot.run(TOKEN)