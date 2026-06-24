# 🛡️ Bot da Guilda: I DieHard I (Albion Online)

Este é um bot multifuncional para Discord desenvolvido em Python (`discord.py`). Ele foi projetado para automatizar o gerenciamento da guilda **I DieHard I** no Albion Online, facilitando o recrutamento, a organização de salas de voz e a formação de grupos (LFG) para eventos no jogo.

A aplicação foi estruturada com foco em alta disponibilidade, contando com um servidor web integrado (`Flask`) para permitir hospedagem contínua em plataformas Cloud.

## ✨ Funcionalidades

- **⚔️ Integração com Albion Online:** Sistema de verificação via API oficial. O bot confere se o jogador pertence à guilda ou aliança no jogo, altera o apelido dele no Discord para o nick exato do jogo e atribui o cargo correto automaticamente.
- **🎧 Sistema de Calls Dinâmicas:** Criação automática de salas de voz temporárias quando um usuário entra no canal gerador. A sala é deletada automaticamente assim que o último membro sai, mantendo o servidor limpo.
- **📋 LFG e Fila Inteligente (FIFO):** Sistema interativo para criar eventos (ZvZs, Ganks, Masmorras) com limite de vagas por classe. Conta com uma fila de espera inteligente e **Autopromoção**: se alguém abandona a vaga principal, o bot puxa o próximo da fila automaticamente e o avisa no chat.
- **☁️ Arquitetura Cloud-Native:** Preparado para rodar 24/7 de forma gratuita usando um servidor fantasma em segundo plano.

---

## 🎮 Como Usar no Discord (Comandos e Funções)

Aqui estão todas as interações e automações que operam diretamente no chat e nos canais do seu servidor:

### 🛡️ Comandos Gerais (Para todos os Membros)

| Comando      | Exemplo de Uso                | O que faz                                                                                              |
| :----------- | :---------------------------- | :----------------------------------------------------------------------------------------------------- |
| `!registrar` | `!registrar SeuNick`          | Consulta a API oficial do Albion. Se aprovado, altera o nick no Discord e dá o cargo de Membro/Aliado. |
| `!vaga`      | `!vaga Gank \ Tank:1 \ DPS:3` | Cria um card interativo com botões para os jogadores se inscreverem no evento e gerencia as filas.     |
| `!ping`      | `!ping`                       | Retorna uma mensagem confirmando que o bot está online e com os sistemas operacionais.                 |

### 👑 Comandos de Moderação (Apenas para Liderança)

| Comando            | Exemplo de Uso     | O que faz                                                                                |
| :----------------- | :----------------- | :--------------------------------------------------------------------------------------- |
| `!painel_registro` | `!painel_registro` | Gera um painel visual fixo e bonito ensinando os novatos a usarem o comando de registro. |

### 🎧 Funcionalidades Automáticas (Sem digitar comandos)

- **Salas de Voz Temporárias:** Ninguém precisa digitar nada para criar uma call. Basta o membro entrar no canal de voz fixo configurado (ex: **`➕ Criar Call`**). O bot instantaneamente criará uma nova sala particular chamada `🎮 [Nome do Membro]` e o moverá para lá. Quando vazia, a sala é deletada.

---

## 🛠️ Como Instalar e Rodar Localmente (Na sua máquina)

Para testes e desenvolvimento, siga o passo a passo abaixo para rodar o bot no seu próprio computador:

### Passo 1: Instalação das Dependências

Certifique-se de ter o Python 3 instalado. No terminal, dentro da pasta do projeto, instale todas as bibliotecas necessárias de uma vez:

```bash
pip install -r requirements.txt

Passo 2: Configuração do Servidor e IDs
Abra o arquivo main.py e preencha as variáveis no topo do código:

GUILDA_ALBION_ID e ALIANCA_ALBION_ID: IDs do jogo (pesquise na API oficial do Albion).

CANAL_GERADOR_ID: ID do canal de voz fixo "Criar Call" do seu Discord.

CARGOS: Substitua os números pelos IDs reais dos cargos do seu servidor.

⚠️ Importante: O cargo do bot no Discord deve estar acima de todos os outros da hierarquia (Membros/Aliados) nas configurações do servidor para que ele tenha permissão de alterar nicks e dar cargos.

Passo 3: Variável de Ambiente e Inicialização
Crie uma variável de ambiente na sua máquina chamada TOKEN_DO_BOT contendo o token do Discord Developer Portal.

Em seguida, execute:
python main.py

☁️ Hospedagem Online 24/7 (Deploy via Render)
Este projeto já está configurado para deploy contínuo (CI/CD) e hospedagem gratuita no Render.com.

Crie um novo Web Service no Render e conecte este repositório do GitHub.

Nas configurações, use:

Build Command: pip install -r requirements.txt

Start Command: python main.py

Vá em Environment Variables (Avançado) e adicione:

Key: TOKEN_DO_BOT

Value: [Seu Token do Discord]

Clique em Deploy.

Prevenção de Suspensão: Copie o link da URL gerada pelo Render e cadastre no site UptimeRobot, configurando um monitor HTTP(s) para pingar o site a cada 5 minutos. Isso impede que o servidor entre em modo de hibernação.

Desenvolvido por: Juan Victor Dias Claros
```
