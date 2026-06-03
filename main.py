import discord
from discord.ext import commands
import aiohttp
import os # Necessário para ler o Token escondido na nuvem
from keep_alive import keep_alive # Importa o servidor web fantasma

# ==========================================
#  CONFIGURAÇÕES INICIAIS E INTENTS
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
#  VARIÁVEIS DO SEU SERVIDOR
# ==========================================

GUILDA_ALBION_ID = "oZercpSURfeSz9_7Mpg1-w"  
ALIANCA_ALBION_ID = "mCKNk3EyQ8qLeNMhozFIZg" 
CANAL_GERADOR_ID = 1510026555286360206 

TAG_GUILDA = "[DH]" 
TAG_ALIANCA = "[ALLY]"

CARGOS = {
    "aliado": 11111111111111111111,  
    "membro": 1508849239222911066,   
    "oficial": 1508848755779047564,  
    "lider" : 1508845743363067955,   
}

# ==========================================
#  EVENTOS DO BOT
# ==========================================

@bot.event
async def on_ready():
    print(f'🔥 Sistema Mestre online! Operando como {bot.user}.')

# ==========================================
#  CRIAR CALL
# ==========================================

@bot.event
async def on_voice_state_update(membro, antes, depois):
    if depois.channel and depois.channel.id == CANAL_GERADOR_ID:
        categoria = depois.channel.category
        
        permissoes = {
            membro.guild.default_role: discord.PermissionOverwrite(
                speak=True, 
                use_voice_activation=True 
            )
        }
        
        nova_sala = await membro.guild.create_voice_channel(
            name=f"🎮 {membro.display_name}", 
            category=categoria,
            overwrites=permissoes
        )
        try:
            await membro.move_to(nova_sala)
        except discord.HTTPException:
            await nova_sala.delete()

    if antes.channel and antes.channel.id != CANAL_GERADOR_ID:
        if len(antes.channel.members) == 0:
            if antes.channel.name.startswith("🎮"):
                await antes.channel.delete()

# ==========================================
#  COMANDOS DE MODERAÇÃO
# ==========================================

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Todos os sistemas operacionais.")

# @bot.command()
# async def mudarnick(ctx, membro: discord.Member, *, novo_nick: str):
#     try:
#         await membro.edit(nick=novo_nick)
#         await ctx.send(f"Feito! O nick de {membro.mention} foi alterado para **{novo_nick}**.")
#     except discord.Forbidden:
#         await ctx.send("Erro de permissão: Meu cargo precisa estar acima do cargo do usuário!")

# @bot.command()
# async def dar_cargo(ctx, membro: discord.Member, nivel: str):
#     nivel = nivel.lower()
    
#     if nivel not in CARGOS:
#         await ctx.send("Nível inválido! Escolha: padrao, membro, lider_mediano, lider_alto.")
#         return

#     cargo_escolhido = ctx.guild.get_role(CARGOS[nivel])
    
#     if cargo_escolhido is None:
#         await ctx.send("Aviso: O ID do cargo não foi encontrado. Atualize o dicionário de CARGOS no código.")
#         return
        
#     try:
#         await membro.add_roles(cargo_escolhido)
#         await ctx.send(f"Sucesso! {membro.mention} recebeu o cargo **{cargo_escolhido.name}**.")
#     except discord.Forbidden:
#         await ctx.send("Erro: Meu cargo está abaixo do cargo que você está tentando dar!")

# ==========================================
# PAINEL VISUAL DE INSTRUÇÕES
# ==========================================

@bot.command(name="painel_registro")
@commands.has_permissions(administrator=True) 
async def painel_registro(ctx):
    await ctx.message.delete()
    
    embed = discord.Embed(
        title="🛡️ PORTAL DE REGISTRO 🛡️",
        description=(
            "Bem-vindo ao nosso servidor!\n\n"
            "Para ter acesso aos canais de voz e texto, você precisa confirmar sua conta do **Albion Online**.\n\n"
            "👉 **Para se registrar, digite aqui no chat o comando:**\n"
            "`!registrar SeuNickDoJogo`\n\n"
            "*Exemplo: `!registrar Zezinho`*"
        ),
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed)

# ==========================================
# COMANDO DE REGISTRO 
# ==========================================

@bot.command(name="registrar")
async def registrar(ctx, *, nick: str = None):
    await ctx.message.delete()
    
    if not nick:
        return await ctx.send(
            f"⚠️ {ctx.author.mention}, você esqueceu de digitar o seu nome do jogo! Use `!registrar SeuNick`.", 
            delete_after=10
        )
        
    msg_aviso = await ctx.send(f"🔍 Buscando **{nick}** nos servidores do Albion, aguarde um momento...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://gameinfo.albiononline.com/api/gameinfo/search?q={nick}") as resp:
                if resp.status != 200:
                    return await msg_aviso.edit(content="❌ Erro ao conectar com o Albion. Tente novamente mais tarde.")
                
                dados = await resp.json()
                jogadores = dados.get('players', [])
                
                jogador_encontrado = next((p for p in jogadores if p['Name'].lower() == nick.lower()), None)
                        
                if not jogador_encontrado:
                    return await msg_aviso.edit(content=f"❌ O jogador **{nick}** não foi encontrado no Albion!")

                guild_id_jogador = jogador_encontrado.get('GuildId')
                alliance_id_jogador = jogador_encontrado.get('AllianceId')
                nome_correto = jogador_encontrado['Name']

                cargo_dar = None
                nova_tag = ""
                mensagem_final = ""

                if guild_id_jogador == GUILDA_ALBION_ID:
                    cargo_dar = ctx.guild.get_role(CARGOS["membro"])
                    nova_tag = f"{TAG_GUILDA} {nome_correto}"
                    mensagem_final = f"✅ **Sucesso!** Bem-vindo à guilda, {ctx.author.mention}!"
                    
                elif ALIANCA_ALBION_ID and alliance_id_jogador == ALIANCA_ALBION_ID:
                    cargo_dar = ctx.guild.get_role(CARGOS["aliado"])
                    nova_tag = f"{TAG_ALIANCA} {nome_correto}"
                    mensagem_final = f"🤝 **Sucesso!** Você foi reconhecido como nosso Aliado, {ctx.author.mention}!"
                    
                else:
                    return await msg_aviso.edit(content=f"❌ Acesso Negado: O jogador **{nome_correto}** não pertence à nossa Guilda ou Aliança.")

                if cargo_dar:
                    try:
                        await ctx.author.add_roles(cargo_dar)
                    except discord.Forbidden:
                        mensagem_final += "\n⚠️ *Aviso: Não consegui te dar o cargo. O meu cargo de Bot precisa estar no topo da lista do servidor!*"
                
                try:
                    await ctx.author.edit(nick=nova_tag[:32])
                except discord.Forbidden:
                    pass 

                await msg_aviso.edit(content=mensagem_final)

    except Exception as e:
        await msg_aviso.edit(content=f"⚠️ Ocorreu um erro interno no bot: {e}")

# ==========================================
# SISTEMA DE VAGAS COM FILA DE ESPERA
# ==========================================

class BotaoDinamico(discord.ui.Button):
    def __init__(self, classe_nome, view_pai):
        super().__init__(label=classe_nome, style=discord.ButtonStyle.secondary)
        self.classe_nome = classe_nome
        self.view_pai = view_pai

    async def callback(self, interaction: discord.Interaction):
        await self.view_pai.processar_clique(interaction, self.classe_nome)

class PainelVagas(discord.ui.View):
    def __init__(self, conteudo, definicao_vagas):
        super().__init__(timeout=None)
        self.conteudo = conteudo
        self.max_vagas = definicao_vagas
        self.jogadores = {classe: [] for classe in definicao_vagas}
        self.fila_espera = {classe: [] for classe in definicao_vagas}

        for classe in definicao_vagas.keys():
            self.add_item(BotaoDinamico(classe, self))
            
        botao_sair = discord.ui.Button(label="Sair da Lista", style=discord.ButtonStyle.danger, emoji="❌")
        botao_sair.callback = self.sair_callback
        self.add_item(botao_sair)

    def gerar_embed(self):
        embed = discord.Embed(
            title="⚔️ EVENTO FORMANDO! ⚔️", 
            description=f"**Conteúdo:** {self.conteudo}",
            color=discord.Color.gold()
        )
        
        for classe, vagas_totais in self.max_vagas.items():
            inscritos = self.jogadores[classe]
            reserva = self.fila_espera[classe]
            
            texto_jogadores = "\n".join(inscritos) if inscritos else "*Vazio*"
            
            if reserva:
                texto_reserva = "\n".join([f"⏳ *{r} (Fila)*" for r in reserva])
                texto_final = f"{texto_jogadores}\n\n**⏱️ Fila de Espera:**\n{texto_reserva}"
            else:
                texto_final = texto_jogadores

            embed.add_field(
                name=f"{classe} ({len(inscritos)}/{vagas_totais})", 
                value=texto_final, 
                inline=True
            )
            
        return embed

    # O "Motor" da Fila Inteligente
    async def promover_da_fila(self, interaction: discord.Interaction, classe: str):
        # Se tem vaga na classe E tem alguém na fila de espera
        if len(self.jogadores[classe]) < self.max_vagas[classe] and len(self.fila_espera[classe]) > 0:
            # .pop(0) tira o primeiro da fila (FIFO)
            proximo_jogador = self.fila_espera[classe].pop(0) 
            self.jogadores[classe].append(proximo_jogador)
            
            # Avisa o jogador promovido no chat geral para ele se preparar
            await interaction.channel.send(
                f"🎉 {proximo_jogador}, uma vaga abriu e você foi puxado da fila para assumir como **{classe}**!"
            )

    async def processar_clique(self, interaction: discord.Interaction, classe: str):
        usuario = interaction.user.mention
        classe_antiga = None
        
        # 1. Remove o usuário e descobre onde ele estava antes
        for c in self.jogadores:
            if usuario in self.jogadores[c]: 
                self.jogadores[c].remove(usuario)
                classe_antiga = c # Guarda a informação da vaga que ele abandonou
            if usuario in self.fila_espera[c]: 
                self.fila_espera[c].remove(usuario)

        # 2. Coloca o usuário na nova classe ou fila
        if len(self.jogadores[classe]) < self.max_vagas[classe]:
            self.jogadores[classe].append(usuario)
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
            
        else:
            if usuario not in self.fila_espera[classe]:
                self.fila_espera[classe].append(usuario)
                await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
                await interaction.followup.send(f"📋 As vagas principais de {classe} estão cheias. Você foi colocado na Fila de Espera!", ephemeral=True)

        # 3. 🆕 Se ele abandonou uma vaga principal, puxa alguém da fila para o lugar dele!
        if classe_antiga and classe_antiga != classe:
            await self.promover_da_fila(interaction, classe_antiga)
            # Atualiza o painel novamente caso alguém tenha subido
            await interaction.message.edit(embed=self.gerar_embed(), view=self)

    async def sair_callback(self, interaction: discord.Interaction):
        usuario = interaction.user.mention
        removido = False
        classe_abandonada = None
        
        for c in self.jogadores:
            if usuario in self.jogadores[c]:
                self.jogadores[c].remove(usuario)
                removido = True
                classe_abandonada = c
            if usuario in self.fila_espera[c]:
                self.fila_espera[c].remove(usuario)
                removido = True
                
        if removido:
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
            
            # 🆕 Se ele saiu e deixou um buraco, preenche com quem está na fila
            if classe_abandonada:
                await self.promover_da_fila(interaction, classe_abandonada)
                await interaction.message.edit(embed=self.gerar_embed(), view=self)
        else:
            await interaction.response.send_message("Você não está inscrito em nenhuma vaga.", ephemeral=True)
@bot.command(name="vaga")
async def vaga(ctx, *, texto: str = None):
    await ctx.message.delete()
    
    if texto is None:
        mensagem_ensino = (
            "📚 **Como usar o sistema de vagas:**\n\n"
            "Você precisa me dizer qual é o conteúdo e quais as classes necessárias, "
            "separando tudo por barras `/` e dois pontos `:`\n\n"
            "**🛠️ O molde é este:**\n"
            "`!vaga Nome do Evento / Classe:Vaga / Classe:Vaga`\n\n"
            "**💡 Exemplos Práticos:**\n"
            "▶️ `!vaga Masmorra Estática T8 / Tank:1 / Healer:1 / DPS:3`\n"
            "▶️ `!vaga Gank na Black Zone / Controle:1 / Scout:1 / DPS:5`\n"
            "▶️ `!vaga ZvZ Defesa / Engaje:3 / Locus:2 / Suporte:3 / DPS:10`"
        )
        return await ctx.send(mensagem_ensino, delete_after=40)
    
    try:
        partes = texto.split('/')
        conteudo = partes[0].strip()
        
        definicao_vagas = {}
        for parte in partes[1:]:
            nome_classe, qtd = parte.split(':')
            definicao_vagas[nome_classe.strip()] = int(qtd.strip())
            
        if not definicao_vagas:
            raise ValueError()
            
    except:
        mensagem_erro = (
            "⚠️ **Formato incorreto!** Verifique se você esqueceu a barra vertical `|` ou os dois pontos `:`\n"
            "*Se tiver dúvidas, digite apenas `!vaga` para ver o tutorial.*"
        )
        return await ctx.send(mensagem_erro, delete_after=20)

    painel = PainelVagas(conteudo, definicao_vagas)
    embed_inicial = painel.gerar_embed()
    
    id_cargo_membro = CARGOS.get("membro")
    mencao_cargo = f"<@&{id_cargo_membro}>" if id_cargo_membro else "@everyone"

    await ctx.send(content=f"📢 {mencao_cargo}", embed=embed_inicial, view=painel)

# ==========================================
#  INICIALIZAÇÃO
# ==========================================

keep_alive() # Liga o servidor fantasma
bot.run(os.getenv('TOKEN_DO_BOT')) # Lê a senha do cofre de forma segura