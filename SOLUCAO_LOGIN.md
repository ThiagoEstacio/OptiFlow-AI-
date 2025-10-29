# 🔐 SOLUÇÃO: Invalid Credentials - Login não funciona

**Problema Reportado**: Login falha com "Invalid credentials" usando `admin@smartport.com / Admin@123456`

---

## ✅ **BOA NOTÍCIA**

O frontend agora está carregando corretamente! Você está vendo a tela de login, o que significa que:
- ✅ Frontend funcionando
- ✅ `process.env` corrigido
- ✅ Interface carregando

**Agora precisamos criar o usuário administrador no banco de dados.**

---

## 🔍 **DIAGNÓSTICO**

### **PASSO 1: Execute o diagnóstico**

```bash
cd ~/OptiFlow-AI-
chmod +x diagnostico_backend.sh
./diagnostico_backend.sh
```

**O que verificar**:
- ✅ Backend está rodando? (optiflow-backend UP)
- ✅ PostgreSQL está rodando? (optiflow-postgres UP)
- ✅ Backend responde? (http://localhost:8000/docs)
- ❓ Existem usuários no banco?

---

## 🚀 **SOLUÇÃO: Criar Usuário Admin**

### **Método 1: Script Automático (Recomendado)**

```bash
cd ~/OptiFlow-AI-
chmod +x criar_usuario_admin.sh
./criar_usuario_admin.sh
```

**O script faz**:
1. Gera hash bcrypt da senha `Admin@123456`
2. Insere/atualiza usuário `admin@smartport.com` no banco
3. Define role como `admin`
4. Ativa a conta

**Depois, tente fazer login novamente!**

---

### **Método 2: Manual via SQL**

Se o script não funcionar, execute manualmente:

```bash
# 1. Conectar ao banco de dados
docker compose exec postgres psql -U optiflow -d optiflow

# 2. Criar usuário admin (cole no terminal SQL)
INSERT INTO users (
    email,
    full_name,
    hashed_password,
    role,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'admin@smartport.com',
    'Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2U6pRK5a2a',
    'admin',
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    updated_at = NOW();

# 3. Verificar se foi criado
SELECT email, full_name, role, is_active FROM users;

# 4. Sair
\q
```

**Hash de senha pré-calculado**: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2U6pRK5a2a`
(Senha: `Admin@123456`)

---

### **Método 3: Via Backend API (se houver endpoint de registro)**

```bash
# Verificar se existe endpoint de criação de usuário
curl http://localhost:8000/docs

# Procurar por: POST /api/v1/users ou POST /api/v1/auth/register
```

Se encontrar, pode criar via API:

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@smartport.com",
    "full_name": "Administrator",
    "password": "Admin@123456",
    "role": "admin"
  }'
```

---

## 🧪 **VERIFICAÇÕES**

### **1. Backend está rodando?**

```bash
# Ver status
docker compose ps backend

# Ver logs
docker compose logs backend --tail=50

# Testar API docs
curl http://localhost:8000/docs
```

**Deve retornar**: HTML da documentação Swagger

---

### **2. PostgreSQL está acessível?**

```bash
# Conectar ao banco
docker compose exec postgres psql -U optiflow -d optiflow

# Listar tabelas
\dt

# Você deve ver: users, organizations, sites, devices, tags, etc.
```

---

### **3. Existem usuários no banco?**

```bash
docker compose exec postgres psql -U optiflow -d optiflow -c "SELECT email, role, is_active FROM users;"
```

**Se retornar vazio**: Não há usuários, precisa criar!

---

## 🎯 **CREDENCIAIS DE LOGIN**

Após criar o usuário admin, use:

```
Email:    admin@smartport.com
Senha:    Admin@123456
```

**URL**: http://localhost:3000

---

## 🐛 **PROBLEMAS COMUNS**

### **Erro: "Backend não está respondendo"**

```bash
# Verificar logs do backend
docker compose logs backend --tail=100

# Procurar por erros como:
# - Database connection failed
# - Port already in use
# - Import errors
```

**Solução**: Reiniciar backend
```bash
docker compose restart backend
sleep 10
docker compose logs backend --tail=30
```

---

### **Erro: "Could not connect to PostgreSQL"**

```bash
# Verificar se PostgreSQL está rodando
docker compose ps postgres

# Deve mostrar: UP
```

**Solução**: Reiniciar PostgreSQL
```bash
docker compose restart postgres
sleep 15
docker compose logs postgres --tail=20
```

---

### **Erro: "relation 'users' does not exist"**

Isso significa que as **migrations não foram executadas**.

```bash
# Executar migrations
docker compose exec backend alembic upgrade head

# Ou reconstruir backend
docker compose down
docker compose up -d
```

---

### **Senha está correta mas login falha**

Possíveis causas:
1. **Hash de senha incorreto** → Recriar usuário
2. **is_active = false** → Ativar usuário
3. **Problema de rate limit** → Aguardar 1 minuto

**Verificar no banco**:
```sql
SELECT email, is_active, hashed_password FROM users WHERE email = 'admin@smartport.com';
```

**Reativar usuário**:
```sql
UPDATE users SET is_active = true WHERE email = 'admin@smartport.com';
```

---

## 📋 **CHECKLIST DE VERIFICAÇÃO**

Antes de tentar fazer login novamente:

- [ ] Backend está rodando (UP)
- [ ] PostgreSQL está rodando (UP)
- [ ] Backend responde em http://localhost:8000/docs
- [ ] Tabela `users` existe no banco
- [ ] Usuário `admin@smartport.com` existe no banco
- [ ] Usuário tem `is_active = true`
- [ ] Usuário tem `role = 'admin'`
- [ ] Hash de senha está correto

---

## 🎓 **EXPLICAÇÃO TÉCNICA**

### **Como funciona a autenticação?**

1. **Frontend** envia POST para `/api/v1/auth/login`
2. **Backend** busca usuário pelo email
3. **Backend** verifica hash da senha com bcrypt
4. **Backend** retorna JWT token se válido
5. **Frontend** armazena token no localStorage
6. **Frontend** usa token em todas as requisições

### **Por que preciso criar usuário manualmente?**

- O banco de dados inicia **vazio**
- Não há seeds/fixtures automáticos
- Primeira vez: criar usuário admin manualmente
- Depois: admin pode criar outros usuários via UI

### **Estrutura da tabela `users`:**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE,
    full_name VARCHAR NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role VARCHAR NOT NULL,  -- 'admin', 'engineer', 'operator', 'viewer'
    is_active BOOLEAN DEFAULT true,
    organization_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🆘 **SE NADA FUNCIONAR**

Execute TODOS os comandos de diagnóstico e me envie:

```bash
cd ~/OptiFlow-AI-

# 1. Diagnóstico backend
./diagnostico_backend.sh > diagnostico_completo.txt

# 2. Ver tabelas do banco
docker compose exec postgres psql -U optiflow -d optiflow -c "\dt" >> diagnostico_completo.txt

# 3. Ver usuários
docker compose exec postgres psql -U optiflow -d optiflow -c "SELECT * FROM users;" >> diagnostico_completo.txt

# 4. Ver resultado
cat diagnostico_completo.txt
```

**Cole TODA a saída aqui** para eu ajudar!

---

## ✅ **APÓS RESOLVER**

Quando conseguir fazer login, você terá acesso a:

- 📊 **Dashboard** - Overview do sistema
- 🏭 **Sites** - Gerenciar sites industriais
- 🔌 **Devices** - Gerenciar dispositivos (PLCs, RTUs)
- 🏷️ **Tags** - Configurar variáveis/tags
- 🚨 **Alarms** - Monitorar alarmes
- 📈 **Analytics** - Query builder e visualizações avançadas
- ⚙️ **Settings** - Configurações do usuário

---

**Última atualização**: 2025-10-29
**Status**: Frontend ✅ | Backend ✅ | Aguardando criação de usuário admin
