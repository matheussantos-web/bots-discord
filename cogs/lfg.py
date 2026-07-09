import discord
import re
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# Importa os cargos do seu arquivo de configuração
from config import CARGOS

FUSO = timezone(timedelta(hours=-4))

DIAS_SEMANA = {
    "seg": 0, "ter": 1, "qua": 2, "qui": 3,
    "sex": 4, "sab": 5, "dom": 6,
}

# ==========================================
# PARSER DE DATA/HORÁRIO FLEXÍVEL
# ==========================================

def interpretar_horario(texto: str):
    """
    Retorna o unix_timestamp de um texto de horário, ou None se não for reconhecido.

    Formatos aceitos:
      "20:30"            -> hoje às 20:30 (ou amanhã se já passou)
      "hoje 20:30"        -> hoje às 20:30
      "amanha 20:30"      -> amanhã às 20:30
      "sex 20:30"         -> próxima sexta-feira às 20:30
      "25-12 20:30"       -> dia 25/12 às 20:30
    """
    t = texto.strip().lower()
    agora = datetime.now(FUSO)

    m = re.fullmatch(r"(\d{1,2}):(\d{2})", t)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            data_evento = agora.replace(hour=h, minute=mi, second=0, microsecond=0)
            if data_evento < agora:
                data_evento += timedelta(days=1)
            return int(data_evento.timestamp())
        return None

    m = re.fullmatch(r"(hoje|amanha|amanhã)\s+(\d{1,2}):(\d{2})", t)
    if m:
        dia, h, mi = m.group(1), int(m.group(2)), int(m.group(3))
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            return None
        data_evento = agora.replace(hour=h, minute=mi, second=0, microsecond=0)
        if dia in ("amanha", "amanhã"):
            data_evento += timedelta(days=1)
        return int(data_evento.timestamp())

    m = re.fullmatch(r"(seg|ter|qua|qui|sex|sab|dom)\s+(\d{1,2}):(\d{2})", t)
    if m:
        dia_abrev, h, mi = m.group(1), int(m.group(2)), int(m.group(3))
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            return None
        alvo_weekday = DIAS_SEMANA[dia_abrev]
        dias_ate_alvo = (alvo_weekday - agora.weekday()) % 7
        data_evento = agora.replace(hour=h, minute=mi, second=0, microsecond=0)
        data_evento += timedelta(days=dias_ate_alvo)
        if data_evento < agora:
            data_evento += timedelta(days=7)
        return int(data_evento.timestamp())

    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})", t)
    if m:
        dia, mes, h, mi = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        try:
            data_evento = agora.replace(month=mes, day=dia, hour=h, minute=mi, second=0, microsecond=0)
        except ValueError:
            return None
        if data_evento < agora:
            try:
                data_evento = data_evento.replace(year=data_evento.year + 1)
            except ValueError:
                return None
        return int(data_evento.timestamp())

    return None


def eh_texto_de_horario(texto: str) -> bool:
    t = texto.strip().lower()
    padroes = [
        r"^\d{1,2}:\d{2}$",
        r"^(hoje|amanha|amanhã)\s+\d{1,2}:\d{2}$",
        r"^(seg|ter|qua|qui|sex|sab|dom)\s+\d{1,2}:\d{2}$",
        r"^\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}$",
    ]
    return any(re.fullmatch(p, t) for p in padroes)


# ==========================================
# CLASSES DE INTERFACE (BOTÕES E PAINÉIS)
# ==========================================

class BotaoDinamico(discord.ui.Button):
    def __init__(self, classe_nome, view_pai):
        super().__init__(label=classe_nome, style=discord.ButtonStyle.secondary)
        self.classe_nome = classe_nome
        self.view_pai = view_pai

    async def callback(self, interaction: discord.Interaction):
        await self.view_pai.processar_clique(interaction, self.classe_nome)


class ModalPuxarMembro(discord.ui.Modal, title="👑 Puxar Membro para a PT"):
    jogador = discord.ui.TextInput(
        label="Nome, @Nick ou ID numérico",
        style=discord.TextStyle.short,
        placeholder="Ex: @[DH] Zezinho",
        required=True
    )
    classe = discord.ui.TextInput(
        label="Nome da Vaga (Exatamente como no painel)",
        style=discord.TextStyle.short,
        placeholder="Ex: Tank, Suporte, DPS",
        required=True
    )

    def __init__(self, view_pai):
        super().__init__()
        self.view_pai = view_pai

    async def on_submit(self, interaction: discord.Interaction):
        usuario_input = self.jogador.value.strip()
        classe_escolhida = self.classe.value.strip()

        if classe_escolhida not in self.view_pai.max_vagas:
            return await interaction.response.send_message(f"❌ A classe `{classe_escolhida}` não existe.", ephemeral=True)

        usuario_final = None

        if usuario_input.startswith("<@") and usuario_input.endswith(">"):
            usuario_final = usuario_input
        elif usuario_input.isdigit():
            usuario_final = f"<@{usuario_input}>"
        else:
            nome_busca = usuario_input.lstrip('@').strip().lower()
            for membro in interaction.guild.members:
                if membro.display_name.lower() == nome_busca or membro.name.lower() == nome_busca:
                    usuario_final = membro.mention
                    break

            if not usuario_final:
                return await interaction.response.send_message(
                    f"❌ Não encontrei ninguém com o nome `{usuario_input}` no servidor.\n"
                    "*Dica: Digite exatamente igual ao apelido do Discord ou cole o ID numérico.*",
                    ephemeral=True
                )

        await self.view_pai.forcar_insercao(interaction, usuario_final, classe_escolhida)


class PainelVagas(discord.ui.View):
    def __init__(self, conteudo, definicao_vagas, autor_id, unix_timestamp=None, descricao=None):
        super().__init__(timeout=None)
        self.conteudo = conteudo
        self.max_vagas = definicao_vagas
        self.autor_id = autor_id
        self.unix_timestamp = unix_timestamp
        self.descricao = descricao
        self.jogadores = {classe: [] for classe in definicao_vagas}
        self.fila_espera = {classe: [] for classe in definicao_vagas}
        self.encerrado = False  # Controla se a PT foi finalizada

        # Adiciona os botões das classes
        for classe in definicao_vagas.keys():
            self.add_item(BotaoDinamico(classe, self))

        # Botão para Sair da Lista
        botao_sair = discord.ui.Button(label="Sair da Lista", style=discord.ButtonStyle.danger, emoji="❌")
        botao_sair.callback = self.sair_callback
        self.add_item(botao_sair)

        # NOVO: Botão de Encerrar Conteúdo (Call Out)
        botao_encerrar = discord.ui.Button(label="Encerrar PT", style=discord.ButtonStyle.secondary, emoji="🛑")
        botao_encerrar.callback = self.encerrar_callback
        self.add_item(botao_encerrar)

    def gerar_embed(self):
        titulo_destaque = f"💥 {self.conteudo.upper()} 💥"

        # Altera o status visual se estiver encerrado
        if self.encerrado:
            status_texto = "🔴 Conteúdo Encerrado / Call Out"
            cor_embed = discord.Color.dark_gray()
        else:
            status_texto = "🟢 Formando Grupo"
            if self.unix_timestamp:
                status_texto += f" | ⏱️ **Começa:** <t:{self.unix_timestamp}:R> (<t:{self.unix_timestamp}:f>)"
            cor_embed = discord.Color.brand_red()

        desc_embed = f"**Líder da PT:** <@{self.autor_id}>\n**Status:** {status_texto}\n"
        if self.descricao:
            desc_embed += f"{self.descricao}\n"
        desc_embed += "━━━━━━━━━━━━━━━━━━━━━━\n"

        embed = discord.Embed(
            title=titulo_destaque,
            description=desc_embed,
            color=cor_embed
        )

        for classe, vagas_totais in self.max_vagas.items():
            inscritos = self.jogadores[classe]
            reserva = self.fila_espera[classe]
            texto_jogadores = "\n".join(inscritos) if inscritos else "*Vazio*"

            if reserva:
                texto_reserva = "\n".join([f"⏳ *{r} (Fila)*" for r in reserva])
                texto_final = f"{texto_jogadores}\n\n**⏱️ Fila:**\n{texto_reserva}"
            else:
                texto_final = texto_jogadores

            embed.add_field(name=f"🛡️ {classe} ({len(inscritos)}/{vagas_totais})", value=texto_final, inline=True)

        if self.encerrado:
            embed.set_footer(text="Esta PT foi encerrada pelo líder e não aceita mais inscrições.")
        else:
            embed.set_footer(text="Clique nos botões abaixo para entrar ou sair da fila.")
        
        return embed

    async def promover_da_fila(self, interaction: discord.Interaction, classe: str):
        if len(self.jogadores[classe]) < self.max_vagas[classe] and len(self.fila_espera[classe]) > 0:
            proximo_jogador = self.fila_espera[classe].pop(0)
            self.jogadores[classe].append(proximo_jogador)
            await interaction.channel.send(f"🎉 {proximo_jogador}, uma vaga abriu e você assumiu como **{classe}**!")

    async def processar_clique(self, interaction: discord.Interaction, classe: str):
        if self.encerrado:
            return await interaction.response.send_message("❌ Esta PT já foi encerrada.", ephemeral=True)

        usuario = interaction.user.mention
        classe_antiga = None

        for c in self.jogadores:
            if usuario in self.jogadores[c]:
                self.jogadores[c].remove(usuario)
                classe_antiga = c
            if usuario in self.fila_espera[c]:
                self.fila_espera[c].remove(usuario)

        if len(self.jogadores[classe]) < self.max_vagas[classe]:
            self.jogadores[classe].append(usuario)
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
        else:
            if usuario not in self.fila_espera[classe]:
                self.fila_espera[classe].append(usuario)
                await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
                await interaction.followup.send(f"📋 Fila de Espera para {classe}!", ephemeral=True)

        if classe_antiga and classe_antiga != classe:
            await self.promover_da_fila(interaction, classe_antiga)
            await interaction.message.edit(embed=self.gerar_embed(), view=self)

    async def sair_callback(self, interaction: discord.Interaction):
        if self.encerrado:
            return await interaction.response.send_message("❌ Esta PT já foi encerrada.", ephemeral=True)

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
            if classe_abandonada:
                await self.promover_da_fila(interaction, classe_abandonada)
                await interaction.message.edit(embed=self.gerar_embed(), view=self)
        else:
            await interaction.response.send_message("Você não está inscrito em nenhuma vaga.", ephemeral=True)

    # NOVO: Callback para encerrar a PT
    async def encerrar_callback(self, interaction: discord.Interaction):
        # Permite apenas que o Criador da PT ou um Administrador encerre o conteúdo
        if interaction.user.id != self.autor_id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Acesso Negado: Apenas o líder da PT ou a Staff pode fazer o call out!", ephemeral=True)

        self.encerrer_painel()
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
        await interaction.followup.send(f"🛑 **{interaction.user.display_name}** deu Call Out e encerrou o conteúdo: **{self.conteudo}**!")

    # Desativa todos os botões da interface visualmente
    def encerrer_painel(self):
        self.encerrado = True
        for item in self.children:
            item.disabled = True


# ==========================================
# MODAL DE CRIAÇÃO (/content)
# ==========================================

class ModalCriarConteudo(discord.ui.Modal, title="🎮 Criar Conteúdo"):
    titulo = discord.ui.TextInput(
        label="Título do Conteúdo",
        style=discord.TextStyle.short,
        placeholder="Ex: Gank na Red",
        max_length=100,
        required=True,
    )
    # 🟢 Nova caixinha de texto (Opcional)
    descricao_texto = discord.ui.TextInput(
        label="Descrição do Conteúdo (Opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="Ex: requisito t8 ou equivalente, foco em pve nao vamos lutar.",
        max_length=500,
        required=False,
    )
    vagas_texto = discord.ui.TextInput(
        label="Vagas (uma por linha: Classe:Qtd)",
        style=discord.TextStyle.paragraph,
        placeholder="Tank:1\nSuporte:2\nDPS:5",
        required=True,
    )
    horario_texto = discord.ui.TextInput(
        label="Horário (opcional)",
        style=discord.TextStyle.short,
        placeholder="20:30 | amanha 20:30 | sex 20:30",
        required=False,
    )

    def __init__(self, cog: "LFG"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        conteudo = self.titulo.value.strip()
        descricao = self.descricao_texto.value.strip() or None  # 🟢 Pega o valor se existir

        # Parseia as vagas
        definicao_vagas = {}
        for linha in self.vagas_texto.value.splitlines():
            linha_limpa = linha.strip().rstrip(',').strip()
            if not linha_limpa:
                continue
            if ":" not in linha_limpa:
                return await interaction.response.send_message(
                    f"❌ Formato inválido em `{linha_limpa}`. Use `Classe:Qtd`, ex: `Tank:2`.",
                    ephemeral=True
                )
            nome_classe, qtd = linha_limpa.split(":", 1)
            qtd = qtd.strip()
            if not qtd.isdigit():
                return await interaction.response.send_message(
                    f"❌ Quantidade inválida em `{linha_limpa}`. Use um número, ex: `Tank:2`.",
                    ephemeral=True
                )
            definicao_vagas[nome_classe.strip()] = int(qtd)

        if not definicao_vagas:
            return await interaction.response.send_message(
                "❌ Você precisa adicionar pelo menos uma vaga (ex: `Tank:2`).", ephemeral=True
            )

        # Parseia o horário
        unix_timestamp = None
        horario_input = self.horario_texto.value.strip()
        if horario_input:
            if not eh_texto_de_horario(horario_input):
                return await interaction.response.send_message(
                    "❌ Horário em formato inválido. Use `20:30`, `amanha 20:30`, `sex 20:30` ou `25-12 20:30`.",
                    ephemeral=True
                )
            unix_timestamp = interpretar_horario(horario_input)

        # 🟢 Passa a descrição para o PainelVagas
        painel = PainelVagas(conteudo, definicao_vagas, interaction.user.id, unix_timestamp, descricao)
        embed_inicial = painel.gerar_embed()

        id_cargo_membro = CARGOS.get("DIE HARD")
        mencao_cargo = f"<@&{id_cargo_membro}>" if id_cargo_membro else "@everyone"

        await interaction.response.send_message(content=f"📢 {mencao_cargo}", embed=embed_inicial, view=painel)
        mensagem_painel = await interaction.original_response()

        # Registra no cache pro comando !agenda / /agenda
        self.cog.eventos_ativos.append({
            "conteudo": conteudo,
            "autor_id": interaction.user.id,
            "unix_timestamp": unix_timestamp,
            "jump_url": mensagem_painel.jump_url,
        })


# ==========================================
# CLASSE COG (COMANDOS)
# ==========================================

class LFG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Registro em memória das PTs criadas, para o comando !agenda.
        # OBS: zera quando o bot reinicia — persistência em disco é o próximo passo.
        self.eventos_ativos = []

    @app_commands.command(name="content", description="Criar um painel de vagas para organizar conteúdo em grupo")
    async def content(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalCriarConteudo(self))

    @commands.command(name="agenda")
    async def agenda(self, ctx):
        agora_ts = int(datetime.now(FUSO).timestamp())

        self.eventos_ativos = [
            e for e in self.eventos_ativos
            if e["unix_timestamp"] is None or e["unix_timestamp"] > agora_ts - 3600
        ]

        if not self.eventos_ativos:
            return await ctx.send("📭 Nenhum Ping agendada no momento. Crie um com `/content`.", delete_after=30)

        eventos_ordenados = sorted(
            self.eventos_ativos,
            key=lambda e: (e["unix_timestamp"] is None, e["unix_timestamp"] or 0)
        )

        embed = discord.Embed(
            title="📅 Agenda de Pings — Die Hard",
            description="Confira abaixo todos os pings agendadas no servidor:",
            color=discord.Color.gold()
        )

        for evento in eventos_ordenados:
            if evento["unix_timestamp"]:
                quando = f"<t:{evento['unix_timestamp']}:R> — <t:{evento['unix_timestamp']}:f>"
            else:
                quando = "🟢 Sem horário definido (imediata)"

            embed.add_field(
                name=f"💥 {evento['conteudo']}",
                value=f"**Líder:** <@{evento['autor_id']}>\n**Quando:** {quando}\n[Ir para a PT]({evento['jump_url']})",
                inline=False
            )

        await ctx.send(embed=embed)

# Função para inicializar e plugar essa engrenagem no main.py
async def setup(bot):
    await bot.add_cog(LFG(bot))