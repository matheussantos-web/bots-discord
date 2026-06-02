# 🛡️ Bot da Guilda: I DieHard I (Albion Online)

Este é um bot multifuncional para Discord desenvolvido em Python (`discord.py`). Ele foi projetado para automatizar o gerenciamento da guilda **I DieHard I** no Albion Online, mas pode ser facilmente adaptado para qualquer guilda ou servidor, facilitando o recrutamento, a organização de salas de voz e a moderação.

## ✨ Funcionalidades

- **⚔️ Integração com Albion Online:** Sistema de verificação via API oficial. O bot confere se o jogador pertence à guilda no jogo, altera o apelido dele no Discord para o nick exato do jogo e atribui o cargo de Membro automaticamente.
- **🎧 Sistema de Calls Dinâmicas:** Criação automática de salas de voz temporárias quando um usuário entra no canal gerador. A sala é deletada automaticamente assim que o último membro sai, mantendo o servidor limpo.
- **👑 Moderação e Cargos:** Comandos dedicados para a liderança alterar apelidos e gerenciar a hierarquia do servidor (Padrão, Membro, Liderança Mediana e Alta).

---

## 🎮 Como Usar no Discord (Comandos e Funções)

Aqui estão todas as interações e automações que operam diretamente no chat e nos canais do seu servidor:

### 🛡️ Comandos Gerais (Para todos os Membros)

| Comando      | Exemplo de Uso           | O que faz                                                                                                                                            |
| :----------- | :----------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| `!registrar` | `!registrar JoaoMatador` | Consulta a API oficial do Albion. Se o jogador estiver na guilda, o bot altera o nick no Discord para ficar igual ao do jogo e dá o cargo de Membro. |
| `!ping`      | `!ping`                  | Comando de teste. Retorna uma mensagem confirmando que o bot está online e processando os comandos.                                                  |

### 👑 Comandos de Moderação (Apenas para Liderança)

| Comando      | Exemplo de Uso                | O que faz                                                                                                                       |
| :----------- | :---------------------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| `!dar_cargo` | `!dar_cargo @Joao membro`     | Atribui um cargo específico ao usuário marcado. Os níveis configurados são: `padrao`, `membro`, `lider_mediano` e `lider_alto`. |
| `!mudarnick` | `!mudarnick @Joao JoaoSniper` | Força a alteração do apelido de um usuário no servidor para manter a organização.                                               |

### 🎧 Funcionalidades Automáticas (Sem digitar comandos)

- **Salas de Voz Temporárias:** Ninguém precisa digitar nada para criar uma call. Basta o membro entrar no canal de voz fixo configurado (ex: **`➕ Criar Call`**). O bot instantaneamente criará uma nova sala particular chamada `🎮 [Nome do Membro]` e o moverá para lá. Quando todos saírem e a sala ficar vazia, o bot a deletará automaticamente para manter a lista de canais do servidor limpa.

---

## 🛠️ Como Instalar e Rodar Localmente (Na sua máquina)

Para testes e desenvolvimento, siga o passo a passo abaixo para rodar o bot no seu próprio computador:

### Passo 1: Instalação do Python

Abra o terminal e execute o comando correspondente ao seu sistema operacional para instalar o Python:

- **Windows:**

```cmd
winget install Python.Python.3.11
```

- **Linux (Ubuntu / Debian):**

```bash
sudo apt update && sudo apt install python3 python3-pip
```

- **macOS:**

```bash
brew install python
```

### Passo 2: Instalação das Bibliotecas

No terminal, dentro da pasta do projeto, digite:

```bash
pip install discord aiohttp
```

### Passo 3: Configuração do Servidor e IDs

Abra o arquivo `main.py` e preencha as variáveis no topo do código:

1. `GUILDA_ALBION_ID`: O ID da sua guilda (pesquise na API oficial do Albion).
2. `CANAL_GERADOR_ID`: Crie um canal de voz fixo no seu Discord e cole o ID dele aqui.
3. `CARGOS`: Substitua os números falsos pelos IDs reais dos cargos do seu servidor.
4. **Token:** Cole o Token gerado no Discord Developer Portal na última linha do arquivo: `bot.run('SEU_TOKEN_AQUI')`.

**⚠️ Importante:** O cargo do bot no Discord deve estar acima de todos os outros da hierarquia para que ele tenha permissão de alterar nicks e dar cargos.

### Passo 4: Inicializando o Bot

Abra o terminal na pasta onde o arquivo `main.py` está salvo e execute:

```bash
python main.py
```

---

## ☁️ Opções de Hospedagem Online (Bot rodando 24/7)

Para que o bot não desligue quando você fechar o seu computador, ele precisa ser hospedado em um servidor na nuvem. Aqui estão as melhores opções gratuitas:

**1. Square Cloud (Recomendado para Iniciantes)**

- É uma plataforma focada em bots do Discord, com interface em português.
- O plano `Free` permite hospedar bots em Python facilmente enviando os arquivos compactados em `.zip`.

**2. Oracle Cloud (Opção Profissional 100% Gratuita)**

- A Oracle oferece o programa "Always Free", fornecendo um VPS (Servidor Virtual Privado) Linux gratuito para sempre.
- Ideal para quem quer um bot online 24 horas por dia sem quedas, mas exige configuração via terminal (semelhante ao Passo 1 do Linux acima).

**3. Discloud**

- Plataforma similar à Square Cloud, suporta `discord.py` perfeitamente.
- A configuração é feita adicionando um arquivo simples chamado `discloud.config` na pasta do projeto. No plano gratuito, exige renovação manual no site a cada poucos dias.

---

**Desenvolvido por:** Juan Victor
