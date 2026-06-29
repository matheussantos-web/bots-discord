import discord
from discord.ext import commands
import aiohttp
import asyncio

from config import GUILDA_ALBION_ID, ALIANCA_ALBION_ID, TAG_GUILDA, TAG_ALIANCA, CARGOS, CARGOS_PERMITIDOS_ADICIONAR

class Utilidades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cria UMA ÚNICA sessão para o bot inteiro usar (Muito mais rápido)
        self.session = aiohttp.ClientSession()
        # Semáforo: Permite no máximo 5 pesquisas no Albion ao mesmo tempo (evita crash)
        self.semaforo = asyncio.Semaphore(5)

    # Quando a Cog for desligada/recarregada, ele fecha a sessão com segurança
    async def cog_unload(self):
        await self.session.close()

    @commands.command(name="ajuda", aliases=["help", "comandos"])
    async def ajuda(self, ctx):
        await ctx.message.delete()
        
        embed = discord.Embed(
            title="📚 Central de Comandos da Guilda",
            description="Aqui estão todos os comandos disponíveis no servidor. Escolha o que você precisa:",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="👤 Comandos de Membros", 
            value=(
                "`!registrar SeuNick` ➔ Vincula sua conta do jogo e libera seu acesso.\n"
                "`!pontos` (ou `!saldo`) ➔ Mostra quantos pontos de atividade você tem.\n"
                "`!ping` ➔ Verifica se os sistemas estão online."
            ), 
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Comandos de Formação (LFG)", 
            value=(
                "`!vaga Conteúdo / Classe:Qtd / Hora:Minuto`\n"
                "➔ *Cria um painel interativo de PT.*\n"
                "➔ *Exemplo:* `!vaga ZvZ / Tank:2 / Healer:2 / 20:30`"
            ), 
            inline=False
        )
        
        # Verifica permissões para mostrar a área VIP da ajuda
        ids_permitidos = [CARGOS.get(nome) for nome in CARGOS_PERMITIDOS_ADICIONAR if CARGOS.get(nome)]
        tem_permissao = any(cargo.id in ids_permitidos for cargo in ctx.author.roles)
        
        if ctx.author.guild_permissions.administrator or tem_permissao:
            embed.add_field(
                name="⚙️ Comandos de Liderança (Restrito)", 
                value=(
                    "`!adicionarpontos @membro 10` ➔ Adiciona pontos na conta de alguém.\n"
                    "`!removerpontos @membro 10` ➔ Remove pontos da conta de alguém.\n"
                    "`!relatorio` ➔ Extrai a planilha do Excel com todos os pontos.\n"
                    "`!painel_registro` ➔ Gera o painel fixo de boas-vindas no chat atual."
                ), 
                inline=False
            )
            
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(text="Dúvidas? Procure um moderador ou oficial da guilda.")
        
        try:
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(f"⚠️ {ctx.author.mention}, sua DM está trancada! Aqui estão os comandos:", embed=embed, delete_after=60)


    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong! Todos os sistemas operacionais.")

    @commands.command(name="registrar")
    @commands.cooldown(1, 30, commands.BucketType.user)  # 1 uso a cada 30s por usuário
    async def registrar(self, ctx, *, nick: str = None):
        await ctx.message.delete()

        if not nick:
            return await ctx.send(
                f"⚠️ {ctx.author.mention}, use `!registrar SeuNick`.",
                delete_after=10
            )

        msg_aviso = await ctx.send(f"🔍 Buscando **{nick}** nos servidores do Albion, aguarde um momento...")

        try:
            nick_lower = nick.lower()

            async with self.semaforo:  # Controla chamadas simultâneas
                timeout = aiohttp.ClientTimeout(total=10)  # Timeout de 10s
                async with self.session.get(
                    f"https://gameinfo.albiononline.com/api/gameinfo/search?q={nick}",
                    timeout=timeout
                ) as resp:
                    if resp.status != 200:
                        return await msg_aviso.edit(
                            content="❌ Erro ao conectar com o Albion. Tente novamente."
                        )
                    dados = await resp.json()

            jogadores = dados.get('players', [])
            jogador_encontrado = next(
                (p for p in jogadores if p['Name'].lower() == nick_lower), None
            )

            if not jogador_encontrado:
                return await msg_aviso.edit(content=f"❌ O jogador **{nick}** não foi encontrado!")

            guild_id_jogador = jogador_encontrado.get('GuildId')
            alliance_id_jogador = jogador_encontrado.get('AllianceId')
            nome_correto = jogador_encontrado['Name']

            cargo_dar = None
            nova_tag = ""
            mensagem_final = ""

            if guild_id_jogador == GUILDA_ALBION_ID:
                cargo_dar = ctx.guild.get_role(CARGOS["DIE HARD"])
                nova_tag = f"{TAG_GUILDA} {nome_correto}"
                mensagem_final = f"✅ **Sucesso!** Bem-vindo à guilda, {ctx.author.mention}!"
            elif ALIANCA_ALBION_ID and alliance_id_jogador == ALIANCA_ALBION_ID:
                cargo_dar = ctx.guild.get_role(CARGOS["aliado"])
                nova_tag = f"{TAG_ALIANCA} {nome_correto}"
                mensagem_final = f"🤝 **Sucesso!** Aliado reconhecido, {ctx.author.mention}!"
            else:
                return await msg_aviso.edit(
                    content="❌ Acesso Negado: Você não pertence à Guilda/Aliança."
                )

            # Aplica cargo e nick em paralelo
            tarefas = []
            if cargo_dar:
                tarefas.append(ctx.author.add_roles(cargo_dar))
            tarefas.append(ctx.author.edit(nick=nova_tag[:32]))

            resultados = await asyncio.gather(*tarefas, return_exceptions=True)

            for resultado in resultados:
                if isinstance(resultado, discord.Forbidden):
                    mensagem_final += "\n⚠️ Sem permissão para aplicar cargo/nick. Avise a liderança."

            await msg_aviso.edit(content=mensagem_final)

        except asyncio.TimeoutError:
            await msg_aviso.edit(content="⏱️ A API do Albion demorou demais. Tente novamente.")
        except Exception as e:
            await msg_aviso.edit(content=f"⚠️ Ocorreu um erro interno: {e}")

    @registrar.error
    async def registrar_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏳ {ctx.author.mention}, aguarde **{error.retry_after:.0f}s** antes de tentar de novo.",
                delete_after=10
            )

# Função obrigatória para inicializar a Cog
async def setup(bot):
    await bot.add_cog(Utilidades(bot))