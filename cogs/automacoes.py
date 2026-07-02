import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from datetime import datetime, timedelta, timezone

# Importa as configurações do seu arquivo principal
from config import (
    CANAL_LIMPEZA_ID, CARGOS, GUILDA_ALBION_ID, ALIANCA_ALBION_ID,
    MONGO_URI, colecao_pontos, MINIMO_PESSOAS_CALL, PONTOS_POR_CICLO,
    MULTIPLICADOR_CALLER, MENSAGEM_CLASSES_ID, REACOES_CLASSES, CANAIS_GERADORES_IDS
)

class Automacoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # LIGANDO OS MOTORES (ON_READY)
    # ==========================================
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.auditoria_guilda.is_running():
            self.auditoria_guilda.start()
            
        if not self.limpeza_automatica.is_running():
            self.limpeza_automatica.start()

        if not self.farm_de_pontos.is_running():
            self.farm_de_pontos.start()

    # ==========================================
    # SISTEMA DE LIMPEZA AUTOMÁTICA
    # ==========================================
    @tasks.loop(minutes=30)
    async def limpeza_automatica(self):
        if CANAL_LIMPEZA_ID == 0:
            return 

        canal = self.bot.get_channel(CANAL_LIMPEZA_ID)
        if not canal:
            return

        limite_tempo = datetime.now(timezone.utc) - timedelta(hours=6)

        def verificar_mensagem(msg):
            return not msg.pinned 

        try:
            deletadas = await canal.purge(limit=None, before=limite_tempo, check=verificar_mensagem)
            if len(deletadas) > 0:
                print(f"🧹 Faxina concluída! {len(deletadas)} mensagens apagadas no canal de limpeza.")
        except Exception as e:
            print(f"⚠️ Erro ao tentar limpar o chat: {e}")

    # ==========================================
    # SISTEMA DE AUDITORIA DE MEMBROS
    # ==========================================
    @tasks.loop(hours=24)
    async def auditoria_guilda(self):
        print("🔍 Iniciando ronda de auditoria diária na API do Albion...")
        
        if not self.bot.guilds:
            return
            
        guilda_discord = self.bot.guilds[0] 
        
        cargos_gerenciados = []
        for id_cargo in CARGOS.values():
            cargo = guilda_discord.get_role(id_cargo)
            if cargo:
                cargos_gerenciados.append(cargo)

        for membro in guilda_discord.members:
            if membro.bot:
                continue

            nomes_imunes = ["lider", "DIE HARD", "recrutador", "moderador", "caller", "SUB-LIDER"]
            ids_imunes = [CARGOS.get(nome) for nome in nomes_imunes if CARGOS.get(nome)]

            if any(c.id in ids_imunes for c in membro.roles):
                continue

            cargos_do_membro = [c for c in cargos_gerenciados if c in membro.roles]

            if not cargos_do_membro:
                continue

            nick = membro.display_name
            if " " in nick:
                nick = nick.split(" ", 1)[1] 

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"https://gameinfo.albiononline.com/api/gameinfo/search?q={nick}") as resp:
                        if resp.status != 200:
                            await asyncio.sleep(2) 
                            continue
                        
                        dados = await resp.json()
                        jogadores = dados.get('players', [])
                        jogador_encontrado = next((p for p in jogadores if p['Name'].lower() == nick.lower()), None)

                        rebaixar = False

                        if not jogador_encontrado:
                            rebaixar = True
                        else:
                            guild_id_jogador = jogador_encontrado.get('GuildId')
                            alliance_id_jogador = jogador_encontrado.get('AllianceId')

                            is_guilda = (guild_id_jogador == GUILDA_ALBION_ID)
                            is_alianca = (ALIANCA_ALBION_ID and alliance_id_jogador == ALIANCA_ALBION_ID)

                            if not is_guilda and not is_alianca:
                                rebaixar = True

                        if rebaixar:
                            await membro.remove_roles(*cargos_do_membro)
                            print(f"⚠️ {membro.display_name} foi rebaixado.")
                            
                            try:
                                await membro.send("⚠️ **Aviso Automático:** Seus cargos no Discord da guilda foram removidos porque nosso sistema detectou que você não está mais na guilda/aliança no jogo. Se isso for um erro, use o comando `!registrar` novamente!")
                            except discord.Forbidden:
                                pass 

                except Exception as e:
                    print(f"Erro na auditoria do jogador {nick}: {e}")

            await asyncio.sleep(2)
            
        print("✅ Base concluída.")

    # ==========================================
    # SISTEMA DE FARM DE PONTOS EM CALL
    # ==========================================
    @tasks.loop(minutes=10)
    async def farm_de_pontos(self):
        if not MONGO_URI:
            return

        for guilda in self.bot.guilds:
            cargos_bonus = [CARGOS.get("caller"), CARGOS.get("caller novato")]

            for canal_voz in guilda.voice_channels:
                membros_na_call = [m for m in canal_voz.members if not m.bot]

                if len(membros_na_call) >= MINIMO_PESSOAS_CALL:
                    for membro in membros_na_call:
                        id_str = str(membro.id)
                        eh_caller = any(c.id in cargos_bonus for c in membro.roles)
                        
                        pontos_ganhos = (PONTOS_POR_CICLO * MULTIPLICADOR_CALLER) if eh_caller else PONTOS_POR_CICLO

                        await colecao_pontos.update_one(
                            {"_id": id_str},
                            {"$inc": {"pontos": pontos_ganhos}},
                            upsert=True
                        )

    # ==========================================
    # EVENTOS DE CARGO POR REAÇÃO (REACTION ROLES)
    # ==========================================
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != MENSAGEM_CLASSES_ID:
            return
        
        if payload.member.bot:
            return

        emoji = str(payload.emoji)
        id_cargo = REACOES_CLASSES.get(emoji)

        if id_cargo:
            guild = self.bot.get_guild(payload.guild_id)
            cargo = guild.get_role(id_cargo)
            if cargo:
                try:
                    await payload.member.add_roles(cargo)
                    print(f"✅ {payload.member.display_name} pegou a classe de {cargo.name}.")
                except discord.Forbidden:
                    print("❌ Erro: O cargo do bot precisa estar acima do cargo da classe.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id != MENSAGEM_CLASSES_ID:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        membro = guild.get_member(payload.user_id)
        if not membro or membro.bot:
            return

        emoji = str(payload.emoji)
        id_cargo = REACOES_CLASSES.get(emoji)

        if id_cargo:
            cargo = guild.get_role(id_cargo)
            if cargo:
                try:
                    await membro.remove_roles(cargo)
                    print(f"🔴 {membro.display_name} removeu a classe de {cargo.name}.")
                except discord.Forbidden:
                    pass        
            
    # ==========================================
    # CRIADOR DE CALLS DINÂMICAS
    # ==========================================
@commands.Cog.listener()
async def on_voice_state_update(self, member, before, after):
        
        # --- 1. ENTROU NUM GERADOR ---
        if after.channel and after.channel.id in CANAIS_GERADORES_IDS:
            guilda = member.guild
            categoria = after.channel.category
            
            # Bloqueia a visão geral, mas dá poder de GERENCIAR O CANAL para o criador
            permissoes = {
                guilda.default_role: discord.PermissionOverwrite(view_channel=False), 
                member: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True) 
            }
            
            # Aplica permissão para todos os cargos registrados no seu config.py
            for nome, id_cargo in CARGOS.items():
                cargo_obj = guilda.get_role(id_cargo)
                if cargo_obj: 
                    permissoes[cargo_obj] = discord.PermissionOverwrite(view_channel=True, connect=True)
            
            try:
                novo_canal = await guilda.create_voice_channel(
                    name=f"🎮 {member.display_name}",
                    category=categoria,
                    overwrites=permissoes
                )
                
                # 🔒 TRAVA DE SEGURANÇA 1: Verifica se o membro ainda está conectado em alguma call
                if member.voice and member.voice.channel:
                    await member.move_to(novo_canal)
                else:
                    # Se ele saiu rápido demais, apaga a sala órfã
                    await novo_canal.delete()
                    
            except Exception as e:
                print(f"⚠️ Erro na criação de call temporária: {e}")

        # --- 2. SAIU DE UMA CALL TEMPORÁRIA ---
        if before.channel and before.channel.name.startswith("🎮") and before.channel.id not in CANAIS_GERADORES_IDS:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                except discord.NotFound:
                    # 🔒 TRAVA DE SEGURANÇA 2: Ignora o erro se outro evento simultâneo já apagou o canal
                    pass
                except Exception as e:
                    print(f"⚠️ Erro ao apagar call temporária: {e}")

# Função para plugar no main.py
async def setup(bot):
    await bot.add_cog(Automacoes(bot))