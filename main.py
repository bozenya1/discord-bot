import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio

# --- KONFIGURACJA ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
MY_USER_ID = 1503055372527599698      # <--- TWOJE ID
CATEGORY_ID = 1503069190083580047    # <--- ID KATEGORII DLA TICKETÓW
# --------------------

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Kup bota (PSC)", style=discord.ButtonStyle.green, custom_id="ticket_button")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(CATEGORY_ID)
        
        # Pobieramy obiekt Twojego konta
        me = guild.get_member(MY_USER_ID)
        if not me:
            try:
                me = await guild.fetch_member(MY_USER_ID)
            except:
                me = None

        # Uprawnienia: nikt nie widzi, tylko Ty i kupujący
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        }
        
        if me:
            overwrites[me] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites,
            topic=f"Zakup bota przez {user.id}"
        )

        await interaction.response.send_message(f"Stworzono ticket: {channel.mention}", ephemeral=True)
        
        # Embed wewnątrz ticketu
        embed = discord.Embed(
            title="Nowe zamówienie!",
            description=f"Witaj {user.mention}! Napisz jakiego bota potrzebujesz.\n\n**Forma płatności:** PSC.\nOczekuj na odpowiedź <@{MY_USER_ID}>.",
            color=discord.Color.blue()
        )
        
        view = discord.ui.View(timeout=None)
        close_button = discord.ui.Button(label="Zamknij Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
        
        async def close_callback(inter: discord.Interaction):
            if inter.user.id == MY_USER_ID:
                await inter.response.send_message("Zamykanie kanału za 5 sekund...")
                await asyncio.sleep(5)
                await inter.channel.delete()
            else:
                await inter.response.send_message("Tylko właściciel może zamknąć ten ticket!", ephemeral=True)
        
        close_button.callback = close_callback
        view.add_item(close_button)

        await channel.send(content=f"<@{MY_USER_ID}> | {user.mention}", embed=embed, view=view)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(TicketView())

bot = MyBot()

@bot.event
async def on_ready():
    print(f'✅ Bot działa! Zalogowano jako: {bot.user.name}')
    print(f'Przejdź na Discorda i wpisz !setup')

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛒 Sklep z Botami",
        description="Kliknij przycisk poniżej, aby otworzyć ticket i kupić bota!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=TicketView())

bot.run(TOKEN)