# Bot da Guilda: I DieHard I (Albion Online)

Bot multifuncional para Discord desenvolvido em Python (`discord.py`). Projetado para automatizar o gerenciamento da guilda **I DieHard I** no Albion Online.

## Funcionalidades

- **Integracao com Albion Online:** Verificacao via API oficial. Altera nick e atribui cargo automaticamente.
- **Calls Dinamicas:** Criacao automatica de salas de voz temporarias.
- **LFG e Fila Inteligente:** Sistema interativo para criar eventos com limite de vagas por classe e fila de espera.
- **Sistema de Sorteio:** Inscricao com verificacao de tempo em call, sorteio aleatorio e rastreamento de ganhadores.
- **Cloud-Native:** Servidor web integrado (Flask) para hospedagem continua.

---

## Comandos do Discord

### Comandos Gerais (Todos os Membros)

| Comando | Exemplo | O que faz |
|:---|:---|:---|
| `!registrar` | `!registrar SeuNick` | Consulta API do Albion, altera nick e da cargo. |
| `!pontos` | `!pontos` | Mostra pontos de atividade acumulados. |
| `!sorteio` | `!sorteio` | Inscreve no sorteio da guilda. |
| `!sorteio tempo` | `!sorteio tempo` | Mostra tempo acumulado em call. |
| `!agenda` | `!agenda` | Lista eventos LFG ativos. |
| `!ping` | `!ping` | Verifica se o bot esta online. |
| `!ajuda` | `!ajuda` | Lista todos os comandos disponiveis. |

### Slash Commands

| Comando | O que faz |
|:---|:---|
| `/content` | Cria painel interativo de vagas para eventos. |
| `/template` | Gerencia templates de eventos (criar, listar, remover). |

### Comandos de Lideranca (Restritos)

| Comando | Exemplo | O que faz |
|:---|:---|:---|
| `!adicionarpontos` | `!adicionarpontos @membro 10` | Adiciona pontos na conta de alguem. |
| `!removerpontos` | `!removerpontos @membro 10` | Remove pontos da conta de alguem. |
| `!relatorio` | `!relatorio` | Gera planilha Excel com todos os pontos. |
| `!sorteio rodar` | `!sorteio rodar Arma 4.4` | Encerra inscricoes e sorteia vencedor. |
| `!sorteio listar` | `!sorteio listar` | Lista todos os inscritos. |
| `!sorteio config` | `!sorteio config 60` | Altera tempo minimo de call. |
| `!sorteio premio` | `!sorteio premio Loot DG 8.2` | Define o premio atual. |

### Funcionalidades Automaticas

- **Calls Dinamicas:** Membro entra no canal gerador -> bot cria sala temporaria. Quando vazia, deleta.
- **Farm de Pontos:** Membros em calls com 5+ pessoas ganham pontos a cada 10 minutos.
- **Auditoria Diaria:** Bot verifica se membros ainda estao na guilda/alianca no jogo.
- **Limpeza Automatica:** Mensagens antigas sao removidas periodicamente.

---

## Instalacao

### Dependencias
```bash
pip install -r requirements.txt
```

### Configuracao
1. Copie `.env.example` para `.env` e adicione seu token:
   ```
   TOKEN_DO_BOT=seu_token_aqui
   ```

2. Configure os IDs em `config.py`:
   - `GUILDA_ALBION_ID` e `ALIANCA_ALBION_ID`
   - `CANAIS_GERADORES_IDS` (canais de voz que criam calls)
   - `CARGOS` (IDs dos cargos do servidor)

### Rodar
```bash
python main.py
```

### Hospedagem 24/7 (Render)
1. Crie um Web Service no Render conectando o repositorio
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python main.py`
4. Adicione a variavel de ambiente `TOKEN_DO_BOT`
5. Configure o UptimeRobot para pingar a URL a cada 5 minutos

---

Desenvolvido por: Juan Victor Dias Claros
