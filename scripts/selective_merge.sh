#!/bin/bash
# ==============================================================================
# OptiFlow AI - Selective Merge Script
# ==============================================================================
# Este script facilita o merge seletivo de features da branch
# merged-chatbot-features para a branch principal
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SOURCE_BRANCH="claude/merged-chatbot-features-011CUdj4zT6jFFR2nKHsykcK"
TARGET_BRANCH=$(git branch --show-current)
BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"

# ==============================================================================
# Helper Functions
# ==============================================================================

print_header() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=====================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]: ${NC})" -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# ==============================================================================
# Pre-flight Checks
# ==============================================================================

preflight_checks() {
    print_header "Pre-flight Checks"

    # Check if git repo
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not a git repository!"
        exit 1
    fi
    print_success "Git repository detected"

    # Check if source branch exists
    if ! git show-ref --verify --quiet refs/remotes/origin/$SOURCE_BRANCH; then
        print_error "Source branch $SOURCE_BRANCH not found!"
        exit 1
    fi
    print_success "Source branch exists"

    # Check for uncommitted changes
    if [[ -n $(git status -s) ]]; then
        print_warning "You have uncommitted changes!"
        if ! confirm "Continue anyway?"; then
            exit 0
        fi
    fi
    print_success "Working directory clean"

    echo ""
}

# ==============================================================================
# Backup Current Branch
# ==============================================================================

create_backup() {
    print_header "Creating Backup"

    git branch $BACKUP_BRANCH
    print_success "Backup created: $BACKUP_BRANCH"
    print_info "To restore: git checkout $BACKUP_BRANCH"

    echo ""
}

# ==============================================================================
# Feature Selection Menu
# ==============================================================================

show_menu() {
    print_header "Select Features to Merge"

    echo "1) 🏷️  Tag Labels System (RECOMMENDED - Quick Win)"
    echo "2) 📊 InfluxDB Optimizations (RECOMMENDED - Performance)"
    echo "3) 🤖 AI Autonomous Agent (HIGH VALUE - Complex)"
    echo "4) 🎨 Frontend Pages - Insights (NEW - Medium)"
    echo "5) 🎨 Frontend Pages - Tag Labels Management (NEW - Medium)"
    echo "6) 🎨 Frontend Pages - All Updates (CAREFUL - Review needed)"
    echo "7) 🚢 SmartPort Simulator (OPTIONAL - Specific use case)"
    echo "8) 📡 OPC-UA Server (OPTIONAL - Specific use case)"
    echo ""
    echo "9) ⚡ Quick Win Bundle (1 + 2)"
    echo "10) 🚀 Full Recommended (1 + 2 + 3 + 4 + 5)"
    echo ""
    echo "0) Exit"
    echo ""
}

# ==============================================================================
# Merge Functions
# ==============================================================================

merge_tag_labels() {
    print_header "Merging Tag Labels System"

    local files=(
        "backend/models/tag_label.py"
        "backend/api/tag_labels.py"
        "backend/services/tag_label_service.py"
    )

    for file in "${files[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_info "Don't forget to run database migrations!"
    echo "  alembic revision --autogenerate -m 'Add tag_labels table'"
    echo "  alembic upgrade head"
    echo ""
}

merge_influxdb_optimizations() {
    print_header "Merging InfluxDB Optimizations"

    local files=(
        "backend/services/influxdb_service.py"
        "backend/config/influxdb_config.py"
    )

    for file in "${files[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_info "Update your .env with:"
    echo "  INFLUXDB_BATCH_SIZE=1000"
    echo "  INFLUXDB_FLUSH_INTERVAL=5"
    echo ""
}

merge_ai_agent() {
    print_header "Merging AI Autonomous Agent"

    local files=(
        "backend/services/autonomous_insights.py"
        "backend/services/llm_tools/base_tool.py"
        "backend/services/llm_tools/tag_search.py"
        "backend/services/llm_tools/historical_query.py"
        "backend/services/llm_tools/correlation_finder.py"
        "backend/services/llm_tools/pattern_detector.py"
        "backend/data/industry_knowledge.txt"
        "backend/tests/test_autonomous_agent.py"
        "backend/tests/test_trained_agent.py"
    )

    for file in "${files[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            mkdir -p $(dirname $file)
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_info "Install required dependencies:"
    echo "  pip install anthropic==0.34.0 langchain==0.2.14"
    echo ""
    print_info "Update your .env with:"
    echo "  LLM_PROVIDER=anthropic"
    echo "  LLM_MODEL=claude-3-5-sonnet-20241022"
    echo "  ANTHROPIC_API_KEY=your_key_here"
    echo "  AGENT_MONITORING_INTERVAL=60"
    echo "  AGENT_ENABLE_AUTO_INSIGHTS=true"
    echo ""
}

merge_frontend_insights() {
    print_header "Merging Frontend - Insights Page"

    local files=(
        "frontend/src/pages/InsightsPage.tsx"
        "frontend/src/components/insights/InsightCard.tsx"
        "frontend/src/components/insights/InsightsList.tsx"
    )

    for file in "${files[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            mkdir -p $(dirname $file)
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_info "Update App.tsx routing to include Insights page"
    echo ""
}

merge_frontend_tag_labels() {
    print_header "Merging Frontend - Tag Labels Page"

    local files=(
        "frontend/src/pages/TagLabelsPage.tsx"
        "frontend/src/components/tags/TagLabelManager.tsx"
    )

    for file in "${files[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            mkdir -p $(dirname $file)
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_info "Update App.tsx routing to include Tag Labels page"
    echo ""
}

merge_frontend_all() {
    print_header "Merging All Frontend Updates"

    print_warning "This will merge all 17 frontend pages!"
    if ! confirm "Are you sure?"; then
        return
    fi

    local pages=(
        "frontend/src/pages/Dashboard.tsx"
        "frontend/src/pages/DevicesPage.tsx"
        "frontend/src/pages/TagsPage.tsx"
        "frontend/src/pages/TagDetailsPage.tsx"
        "frontend/src/pages/InsightsPage.tsx"
        "frontend/src/pages/TagLabelsPage.tsx"
        "frontend/src/pages/VisualizationShowcase.tsx"
    )

    for file in "${pages[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_warning "Review each file for conflicts and redundancies!"
    echo ""
}

merge_smartport_simulator() {
    print_header "Merging SmartPort Simulator"

    print_warning "This is a large feature specific to grain terminals!"
    if ! confirm "Continue?"; then
        return
    fi

    local files=(
        "simulators/smartport_bulk_terminal_simulator.py"
        "simulators/opcua_server.py"
        "simulators/setup_smartport_tags.py"
        "docs/SMARTPORT_SETUP_GUIDE.md"
    )

    for file in "${files[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            mkdir -p $(dirname $file)
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_info "Install dependencies:"
    echo "  pip install opcua pymunk numpy"
    echo ""
}

merge_opcua_server() {
    print_header "Merging OPC-UA Server"

    local files=(
        "simulators/opcua_server.py"
        "backend/integrations/opcua_client.py"
    )

    for file in "${files[@]}"; do
        if git show $SOURCE_BRANCH:$file > /dev/null 2>&1; then
            mkdir -p $(dirname $file)
            git checkout $SOURCE_BRANCH -- $file
            print_success "Merged: $file"
        else
            print_warning "File not found: $file"
        fi
    done

    print_info "Install dependencies:"
    echo "  pip install opcua"
    echo ""
}

# ==============================================================================
# Bundle Merges
# ==============================================================================

merge_quick_win_bundle() {
    print_header "Quick Win Bundle"
    print_info "Merging: Tag Labels + InfluxDB Optimizations"
    echo ""

    merge_tag_labels
    merge_influxdb_optimizations

    print_success "Quick Win Bundle merged successfully!"
    echo ""
}

merge_full_recommended() {
    print_header "Full Recommended Bundle"
    print_info "Merging: Tag Labels + InfluxDB + AI Agent + Frontend (Insights + Tag Labels)"
    echo ""

    merge_tag_labels
    merge_influxdb_optimizations
    merge_ai_agent
    merge_frontend_insights
    merge_frontend_tag_labels

    print_success "Full Recommended Bundle merged successfully!"
    echo ""
}

# ==============================================================================
# Post-merge Actions
# ==============================================================================

post_merge_actions() {
    print_header "Post-Merge Actions"

    # Stage changes
    print_info "Staging changes..."
    git add .

    # Show status
    print_info "Current status:"
    git status --short
    echo ""

    # Commit prompt
    if confirm "Commit these changes?"; then
        read -p "Enter commit message: " commit_msg
        git commit -m "$commit_msg"
        print_success "Changes committed!"
    else
        print_warning "Changes staged but not committed"
        print_info "Review and commit manually when ready"
    fi

    echo ""
    print_header "Next Steps"
    echo "1. Run tests: pytest && npm test"
    echo "2. Check for conflicts or issues"
    echo "3. Update documentation if needed"
    echo "4. Run database migrations (if applicable)"
    echo "5. Update .env with new configuration"
    echo "6. Test locally before pushing"
    echo ""

    if [[ -n $(git status -s) ]]; then
        print_info "To undo all changes: git checkout $TARGET_BRANCH && git reset --hard $BACKUP_BRANCH"
    fi
}

# ==============================================================================
# Main Interactive Loop
# ==============================================================================

main() {
    print_header "OptiFlow AI - Selective Merge Tool"
    echo "Source: $SOURCE_BRANCH"
    echo "Target: $TARGET_BRANCH"
    echo ""

    preflight_checks
    create_backup

    while true; do
        show_menu
        read -p "Select option: " choice
        echo ""

        case $choice in
            1) merge_tag_labels ;;
            2) merge_influxdb_optimizations ;;
            3) merge_ai_agent ;;
            4) merge_frontend_insights ;;
            5) merge_frontend_tag_labels ;;
            6) merge_frontend_all ;;
            7) merge_smartport_simulator ;;
            8) merge_opcua_server ;;
            9) merge_quick_win_bundle ;;
            10) merge_full_recommended ;;
            0)
                print_info "Exiting..."
                if [[ -n $(git status -s) ]]; then
                    post_merge_actions
                fi
                exit 0
                ;;
            *)
                print_error "Invalid option!"
                ;;
        esac

        if confirm "Continue merging more features?"; then
            continue
        else
            post_merge_actions
            break
        fi
    done
}

# ==============================================================================
# Script Entry Point
# ==============================================================================

main "$@"
