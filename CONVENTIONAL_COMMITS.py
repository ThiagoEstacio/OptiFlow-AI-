"""
Conventional Commits - Guia de Referência Rápida
=================================================

Sistema de commits padronizado para controle de mudanças e geração de CHANGELOG

Autor: OptiFlow AI Team
Data: 2025-11-10
Referência: https://www.conventionalcommits.org/
"""

# ============================================================================
# FORMATO BÁSICO
# ============================================================================

"""
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé opcional]

Exemplo:
feat(gateway): adiciona auto-discovery de tags OPC-UA

Implementa descoberta automática de tags usando OPC-UA browser.
Suporta filtragem por namespace e padrões de nome.

BREAKING CHANGE: Remove método manual de configuração de tags
Refs: #123
Closes: #456
"""


# ============================================================================
# TIPOS DE COMMIT
# ============================================================================

COMMIT_TYPES = {
    # Mudanças que afetam usuários
    "feat": {
        "description": "Nova funcionalidade",
        "examples": [
            "feat: adiciona endpoint de descoberta OPC-UA",
            "feat(api): implementa autenticação JWT",
            "feat(gateway): adiciona suporte a Modbus TCP",
        ],
        "changelog": "✅ Features"
    },
    
    "fix": {
        "description": "Correção de bug",
        "examples": [
            "fix: corrige erro 1006 em WebSocket",
            "fix(gateway): corrige await em propriedade is_connected",
            "fix(ui): corrige crash ao carregar dashboard vazio",
        ],
        "changelog": "🐛 Bug Fixes"
    },
    
    # Mudanças que não afetam comportamento
    "refactor": {
        "description": "Refatoração de código",
        "examples": [
            "refactor: extrai lógica de alarmes para service",
            "refactor(gateway): simplifica conexão OPC-UA",
        ],
        "changelog": "♻️ Code Refactoring"
    },
    
    "perf": {
        "description": "Melhoria de performance",
        "examples": [
            "perf: otimiza query de tags com índice",
            "perf(kafka): adiciona compressão LZ4",
        ],
        "changelog": "⚡ Performance Improvements"
    },
    
    # Documentação e testes
    "test": {
        "description": "Adiciona ou modifica testes",
        "examples": [
            "test: adiciona testes unitários para AlarmManager",
            "test(gateway): adiciona testes de integração OPC-UA",
        ],
        "changelog": "✅ Tests"
    },
    
    "docs": {
        "description": "Documentação",
        "examples": [
            "docs: atualiza README com guia TDD",
            "docs(api): adiciona exemplos de uso",
        ],
        "changelog": "📚 Documentation"
    },
    
    # Configuração e build
    "build": {
        "description": "Mudanças no sistema de build",
        "examples": [
            "build: atualiza dependências do frontend",
            "build(docker): otimiza imagem do gateway",
        ],
        "changelog": "🏗️ Build System"
    },
    
    "ci": {
        "description": "Mudanças em CI/CD",
        "examples": [
            "ci: adiciona GitHub Actions para testes",
            "ci: configura deploy automático",
        ],
        "changelog": "👷 Continuous Integration"
    },
    
    "chore": {
        "description": "Tarefas de manutenção",
        "examples": [
            "chore: atualiza dependências",
            "chore: remove código comentado",
        ],
        "changelog": "🔧 Chores"
    },
    
    # Estilo
    "style": {
        "description": "Formatação (não afeta lógica)",
        "examples": [
            "style: formata código com black",
            "style(frontend): aplica prettier",
        ],
        "changelog": "💄 Styles"
    },
}


# ============================================================================
# BREAKING CHANGES
# ============================================================================

"""
Para mudanças que quebram compatibilidade:

1. Adicionar ! após o tipo:
   feat!: remove suporte a Python 3.8

2. Ou adicionar BREAKING CHANGE no rodapé:
   feat: migra para FastAPI 0.100

   BREAKING CHANGE: Endpoint /api/tags agora requer autenticação
"""


# ============================================================================
# ESCOPOS COMUNS
# ============================================================================

COMMON_SCOPES = [
    # Backend
    "api", "auth", "models", "services", "database", "kafka", "influxdb",
    
    # Gateway
    "gateway", "opcua", "modbus", "mqtt", "protocols",
    
    # Frontend
    "ui", "dashboard", "components", "store", "api-client",
    
    # Infraestrutura
    "docker", "ci", "deploy", "monitoring",
    
    # Documentação
    "docs", "readme", "api-docs",
]


# ============================================================================
# TEMPLATES DE COMMIT
# ============================================================================

def commit_template_new_feature():
    """Template para nova funcionalidade"""
    return """
feat(gateway): adiciona descoberta automática de tags OPC-UA

Implementa OPCUABrowser para descobrir tags automaticamente:
- Conecta ao servidor OPC-UA
- Lista todos os namespaces
- Descobre tags recursivamente
- Suporta filtragem por namespace e padrão

Permite operação sem configuração manual de tags, similar ao
KEPServerEX.

Tests: ✅ 5/5 passed
Performance: Descobre 1000+ tags em <3s
Closes: #123
    """.strip()


def commit_template_bug_fix():
    """Template para correção de bug"""
    return """
fix(gateway): corrige memory leak em conexão OPC-UA

Adiciona cleanup correto de recursos:
- Desconecta client ao destruir objeto
- Libera subscriptions antes de fechar
- Remove listeners de eventos

Problema identificado através de testes de stress com 
10h+ de operação contínua.

Fixes: #456
Tests: ✅ Passed após 24h de teste
Memory: Estável em 150MB (antes: crescendo 10MB/h)
    """.strip()


def commit_template_refactor():
    """Template para refatoração"""
    return """
refactor(services): extrai lógica de alarmes para AlarmManager

Separa responsabilidades:
- AlarmManager gerencia criação e estado de alarmes
- AlarmEvaluator avalia condições e thresholds
- AlarmNotifier envia notificações

Facilita testes unitários e manutenção futura.

Tests: ✅ 15/15 passed (mantidos)
Coverage: 95% (antes: 78%)
Refs: #789
    """.strip()


def commit_template_breaking_change():
    """Template para mudança breaking"""
    return """
feat!: migra autenticação para OAuth2 + JWT

Substitui autenticação simples por OAuth2:
- Adiciona refresh tokens
- Suporte a múltiplos providers (Google, Azure AD)
- Tokens com expiração configurável

BREAKING CHANGE: 
- Endpoint /api/login agora é /api/auth/token
- Header Authorization agora requer formato "Bearer <token>"
- Variável de ambiente AUTH_SECRET foi renomeada para JWT_SECRET

Migration Guide: docs/migration/auth-oauth2.md
Tests: ✅ 25/25 passed
Closes: #1001
    """.strip()


# ============================================================================
# COMANDOS GIT ÚTEIS
# ============================================================================

GIT_COMMANDS = """
# Commit simples
git commit -m "feat: adiciona nova funcionalidade"

# Commit com corpo e rodapé
git commit -m "feat: adiciona funcionalidade" \\
           -m "Corpo do commit com detalhes" \\
           -m "Closes: #123"

# Alterar último commit (adicionar mais arquivos ou mudar mensagem)
git commit --amend

# Commit interativo (permite escrever mensagem longa)
git commit

# Ver histórico de commits
git log --oneline --graph

# Ver mudanças de um commit específico
git show <commit-hash>

# Buscar commits por mensagem
git log --grep="fix"

# Buscar commits por autor
git log --author="seu-nome"

# Ver commits que afetaram arquivo específico
git log -- path/to/file
"""


# ============================================================================
# GERANDO CHANGELOG AUTOMATICAMENTE
# ============================================================================

"""
Usando conventional-changelog:

# Instalar
npm install -g conventional-changelog-cli

# Gerar CHANGELOG.md
conventional-changelog -p angular -i CHANGELOG.md -s

# Ou usar standard-version para release automatizado
npm install -g standard-version
standard-version

Resultado em CHANGELOG.md:
==========================

# Changelog

## [1.2.0] - 2025-11-10

### ✅ Features
- **gateway**: adiciona descoberta automática de tags OPC-UA (#123)
- **api**: implementa autenticação JWT (#124)

### 🐛 Bug Fixes
- **gateway**: corrige memory leak em conexão OPC-UA (#456)
- **ui**: corrige crash ao carregar dashboard vazio (#457)

### ♻️ Code Refactoring
- **services**: extrai lógica de alarmes para AlarmManager (#789)

### ⚡ Performance Improvements
- **kafka**: adiciona compressão LZ4 (#790)

### 📚 Documentation
- **readme**: atualiza guia de instalação (#791)
"""


# ============================================================================
# VALIDAÇÃO DE COMMITS (Pre-commit Hook)
# ============================================================================

COMMIT_MSG_HOOK = """
#!/bin/bash
# .git/hooks/commit-msg

commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# Regex para validar formato conventional commit
pattern="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\\(.+\\))?!?: .{1,100}$"

if ! echo "$commit_msg" | head -1 | grep -qE "$pattern"; then
    echo "❌ Commit message inválido!"
    echo ""
    echo "Formato esperado:"
    echo "  <tipo>[escopo opcional]: <descrição>"
    echo ""
    echo "Tipos válidos:"
    echo "  feat, fix, docs, style, refactor, perf, test, build, ci, chore"
    echo ""
    echo "Exemplos:"
    echo "  feat: adiciona nova funcionalidade"
    echo "  fix(gateway): corrige bug de conexão"
    echo "  docs: atualiza README"
    echo ""
    exit 1
fi

echo "✅ Commit message válido"
exit 0
"""


# ============================================================================
# INSTALAÇÃO DO HOOK
# ============================================================================

def install_commit_hook():
    """Instala hook de validação de commits"""
    import os
    import stat
    
    hook_path = ".git/hooks/commit-msg"
    
    # Criar arquivo de hook
    with open(hook_path, 'w') as f:
        f.write(COMMIT_MSG_HOOK)
    
    # Tornar executável
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
    
    print("✅ Commit hook instalado em .git/hooks/commit-msg")
    print("   Commits agora serão validados automaticamente!")


# ============================================================================
# EXEMPLOS DO PROJETO OPTIFLOW AI
# ============================================================================

OPTIFLOW_EXAMPLES = """
# Features
feat(gateway): adiciona auto-discovery de tags OPC-UA
feat(api): implementa endpoint de análise de alarmes
feat(ui): adiciona dashboard de manutenção preditiva
feat(kafka): implementa streaming de dados em tempo real

# Bug Fixes
fix(gateway): corrige await em propriedade is_connected
fix(websocket): corrige erro 1006 em conexão
fix(ui): corrige undefined reading em SystemOverview
fix(influxdb): corrige escrita de valores NaN

# Refactoring
refactor(gateway): remove configurações hardcoded
refactor(services): separa lógica de negócio de apresentação
refactor(opcua): simplifica browser de tags

# Performance
perf(gateway): otimiza descoberta de 1000+ tags
perf(kafka): adiciona compressão LZ4
perf(influxdb): adiciona batch write de 500 pontos

# Tests
test(gateway): adiciona testes unitários para device manager
test(api): adiciona testes de integração para endpoints
test(e2e): adiciona testes de fluxo completo de dados

# Documentation
docs: adiciona guia TDD completo
docs(api): atualiza documentação OpenAPI
docs: adiciona exemplos de uso da API

# Infrastructure
build(docker): otimiza imagens para produção
ci: adiciona GitHub Actions para testes automatizados
chore: atualiza dependências para versões LTS
"""


if __name__ == "__main__":
    print("=" * 70)
    print("CONVENTIONAL COMMITS - GUIA DE REFERÊNCIA")
    print("=" * 70)
    print()
    print("Tipos de commit:")
    for tipo, info in COMMIT_TYPES.items():
        print(f"  {tipo:12s} - {info['description']}")
    print()
    print("Instalando commit hook...")
    install_commit_hook()
