import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# Importa os cargos do seu arquivo de configuração
from config import CARGOS

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
    def __init__(self, conteudo, definicao_vagas, autor_id, unix_timestamp=None):
        super().__init__(timeout=None)
        self.conteudo = conteudo
        self.max_vagas = definicao_vagas
        self.autor_id = autor_id 
        self.unix_timestamp = unix_timestamp 
        self.jogadores = {classe: [] for classe in definicao_vagas}
        self.fila_espera = {classe: [] for classe in definicao_vagas}

        for classe in definicao_vagas.keys():
            self.add_item(BotaoDinamico(classe, self))
            
        botao_sair = discord.ui.Button(label="Sair da Lista", style=discord.ButtonStyle.danger, emoji="❌")
        botao_sair.callback = self.sair_callback
        self.add_item(botao_sair)

    def gerar_embed(self):
        titulo_destaque = f"💥 {self.conteudo.upper()} 💥"
        
        status_texto = "🟢 Formando Grupo"
        if self.unix_timestamp:
            status_texto += f" | ⏱️ **Começa:** <t:{self.unix_timestamp}:R>"
        
        embed = discord.Embed(
            title=titulo_destaque, 
            description=f"**Líder da PT:** <@{self.autor_id}>\n**Status:** {status_texto}\n━━━━━━━━━━━━━━━━━━━━━━\n",
            color=discord.Color.brand_red()
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
            
        embed.set_footer(text="Clique nos botões abaixo para entrar ou sair da fila.")
        return embed

    async def promover_da_fila(self, interaction: discord.Interaction, classe: str):
        if len(self.jogadores[classe]) < self.max_vagas[classe] and len(self.fila_espera[classe]) > 0:
            proximo_jogador = self.fila_espera[classe].pop(0) 
            self.jogadores[classe].append(proximo_jogador)
            await interaction.channel.send(f"🎉 {proximo_jogador}, uma vaga abriu e você assumiu como **{classe}**!")

    async def processar_clique(self, interaction: discord.Interaction, classe: str):
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

    async def abrir_modal_lider(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message("❌ Acesso Negado: Apenas o criador pode puxar membros!", ephemeral=True)
        await interaction.response.send_modal(ModalPuxarMembro(self))

    async def forcar_insercao(self, interaction: discord.Interaction, usuario: str, classe: str):
        for c in self.jogadores:
            if usuario in self.jogadores[c]: 
                self.jogadores[c].remove(usuario)
            if usuario in self.fila_espera[c]: 
                self.fila_espera[c].remove(usuario)

        if len(self.jogadores[classe]) < self.max_vagas[classe]:
            self.jogadores[classe].append(usuario)
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
            await interaction.followup.send(f"✅ Membro forçado na vaga de **{classe}**!", ephemeral=True)
        else:
            self.fila_espera[classe].append(usuario)
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
            await interaction.followup.send(f"⚠️ Fila de Espera de **{classe}**.", ephemeral=True)

# ==========================================
# CLASSE COG (COMANDO)
# ==========================================

class LFG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vaga")
    async def vaga(self, ctx, *, texto: str = None):
        await ctx.message.delete()
        
        if texto is None:
            embed_ajuda = discord.Embed(
                title="🛠️ Manual de Criação de PT (!vaga)",
                description="Aprenda a montar o seu painel interativo de vagas passo a passo.",
                color=discord.Color.blue()
            )
            embed_ajuda.add_field(
                name="🧩 Entendendo as Peças do Comando:",
                value=(
                    "**1. Título:** O nome do seu conteúdo (Ex: `Gank`).\n"
                    "**2. Vagas:** O nome da função e a quantidade de jogadores separados por dois-pontos (Ex: `Tank:2`).\n"
                    "**3. Horário:** A hora que a PT vai sair (Opcional, Ex: `20:30`).\n"
                    "*(Importante: Separe cada uma dessas peças usando uma barra `/`)*"
                ),
                inline=False
            )
            embed_ajuda.add_field(
                name="🎯 Exemplo 1: PT Agendada (Com Horário)",
                value=(
                    "*Você quer montar um Gank mais tarde, às 21:30, e precisa de 1 Tank, 2 Suportes e 5 DPS.* \n"
                    "**Você digita exatamente assim:**\n"
                    "`!vaga 🗡️ Gank na Red / Tank:1 / Suporte:2 / DPS:5 / 21:30`"
                ),
                inline=False
            )
            embed_ajuda.add_field(
                name="⚡ Exemplo 2: PT Imediata (Sem Horário)",
                value=(
                    "*Você quer montar um grupo de Fama agora mesmo e precisa de 1 Healer e 3 DPS.*\n"
                    "**Você digita exatamente assim:**\n"
                    "`!vaga 📖 Fama Group / Healer:1 / DPS:3`"
                ),
                inline=False
            )
            embed_ajuda.add_field(
                name="⚠️ Atenção aos Detalhes:",
                value=(
                    "• Nunca esqueça de colocar os dois-pontos `:` para a quantidade de vagas (Errado: `Tank 2`, Certo: `Tank:2`).\n"
                    "• Os nomes das classes que você escrever aqui (ex: DPS, Curandeiro, Suporte) serão **exatamente** os nomes que vão aparecer nos botões em que os jogadores vão clicar."
                ),
                inline=False
            )
            return await ctx.send(embed=embed_ajuda, delete_after=120)
        
        try:
            partes = texto.split('/')
            conteudo = partes[0].strip()
            definicao_vagas = {}
            horario_evento = None
            
            for parte in partes[1:]:
                parte_limpa = parte.strip()
                if not parte_limpa:
                    continue
                    
                if ":" in parte_limpa and len(parte_limpa) <= 5:
                    partes_tempo = parte_limpa.split(':')
                    if len(partes_tempo) == 2:
                        h, m = partes_tempo
                        if h.isdigit() and m.isdigit() and len(h) <= 2 and len(m) == 2:
                            horario_evento = parte_limpa
                            continue 
                            
                if ":" not in parte_limpa:
                    raise ValueError()
                    
                nome_classe, qtd = parte_limpa.split(':', 1)
                if not qtd.strip().isdigit():
                    raise ValueError()
                    
                definicao_vagas[nome_classe.strip()] = int(qtd.strip())
                
            if not definicao_vagas:
                raise ValueError()
                
        except Exception as e:
            mensagem_erro = "⚠️ **Formato incorreto!** Faltou alguma barra (`/`) ou dois-pontos (`:`). Digite apenas `!vaga` para ver o manual de instruções."
            return await ctx.send(mensagem_erro, delete_after=60)

        unix_timestamp = None
        if horario_evento:
            try:
                h_str, m_str = horario_evento.split(':')
                fuso = timezone(timedelta(hours=-4))
                agora = datetime.now(fuso)
                data_evento = agora.replace(hour=int(h_str), minute=int(m_str), second=0, microsecond=0)
                if data_evento < agora:
                    data_evento += timedelta(days=1)
                unix_timestamp = int(data_evento.timestamp())
            except:
                pass

        painel = PainelVagas(conteudo, definicao_vagas, ctx.author.id, unix_timestamp)
        embed_inicial = painel.gerar_embed()
        
        # Puxando o cargo correto que você configurou para dar mention na guilda
        id_cargo_membro = CARGOS.get("DIE HARD")
        mencao_cargo = f"<@&{id_cargo_membro}>" if id_cargo_membro else "@everyone"

        await ctx.send(content=f"📢 {mencao_cargo}", embed=embed_inicial, view=painel)

# Função para inicializar e plugar essa engrenagem no main.py
async def setup(bot):
    await bot.add_cog(LFG(bot))