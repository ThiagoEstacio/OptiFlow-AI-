# 🔐 Credenciais de Acesso - OptiFlow AI Platform

**Data**: 2025-11-14
**Ambiente**: Desenvolvimento/Teste Local

---

## 👤 Usuário Administrador

### Login no Frontend (http://localhost:3000)

```
Email: admin@optiflow.com
Senha: admin
```

**Permissões**:
- ✅ Acesso total ao sistema
- ✅ Gerenciamento de usuários
- ✅ Configuração de gateways
- ✅ Visualização de todos os dashboards
- ✅ Acesso ao GraphQL Playground
- ✅ Gerenciamento de ML Models

---

## 🚪 Endpoints de Acesso

### Frontend
- **URL**: http://localhost:3000
- **Uso**: Interface web completa
- **Login**: Tela de login automática
- **Sem rate limit**: Login e autenticação liberados

### Backend API REST
- **URL**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/health
- **Login**: POST http://localhost:8000/api/v1/auth/login

### GraphQL API (PDCA #27)
- **URL**: http://localhost:8000/graphql
- **Playground**: Interface interativa
- **Sem autenticação** necessária para playground
- **Sem rate limit**: Endpoint liberado

### Monitoramento

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | Sem autenticação |
| **RabbitMQ** | http://localhost:15672 | guest / guest |
| **MLflow** | http://localhost:5000 | Sem autenticação |

---

## 🧪 Como Testar o Login

### Via Frontend (Recomendado)

1. Abra o navegador em: http://localhost:3000
2. Preencha o formulário:
   - Email: `admin@optiflow.com`
   - Senha: `admin`
3. Clique em "Sign In"
4. Você será redirecionado para o dashboard principal

### Via API (curl)

```bash
# Fazer login e obter token JWT
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=admin@optiflow.com" \
  --data-urlencode "password=admin"

# Resposta esperada:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Testar token obtido

```bash
# Use o token para acessar endpoint protegido
TOKEN="<seu_token_aqui>"

curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Resposta esperada:
{
  "id": "...",
  "email": "admin@optiflow.com",
  "full_name": "OptiFlow Admin",
  "role": "ADMIN",
  "is_active": true,
  "is_superuser": true
}
```

---

## ⚠️ Importante: Rate Limiting

Os seguintes endpoints **NÃO têm rate limiting** para facilitar testes:

- ✅ `/api/health`
- ✅ `/api/v1/health`
- ✅ `/api/v1/auth/login` ← **LOGIN**
- ✅ `/api/v1/auth/me` ← **USER INFO**
- ✅ `/graphql` ← **GRAPHQL API**
- ✅ `/docs` (Swagger UI)
- ✅ `/redoc` (ReDoc)

Todos os outros endpoints têm:
- **Limite**: 20 requisições por 60 segundos (por IP/usuário)
- **Headers**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

---

## 🔧 Troubleshooting de Login

### Erro: "Unable to connect to server"

**Causa**: Backend não está respondendo

**Solução**:
```bash
# Verificar se backend está rodando
docker ps | grep optiflow-backend

# Ver logs do backend
docker logs optiflow-backend --tail 50

# Reiniciar se necessário
docker restart optiflow-backend
```

### Erro: "Invalid credentials"

**Causa**: Senha incorreta

**Solução**:
- Verifique se está usando `admin` (minúsculas)
- Email correto: `admin@optiflow.com`

### Erro: "Rate limit exceeded"

**Causa**: Muitas tentativas de login

**Solução**:
- Aguarde 60 segundos
- O endpoint `/api/v1/auth/login` foi liberado do rate limit (após último fix)
- Reinicie o backend se o problema persistir

### Erro CORS

**Causa**: CORS mal configurado (já corrigido)

**Solução**:
- O fix de CORS já foi aplicado
- Se o erro persistir, limpe o cache do navegador (Ctrl+Shift+R)

---

## 📊 Dados de Teste

Após fazer login, você terá acesso a:

- **Dashboards**: Pré-configurados com dados sintéticos
- **Gateways**: Simuladores de OPC UA ativos
- **Tags**: Dados de timeseries em InfluxDB
- **Alarmes**: Eventos de alarme simulados
- **ML Models**: Modelos pré-treinados no MLflow

---

## 🎯 Próximos Passos Após Login

1. **Executive Dashboard**
   - Ver KPIs principais
   - Health Score dos assets
   - ROI e savings

2. **ML Insights**
   - Predições de falha
   - Anomalias detectadas
   - Drift de modelos

3. **Gateway Management**
   - Status dos gateways OPC UA
   - Configuração de devices

4. **Dashboard Builder**
   - Criar dashboards personalizados
   - Drag & drop de widgets

5. **GraphQL Playground**
   - http://localhost:8000/graphql
   - Testar queries otimizadas (PDCA #27)

---

**✅ Sistema pronto para acesso! Basta fazer login e explorar todas as funcionalidades.**
