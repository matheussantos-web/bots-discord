import discord
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timezone

from config import (
    CARGOS, CARGOS_PERMITIDOS_SORTEIO, MINUTO_MINIMO_CALL_PADRAO
)

# Arquivos JSON para persistência
ARQUIVO_CONFIG = "data/sorteio_config.json"
ARQUIVO_INSCRITOS = "data/sorteio_inscritos.json"
ARQUIVO_TEMPO = "data/tempo_call.json"

def _carregar_json(caminho, padrao=None):
    """Carrega um arquivo JSON. Retorna o conteúdo ou o padrão."""
    if not os.path.exists(caminho):
        return padrao if padrao is not None else {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return padrao if padrao is not None else {}

def _salvar_json(caminho, dados):
    """Salva dados em um arquivo JSON."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False, default=str)

class Sorteio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==================== HELPERS ====================

    def _garantir_config(self):
        """Garante que existe uma config de sorteio. Retorna dict."""
        dados = _carregar_json(ARQUIVO_CONFIG)
        if not dados:
            dados = {
                "ultimo_ganhador_id": None,
                "premio_atual": "A definir",
                "minuto_minimo": MINUTO_MINIMO_CALL_PADRAO
            }
            _salvar_json(ARQUIVO_CONFIG, dados)
        return dados

    def _tem_permissao_sorteio(self, user):
        """Verifica se o membro tem permissão para gerenciar sorteios."""
        if user.guild_permissions.administrator:
            return True
        ids_permitidos = [CARGOS.get(nome) for nome in CARGOS_PERMITIDOS_SORTEIO if CARGOS.get(nome)]
        return any(cargo.id in ids_permitidos for cargo in user.roles)

    def _buscar_tempo_user(self, user_id_str):
        """Retorna (minutos_acumulados, ultima_entrada) do usuário."""
        dados = _carregar_json(ARQUIVO_TEMPO)
        user = dados.get(user_id_str, {})
        return user.get("minutos_acumulados", 0), user.get("ultima_entrada")

    def _calcular_minutos(self, minutos_acumulados, ultima_entrada):
        """Soma tempo parcial se estiver em call agora."""
        if ultima_entrada:
            try:
                ultima_dt = datetime.fromisoformat(ultima_entrada)
                agora = datetime.now(timezone.utc)
                minutos_parciais = int((agora - ultima_dt).total_seconds() / 60)
                return minutos_acumulados + minutos_parciais
            except (ValueError, TypeError):
                pass
        return minutos_acumulados

    # ==================== COMANDO PRINCIPAL ====================

    @commands.command(name="sorteio")
    async def sorteio(self, ctx, subcomando=None, *args):
        """Comando principal de sorteio."""
        if subcomando == "rodar":
            return await self._rodar_sorteio(ctx, args)
        elif subcomando == "listar":
            return await self._listar_inscritos(ctx)
        elif subcomando == "tempo":
            return await self._ver_tempo(ctx, args)
        elif subcomando == "config":
            return await self._configurar_tempo(ctx, args)
        elif subcomando == "premio":
            return await self._configurar_premio(ctx, args)
        elif subcomando == "status":
            return await self._ver_status(ctx)
        elif subcomando is not None:
            return await ctx.send("❌ Subcomando inválido. Use: `!sorteio`, `!sorteio rodar`, `!sorteio listar`, `!sorteio tempo`, `!sorteio config`, `!sorteio premio`, `!sorteio status`")

        # === FLUXO DE INSCRIÇÃO ===
        config = self._garantir_config()

        # 1. Checagem de Ganhador Anterior
        ultimo_ganhador = config.get("ultimo_ganhador_id")
        if ultimo_ganhador and ultimo_ganhador == str(ctx.author.id):
            embed = discord.Embed(
                title="❌ Inscrição Bloqueada",
                description="Você ganhou o último sorteio e precisa esperar o próximo para participar de novo.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        # 2. Checagem de Tempo em Call
        user_id_str = str(ctx.author.id)
        minutos_acumulados, ultima_entrada = self._buscar_tempo_user(user_id_str)
        minutos_total = self._calcular_minutos(minutos_acumulados, ultima_entrada)

        minimo_necessario = config.get("minuto_minimo", MINUTO_MINIMO_CALL_PADRAO)

        if minutos_total < minimo_necessario:
            embed = discord.Embed(
                title="❌ Tempo Insuficiente",
                description=f"Você precisa de pelo menos **{minimo_necessario} minutos** de call para participar.\nSeu tempo atual é **{minutos_total} minutos**.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        # 3. Verificar se já está inscrito
        inscritos = _carregar_json(ARQUIVO_INSCRITOS)
        if user_id_str in inscritos:
            embed = discord.Embed(
                title="⚠️ Já Inscrito",
                description="Você já está inscrito neste sorteio!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        # 4. Inscrever
        inscritos[user_id_str] = {
            "nome": ctx.author.display_name,
            "inscrito_em": datetime.now(timezone.utc).isoformat()
        }
        _salvar_json(ARQUIVO_INSCRITOS, inscritos)

        embed = discord.Embed(
            title="✅ Inscrição Realizada!",
            description=f"**{ctx.author.display_name}** foi inscrito(a) com sucesso!\n\nBoa sorte no sorteio!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Tempo acumulado: {minutos_total} minutos")
        await ctx.send(embed=embed)

    # ==================== SUBCOMANDOS ====================

    async def _rodar_sorteio(self, ctx, args):
        """Roda o sorteio e seleciona um vencedor."""
        if not self._tem_permissao_sorteio(ctx.author):
            return await ctx.send("❌ Acesso Negado: Você não tem permissão para rodar o sorteio.")

        config = self._garantir_config()
        inscritos = _carregar_json(ARQUIVO_INSCRITOS)

        if not inscritos:
            embed = discord.Embed(
                title="❌ Sorteio Cancelado",
                description="Nenhum inscrito no momento.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        # Selecionar vencedor aleatoriamente
        lista_ids = list(inscritos.keys())
        vencedor_id = random.choice(lista_ids)
        vencedor = ctx.guild.get_member(int(vencedor_id))

        # Definir prêmio
        premio = " ".join(args) if args else config.get("premio_atual", "A definir")

        # Atualizar config: novo ganhador
        config["ultimo_ganhador_id"] = vencedor_id
        config["premio_atual"] = premio
        _salvar_json(ARQUIVO_CONFIG, config)

        # Limpar inscritos
        _salvar_json(ARQUIVO_INSCRITOS, {})

        # Resetar tempo de call de todos
        _salvar_json(ARQUIVO_TEMPO, {})

        # Anunciar vencedor
        nome_vencedor = vencedor.display_name if vencedor else inscritos.get(vencedor_id, {}).get("nome", f"ID: {vencedor_id}")
        mention_vencedor = vencedor.mention if vencedor else f"<@{vencedor_id}>"

        embed = discord.Embed(
            title="🎉 SORTEIO ENCERRADO! 🎉",
            description=f"O vencedor foi: {mention_vencedor}\n\n**Prêmio:** {premio}",
            color=discord.Color.gold()
        )
        if vencedor:
            embed.set_thumbnail(url=vencedor.display_avatar.url)
        embed.set_footer(text=f"Total de inscritos: {len(lista_ids)}")
        embed.timestamp = datetime.now(timezone.utc)

        await ctx.send(embed=embed)

    async def _listar_inscritos(self, ctx):
        """Lista todos os inscritos no sorteio atual."""
        if not self._tem_permissao_sorteio(ctx.author):
            return await ctx.send("❌ Acesso Negado: Você não tem permissão para listar inscritos.")

        inscritos = _carregar_json(ARQUIVO_INSCRITOS)

        if not inscritos:
            embed = discord.Embed(
                title="📋 Inscritos no Sorteio",
                description="Nenhum inscrito no momento.",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)

        # Montar lista com tempo de call
        lista_formatada = []

        for user_id, dados in inscritos.items():
            member = ctx.guild.get_member(int(user_id))
            nome = member.display_name if member else dados.get("nome", f"ID: {user_id}")

            # Buscar tempo
            minutos_acumulados, ultima_entrada = self._buscar_tempo_user(user_id)
            minutos = self._calcular_minutos(minutos_acumulados, ultima_entrada)

            lista_formatada.append(f"• **{nome}** — {minutos} min")

        # Dividir em páginas se muito grande (max 20 por embed)
        paginas = [lista_formatada[i:i+20] for i in range(0, len(lista_formatada), 20)]

        for idx, pagina in enumerate(paginas):
            embed = discord.Embed(
                title=f"📋 Inscritos no Sorteio (Página {idx+1}/{len(paginas)})",
                description="\n".join(pagina),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Total: {len(inscritos)} inscrito(s)")
            await ctx.send(embed=embed)

    async def _ver_tempo(self, ctx, args):
        """Mostra o tempo acumulado em call de um membro."""
        if ctx.message.mentions:
            membro = ctx.message.mentions[0]
        else:
            membro = ctx.author

        minutos_acumulados, ultima_entrada = self._buscar_tempo_user(str(membro.id))
        minutos_total = self._calcular_minutos(minutos_acumulados, ultima_entrada)

        embed = discord.Embed(
            title="⏱️ Tempo em Call",
            description=f"**{membro.display_name}** possui **{minutos_total} minutos** acumulados em call.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        await ctx.send(embed=embed)

    async def _ver_status(self, ctx):
        """Mostra a configuração atual do sorteio."""
        config = self._garantir_config()

        ultimo_ganhador = config.get("ultimo_ganhador_id")
        if ultimo_ganhador:
            membro = ctx.guild.get_member(int(ultimo_ganhador))
            ganhador_texto = membro.mention if membro else f"ID: {ultimo_ganhador}"
        else:
            ganhador_texto = "Nenhum ainda"

        inscritos = _carregar_json(ARQUIVO_INSCRITOS)

        embed = discord.Embed(
            title="⚙️ Status do Sorteio",
            color=discord.Color.blue()
        )
        embed.add_field(name="🏆 Último Ganhador", value=ganhador_texto, inline=False)
        embed.add_field(name="🎁 Prêmio Atual", value=config.get("premio_atual", "A definir"), inline=False)
        embed.add_field(name="⏱️ Tempo Mínimo", value=f"{config.get('minuto_minimo', MINUTO_MINIMO_CALL_PADRAO)} minutos", inline=False)
        embed.add_field(name="👥 Inscritos Atuais", value=str(len(inscritos)), inline=False)

        await ctx.send(embed=embed)

    async def _configurar_tempo(self, ctx, args):
        """Configura o tempo mínimo de call para o sorteio."""
        if not self._tem_permissao_sorteio(ctx.author):
            return await ctx.send("❌ Acesso Negado: Você não tem permissão para configurar o sorteio.")

        if not args:
            return await ctx.send("❌ Use: `!sorteio config <minutos>`")

        try:
            minutos = int(args[0])
        except ValueError:
            return await ctx.send("❌ Por favor, forneça um número válido de minutos.")

        if minutos <= 0:
            return await ctx.send("❌ O tempo mínimo deve ser maior que 0 minutos.")

        config = self._garantir_config()
        config["minuto_minimo"] = minutos
        _salvar_json(ARQUIVO_CONFIG, config)

        embed = discord.Embed(
            title="⚙️ Configuração Atualizada",
            description=f"Tempo mínimo de call alterado para **{minutos} minutos**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    async def _configurar_premio(self, ctx, args):
        """Configura o prêmio atual do sorteio."""
        if not self._tem_permissao_sorteio(ctx.author):
            return await ctx.send("❌ Acesso Negado: Você não tem permissão para configurar o sorteio.")

        if not args:
            return await ctx.send("❌ Use: `!sorteio premio <descrição do prêmio>`")

        premio = " ".join(args)

        config = self._garantir_config()
        config["premio_atual"] = premio
        _salvar_json(ARQUIVO_CONFIG, config)

        embed = discord.Embed(
            title="🎁 Prêmio Atualizado",
            description=f"Prêmio do sorteio definido como: **{premio}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Sorteio(bot))
