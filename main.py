import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# --- KONFIGURACJA Z .ENV ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bezpieczne wczytywanie listy serwerów
raw_servers = os.getenv('PAID_SERVERS', '')
# Czyścimy dane: usuwamy spacje i dzielimy po przecinku, zamieniając na INTy
PAID_SERVERS = [int(s.strip()) for s in raw_servers.split(',') if s.strip().isdigit()]
OWNER_ID = int(os.getenv('OWNER_ID', '0'))

# --- KLASY UI ---
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij zgłoszenie", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Sprawdzamy czy to Admin
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Tylko administracja zamyka tickety!", ephemeral=True)
        
        await interaction.response.send_message("🔒 Zamykanie za 5 sekund...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Otwórz zgłoszenie", style=discord.ButtonStyle.primary, emoji="📩", custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            return await interaction.response.send_message(f"⚠️ Masz już bilet: {existing_channel.mention}", ephemeral=True)

        await interaction.response.defer()
        new_channel = await guild.create_text_channel(
            channel_name, 
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )
        
        embed = discord.Embed(title="🎫 Zgłoszenie", description=f"Witaj {user.mention}!", color=discord.Color.green())
        await new_channel.send(embed=embed, view=TicketCloseView())

# --- KONFIGURACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot gotowy | Licencje dla: {PAID_SERVERS}')
    bot.add_view(TicketView())
    bot.add_view(TicketCloseView())

@bot.command()
async def setup(ctx):
    # --- RIGORISTYCZNY CHECK LICENCJI ---
    server_id = int(ctx.guild.id)
    
    if server_id not in PAID_SERVERS:
        print(f"⚠️ PRÓBA UŻYCIA BEZ LICENCJI: {ctx.guild.name} ({server_id})")
        return await ctx.send(f"❌ Ten serwer (ID: {server_id}) nie posiada licencji.")

    # Reszta kodu (tylko dla opłaconych)
    if not ctx.author.guild_permissions.administrator and ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Brak uprawnień.")

    category = discord.utils.get(ctx.guild.categories, name="TICKETY") or await ctx.guild.create_category("TICKETY")
    channel = await ctx.guild.create_text_channel("pomoc-ticket", category=category)
    
    embed = discord.Embed(title="📩 Panel Pomocy", description="Kliknij przycisk poniżej.", color=discord.Color.blue())
    await channel.send(embed=embed, view=TicketView())
    await ctx.send("✅ Skonfigurowano!")

if __name__ == "__main__":
    bot.run(TOKEN)