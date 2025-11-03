# AI Assistant - Configuração

## 🤖 Funcionalidades do AI Assistant

O OptiFlow AI Assistant é um chatbot inteligente que:

- ✅ **Consulta tags em tempo real** - Acessa valores atuais de sensores e dispositivos
- ✅ **Analisa dados históricos** - Examina tendências e padrões ao longo do tempo
- ✅ **Assistente de processo** - Fornece insights sobre otimização industrial
- ✅ **Troubleshooting** - Ajuda a diagnosticar problemas em equipamentos
- ✅ **Recomendações** - Sugere melhorias baseadas em dados

## 🔑 Configuração da API OpenAI

### Modo Demo (Sem OpenAI)

O chatbot funciona em **modo demo** sem necessidade de chave API:
- Respostas simuladas para testes
- Funcionalidade completa da interface
- Ideal para desenvolvimento e demonstração

### Modo Completo (Com OpenAI)

Para ativar a IA completa com ChatGPT:

1. **Obtenha uma chave API da OpenAI:**
   - Acesse: https://platform.openai.com/api-keys
   - Crie uma conta ou faça login
   - Gere uma nova chave API
   - Copie a chave (começa com `sk-...`)

2. **Configure no Docker:**

   Edite o arquivo `docker-compose.yml` e adicione:

   ```yaml
   backend:
     environment:
       - OPENAI_API_KEY=sk-sua-chave-aqui
       - OPENAI_MODEL=gpt-4-turbo-preview  # ou gpt-3.5-turbo para economia
       - OPENAI_MAX_TOKENS=1000
       - OPENAI_TEMPERATURE=0.7
   ```

3. **Reinicie o backend:**

   ```bash
   sudo docker compose restart backend
   ```

## 📊 Integração com Tags

O AI Assistant pode:

### Consultar Valores em Tempo Real

```
Usuário: "Qual o valor atual da Balança 1?"
AI: "A Balança 1 (RCV_SCALE_01_WEIGHT) está marcando 32,450 kg atualmente."
```

### Analisar Histórico

```
Usuário: "Mostre o histórico da Moega 1 nas últimas 24 horas"
AI: "A Moega 1 (RCV_HOPPER_01_LEVEL) teve as seguintes variações..."
```

### Fornecer Insights

```
Usuário: "Por que a fila de caminhões está alta?"
AI: "Analisando os dados, identifiquei que a Balança 2 está com tempo de pesagem 
     30% acima do normal, causando o acúmulo..."
```

## 🛠️ Funcionalidades Técnicas

### Endpoints Disponíveis

- **`POST /api/v1/chat/chat/demo`** - Chat sem autenticação (modo demo)
- **`POST /api/v1/chat/chat`** - Chat autenticado (persiste conversas)
- **`GET /api/v1/chat/conversations`** - Lista conversas do usuário
- **`POST /api/v1/chat/insights`** - Gera insights baseados em dados

### Contexto Automático

O AI tem acesso a:
- Lista completa de tags e seus valores
- Histórico de alarmes
- Status de dispositivos
- Métricas de performance

### Modelos Disponíveis

| Modelo | Descrição | Custo |
|--------|-----------|-------|
| `gpt-4-turbo-preview` | Mais inteligente, melhor para análises complexas | Alto |
| `gpt-4` | Muito capaz, balanceado | Médio-Alto |
| `gpt-3.5-turbo` | Rápido e econômico, bom para consultas simples | Baixo |

## 🔍 Exemplo de Uso

### 1. Modo Demo (Atual)

```typescript
// Frontend automaticamente usa /chat/demo se não houver token
await chatApiClient.sendMessage({
  message: "Qual o status do sistema?",
  include_context: true
});
```

### 2. Modo Autenticado

```typescript
// Com token de autenticação, usa /chat
localStorage.setItem('auth_token', 'seu-token-jwt');
await chatApiClient.sendMessage({
  message: "Analise a eficiência das balanças",
  conversation_id: "uuid-da-conversa",  // opcional
  include_context: true
});
```

## 🚀 Próximos Passos

1. **Configurar OpenAI API Key** para IA completa
2. **Implementar autenticação** para salvar conversas
3. **Adicionar análise de trends** automática
4. **Integrar com sistema de alarmes** para notificações proativas

## 📝 Notas

- O modo demo **não** requer chave API da OpenAI
- Sem chave API, o chatbot retorna respostas simuladas úteis
- Com chave API, obtém inteligência completa do ChatGPT
- Custos da API OpenAI variam por modelo e uso
- Recomendado: começar com `gpt-3.5-turbo` para testes

## 🐛 Troubleshooting

**Erro 401 Unauthorized:**
- Solução: O endpoint demo (`/chat/demo`) não requer autenticação
- Frontend agora usa automaticamente o endpoint correto

**AI não responde:**
- Verifique se `OPENAI_API_KEY` está configurada
- Veja logs do backend: `sudo docker compose logs backend | grep -i openai`
- Modo demo funciona sem chave

**Respostas genéricas:**
- Ative `include_context: true` nas requisições
- Verifique se tags estão sendo enviadas no contexto
