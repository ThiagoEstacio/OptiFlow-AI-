# 🔐 OptiFlow AI - Credenciais de Acesso

## ✅ Frontend Funcionando

🌐 **URL**: http://localhost:3000

---

## 👤 Como Criar Usuário Administrador

### Opção 1: Registrar pela Interface Web

1. Acesse: http://localhost:3000
2. Na tela de login, procure por "Criar conta" ou "Sign up"
3. Preencha os dados:
   - **Email**: admin@optiflow.com
   - **Senha**: admin123 (ou sua preferência)
   - **Nome**: Administrador OptiFlow

### Opção 2: Usar Credenciais de Teste

Se o banco de dados já tiver dados, tente:

```
Email: admin@example.com
Senha: admin
```

ou

```
Email: user@example.com  
Senha: password
```

---

## 🔧 Resetar Banco de Dados (Se Necessário)

Para começar do zero com um banco limpo:

```bash
# 1. Parar todos os containers
./stop-all.sh

# 2. Remover volumes do banco de dados
docker volume rm optiflow-ai-_postgres_data

# 3. Reiniciar
./start-all.sh
```

---

## 📊 Status do Sistema

- ✅ Frontend: http://localhost:3000
- ✅ Backend API: http://localhost:8000
- ✅ Docs API: http://localhost:8000/docs
- ✅ Health Check: http://localhost:8000/health

---

## 🎉 Problema Resolvido!

A aplicação está **totalmente funcional**. O problema era incompatibilidade do módulo `prop-types` com Material-UI, que foi corrigido configurando o Vite para otimizar corretamente as dependências.

### Correções Aplicadas:
1. ✅ Rebuild do container frontend sem cache
2. ✅ Configuração do `optimizeDeps` no vite.config.ts
3. ✅ Adicionadas dependências MUI ao pre-bundling
4. ✅ Configurado ESBuild loader para JSX
5. ✅ Corrigidas variáveis de ambiente (localhost:8000)
