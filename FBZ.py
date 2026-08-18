import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# Carga las variables de entorno
load_dotenv()

# ... (Todo el resto de tu código queda exactamente igual) ...
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# --- VARIABLES A CONFIGURAR ---
CANAL_INTRODUCCION_ID = 1513979582636884078 
CANAL_ROLES_ID = 1533923979683827802

CATEGORIA_TICKETS_ID = 1533849701823283210  # Reemplaza por el ID de la categoría de los tickets
ROLES_STAFF_IDS = [
    1513682190351728743,  # Lider
    1524828451234906264   # ID de SubLider (Ejemplo)
]

ROL_CAMIONERO_ID = 1531399187034411098
ROL_CLIENTE_ID = 1513951912398164230
ROL_MECANICO_ID = 1525602230194147379
ROL_SEGURIDAD_ID = 1517320699482734732

# --- CLASE DEL MENÚ INTERACTIVO (TRABAJOS LEGALES) ---
class MenuRoles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # Fila 0: Camionero
    @discord.ui.button(label="Camionero (Vice Coast)", emoji="\U0001f69a", style=discord.ButtonStyle.secondary, custom_id="btn_cam", row=0)
    async def btn_camionero(self, interaction: discord.Interaction, button: discord.ui.Button):
        rol = interaction.guild.get_role(ROL_CAMIONERO_ID)
        await interaction.user.add_roles(rol)
        await interaction.response.send_message("\U0001f69a ¡Se te ha asignado el rol de Camionero!", ephemeral=True)

    # Fila 1: Concesionaria 
    @discord.ui.button(label="Vice Coast Motor's (Concesionaria)", emoji="\U0001f697", style=discord.ButtonStyle.success, custom_id="btn_tax", row=1)
    async def btn_concesionaria(self, interaction: discord.Interaction, button: discord.ui.Button):
        rol = interaction.guild.get_role(ROL_CLIENTE_ID)
        await interaction.user.add_roles(rol)
        await interaction.response.send_message("\U0001f697 ¡Se te ha asignado el rol de Cliente!", ephemeral=True)

    # Fila 2: Mecánico 
    @discord.ui.button(label="Mecánico (Vice Coast)", emoji="\U0001f527", style=discord.ButtonStyle.secondary, custom_id="btn_mec", row=2)
    async def btn_mecanico(self, interaction: discord.Interaction, button: discord.ui.Button):
        rol = interaction.guild.get_role(ROL_MECANICO_ID)
        await interaction.user.add_roles(rol)
        await interaction.response.send_message("\U0001f527 ¡Se te ha asignado el rol de Mecánico!", ephemeral=True)

    # Fila 3: Seguridad 
    @discord.ui.button(label="Seguridad (Génesis Club)", emoji="\u2694\ufe0f", style=discord.ButtonStyle.primary, custom_id="btn_seg", row=3)
    async def btn_seguridad(self, interaction: discord.Interaction, button: discord.ui.Button):
        rol = interaction.guild.get_role(ROL_SEGURIDAD_ID)
        await interaction.user.add_roles(rol)
        await interaction.response.send_message("\u2694\ufe0f ¡Se te ha asignado el rol de Seguridad!", ephemeral=True)


# --- EVENTOS Y COMANDOS ---
@bot.event
async def on_ready():
    print(f'? Bot conectado exitosamente como {bot.user}')

@bot.event
async def on_member_join(member):
    canal_intro = bot.get_channel(CANAL_INTRODUCCION_ID)
    if canal_intro:
        mensaje = (f"¡Bienvenido/a {member.mention} al discord oficial del entorno **Florida Boyz**!\n\n"
                   f"**1.** Por favor, escribe en este canal el `Nombre_Apellido` de tu personaje dentro del juego para actualizar tu apodo.\n"
                   f"**2.** Una vez que lo hagas, dirígete al canal <#{CANAL_ROLES_ID}> para seleccionar a qué rubro vas a pertenecer.")
        await canal_intro.send(mensaje)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == CANAL_INTRODUCCION_ID:
        nuevo_nombre = message.content.strip()
        try:
            await message.author.edit(nick=nuevo_nombre)
            # Usamos el código Unicode para el check verde
            await message.add_reaction("\u2705")
        except discord.Forbidden:
            print(f"Faltan permisos para cambiar el apodo de {message.author.name}.")
            # Usamos el código Unicode para la cruz roja
            await message.add_reaction("\u274C")

    await bot.process_commands(message)

# Comando para generar el menú con estilo Miami Vice
@bot.command()
async def enviar_menu(ctx):
    view = MenuRoles()
    
    # Creamos un Embed con color Rosa Neón (código hex: 0xFF007F)
    embed_miami = discord.Embed(
        title="\U0001f334 Selección de Rubro - Trabajos Legales",
        description="Por favor, selecciona a qué empresa perteneces dentro de la facción haciendo clic en el botón correspondiente.",
        color=0xFF007F 
    )
    
    await ctx.send(embed=embed_miami, view=view)


# --- FUNCIÓN GLOBAL PARA CREAR TICKETS ---
async def crear_ticket_canal(interaction: discord.Interaction, tipo: str, modal: discord.ui.Modal):
    # Extraemos el nombre del personaje (siempre es el primer campo en todos los modales)
    nombre_ic_crudo = modal.children[0].value
    nombre_ic_formateado = nombre_ic_crudo.replace(" ", "-").replace("_", "-").lower()

    guild = interaction.guild
    categoria = discord.utils.get(guild.categories, id=CATEGORIA_TICKETS_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

    menciones_staff = []
    for rol_id in ROLES_STAFF_IDS:
        rol = guild.get_role(rol_id)
        if rol:
            overwrites[rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            menciones_staff.append(rol.mention)

    nombre_canal = f"tkt-{tipo}-{nombre_ic_formateado}"
    canal = await guild.create_text_channel(name=nombre_canal, category=categoria, overwrites=overwrites)
    
    embed = discord.Embed(title=f"\U0001f4cb Nuevo Ticket - Opción {tipo}", color=0x8B0000)
    
    # Adaptamos la lectura para soportar texto y menús desplegables
    # Preparamos el Embed con todas las respuestas
    embed = discord.Embed(title=f"\U0001f4cb Nuevo Ticket - Opción {tipo}", color=0x8B0000)
    for item in modal.children:
        # Si un campo opcional está vacío, le ponemos "No aplica" para que no quede en blanco
        valor = item.value if item.value else "No aplica / No especificado."
        embed.add_field(name=item.label, value=valor, inline=False)
        
    texto_menciones_staff = " ".join(menciones_staff)
    await canal.send(content=f"{interaction.user.mention} | {texto_menciones_staff}", embed=embed)
    await interaction.response.send_message(f"\u2705 Formulario enviado. Tu ticket ha sido creado: {canal.mention}", ephemeral=True)


# --- MODALES (LOS FORMULARIOS EMERGENTES) ---

class ModalOpcionA(discord.ui.Modal, title='Contacto con Dueño de Negocio'):
    nombre_ic = discord.ui.TextInput(label='Nombre y Apellido IC', style=discord.TextStyle.short)
    
    # Lo convertimos a texto, pero le damos las opciones como ejemplo
    negocio = discord.ui.TextInput(
        label='¿Con qué negocio quieres hablar?', 
        style=discord.TextStyle.short, 
        placeholder="Camionero, Cliente, Mecánico o Seguridad"
    )
    
    razon = discord.ui.TextInput(label='Razón del contacto', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await crear_ticket_canal(interaction, "A", self)

class ModalOpcionB(discord.ui.Modal, title='Ingreso a la Facción'):
    nombre_ic = discord.ui.TextInput(label='Nombre y Apellido IC', style=discord.TextStyle.short)
    llegada = discord.ui.TextInput(label='¿Cómo llegaste hasta Florida Boyz?', style=discord.TextStyle.paragraph)
    motivo = discord.ui.TextInput(label='¿Por qué quieres abandonar la legalidad?', style=discord.TextStyle.paragraph)
    meta = discord.ui.TextInput(label='¿Cuál sería tu máxima meta dentro del rol ilegal?', style=discord.TextStyle.paragraph, placeholder="Ej: Llegar a ser el asesino a sueldo profesional de la facción.")
    horarios = discord.ui.TextInput(label='¿Qué horarios de conexión manejas?', style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await crear_ticket_canal(interaction, "B", self)

class ModalOpcionC(discord.ui.Modal, title='Rolear con la Facción'):
    nombre_ic = discord.ui.TextInput(label='Nombre y Apellido IC', style=discord.TextStyle.short)
    es_miembro = discord.ui.TextInput(label='¿Eres parte de FBZ? (Responde Si o No)', style=discord.TextStyle.short, max_length=2)
    # required=False hace que no sea obligatorio llenarlo para enviar el formulario
    idea_rol = discord.ui.TextInput(label='(Si eres FBZ) Idea de rol a plantear', style=discord.TextStyle.paragraph, required=False)
    razon_acercamiento = discord.ui.TextInput(label='(Si NO eres) Razón del acercamiento', style=discord.TextStyle.paragraph, required=False)
    miembro_inv = discord.ui.TextInput(label='(Si NO eres) Miembro a involucrar', style=discord.TextStyle.short, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await crear_ticket_canal(interaction, "C", self)


# --- MENÚ DE TICKETS (BOTONES) ---
class MenuTicketsIlegal(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="A. Contactar Dueño de Negocio", style=discord.ButtonStyle.secondary, custom_id="btn_tkt_a")
    async def btn_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalOpcionA())

    @discord.ui.button(label="B. Ingresar a la Facción", style=discord.ButtonStyle.danger, custom_id="btn_tkt_b")
    async def btn_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalOpcionB())

    @discord.ui.button(label="C. Rolear con la Facción", style=discord.ButtonStyle.primary, custom_id="btn_tkt_c")
    async def btn_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalOpcionC())


# --- COMANDO PARA ENVIAR EL MENÚ ---
@bot.command()
async def enviar_tickets(ctx):
    view = MenuTicketsIlegal()
    
    embed_ilegal = discord.Embed(
        title="\u2620\ufe0f Florida Boyz - Departamento de Admisiones",
        description=(
            "¿Qué te gustaría hacer dentro de Florida Boyz?\n\n"
            "¿Alguna vez pensaste en pasarte al mundo ilícito y pertenecer a la facción? "
            "Puedes comunicarte con nosotros seleccionando alguna de estas opciones y a la brevedad obtendrás una respuesta:\n\n"
            "**A.** Hablar con un dueño de negocio.\n"
            "**B.** Me interesa entrar en la facción ilegal.\n"
            "**C.** Me interesa rolear con la facción."
        ),
        color=0x8B0000 
    )
    
    await ctx.send(embed=embed_ilegal, view=view)

bot.run(os.getenv('DISCORD_TOKEN'))