# OptiFlow AI Chatbot - Guia de Instalação e Uso

## 🤖 Sobre o Chatbot

O OptiFlow AI Assistant é um chatbot inteligente integrado à plataforma OptiFlow que fornece insights sobre seus dispositivos industriais, alarmes e dados de séries temporais. Ele utiliza a API da OpenAI para fornecer respostas contextualizadas e recomendações acionáveis.

## ✨ Funcionalidades

- **Análise Inteligente**: Obtenha insights sobre o status dos seus dispositivos industriais
- **Monitoramento de Alarmes**: Consulte alarmes ativos e histórico
- **Recomendações**: Receba sugestões de otimização baseadas em dados
- **Conversas Persistentes**: Histórico de conversas salvo no banco de dados
- **Sugestões Contextuais**: Perguntas sugeridas baseadas na conversa
- **Interface Moderna**: UI responsiva e intuitiva

## 🚀 Instalação

### Backend

1. **Instale as dependências do Python:**

```bash
cd backend
pip install -r requirements.txt
```

2. **Configure a variável de ambiente para a API da OpenAI:**

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua chave da API OpenAI:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7
```

**Onde obter a chave da API:**
- Acesse [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Faça login ou crie uma conta
- Crie uma nova chave de API
- Copie e cole no arquivo `.env`

3. **Execute as migrações do banco de dados:**

```bash
# O banco de dados será criado automaticamente quando você iniciar o backend
```

4. **Inicie o servidor backend:**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

1. **Instale as dependências do Node.js:**

```bash
cd frontend
npm install
```

2. **Configure a URL da API (opcional):**

Crie um arquivo `.env` no diretório `frontend`:

```env
VITE_API_URL=http://localhost:8000
```

3. **Inicie o servidor de desenvolvimento:**

```bash
npm run dev
```

A aplicação estará disponível em `http://localhost:5173`

## 📖 Como Usar

### Interface do Usuário

1. **Acesse a aplicação** em `http://localhost:5173`
2. **Clique em "Abrir AI Assistant"** para iniciar o chatbot
3. **Digite sua pergunta** na caixa de texto inferior
4. **Envie a mensagem** clicando no botão de enviar ou pressionando Enter

### Exemplos de Perguntas

- "Quais dispositivos estão offline?"
- "Mostre-me os alarmes ativos"
- "Como está a performance do sistema?"
- "Quais são as tendências de dados nas últimas 24 horas?"
- "Há dispositivos que precisam de manutenção?"
- "Mostre padrões nos alarmes recentes"

### Recursos Avançados

#### Conversas Múltiplas
- Clique no ícone de menu (canto superior esquerdo) para ver todas as conversas
- Crie uma nova conversa clicando em "Nova Conversa"
- Exclua conversas antigas clicando no ícone de lixeira

#### Sugestões Contextuais
- O chatbot sugere perguntas relevantes baseadas na conversa
- Clique em uma sugestão para enviá-la rapidamente

## 🔧 API Endpoints

### Chat

**POST `/api/v1/chat/chat`**
Enviar uma mensagem e receber resposta da IA

```json
{
  "message": "Quais dispositivos estão offline?",
  "conversation_id": "uuid-opcional",
  "include_context": true
}
```

**GET `/api/v1/chat/conversations`**
Listar todas as conversas do usuário

**GET `/api/v1/chat/conversations/{conversation_id}`**
Obter uma conversa específica com todas as mensagens

**POST `/api/v1/chat/insights`**
Obter insights baseados em dados da plataforma

```json
{
  "query": "Análise de performance",
  "scope": "organization",
  "time_range": "24h"
}
```

## 🎨 Personalização

### Modificar o Modelo de IA

Você pode alterar o modelo usado pelo chatbot no arquivo `.env`:

```env
# Modelos disponíveis:
# - gpt-4-turbo-preview (mais inteligente, mais caro)
# - gpt-4 (inteligente, balanceado)
# - gpt-3.5-turbo (mais rápido, mais barato)
OPENAI_MODEL=gpt-4-turbo-preview
```

### Ajustar a Temperatura

A temperatura controla a criatividade das respostas (0.0 a 1.0):

```env
# 0.0 = Respostas mais determinísticas e focadas
# 1.0 = Respostas mais criativas e variadas
OPENAI_TEMPERATURE=0.7
```

### Modo Fallback (Sem OpenAI)

O chatbot funciona mesmo sem a chave da API OpenAI configurada! Neste caso, ele fornece:
- Respostas básicas baseadas em padrões
- Informações sobre o status dos dispositivos
- Dados de alarmes
- Navegação pela plataforma

Para ativar todas as funcionalidades de IA, configure a `OPENAI_API_KEY`.

## 🗄️ Estrutura do Banco de Dados

### Tabela: `conversations`
- `id`: UUID (chave primária)
- `user_id`: UUID (referência ao usuário)
- `organization_id`: UUID (referência à organização)
- `title`: String (título da conversa)
- `context`: JSON (contexto adicional)
- `created_at`: DateTime
- `updated_at`: DateTime

### Tabela: `messages`
- `id`: UUID (chave primária)
- `conversation_id`: UUID (referência à conversa)
- `role`: Enum ('user', 'assistant', 'system')
- `content`: Text (conteúdo da mensagem)
- `metadata`: JSON (metadados adicionais)
- `created_at`: DateTime

## 🔐 Segurança

- Todas as conversas são isoladas por usuário e organização
- As mensagens são armazenadas de forma segura no PostgreSQL
- A chave da API OpenAI é armazenada apenas no servidor
- Autenticação JWT é necessária para acessar o chatbot

## 🐛 Troubleshooting

### Erro: "OpenAI API key not configured"
- Verifique se a variável `OPENAI_API_KEY` está configurada no `.env`
- Reinicie o servidor backend após configurar

### Erro: "Failed to send message"
- Verifique se o backend está rodando
- Verifique a conexão com o banco de dados
- Verifique os logs do servidor

### Chatbot não responde
- Verifique sua cota de uso da API OpenAI
- Verifique se a chave da API é válida
- Tente usar o modo fallback (sem OPENAI_API_KEY)

## 📝 Licença

Este projeto é parte do OptiFlow AI Platform. Consulte o arquivo LICENSE para mais informações.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request.

## 📧 Suporte

Para suporte, entre em contato ou abra uma issue no repositório do projeto.
