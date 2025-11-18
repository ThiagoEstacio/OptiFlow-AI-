#!/bin/bash
# Bundle Analysis Script (PDCA #19)
#
# Analyzes frontend bundle size and generates visualization

set -e

echo "📦 OptiFlow Frontend Bundle Analyzer"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found. Running npm install..."
    npm install
fi

# Install visualization dependencies if needed
if ! npm list rollup-plugin-visualizer > /dev/null 2>&1; then
    echo "📥 Installing bundle analyzer dependencies..."
    npm install --save-dev rollup-plugin-visualizer
fi

# Build with analysis
echo ""
echo "🔍 Building with bundle analysis..."
ANALYZE=true npm run build

# Check build output
if [ -f "dist/stats.html" ]; then
    echo ""
    echo -e "${GREEN}✅ Bundle analysis complete!${NC}"
    echo ""
    echo "📊 Analysis report: dist/stats.html"
    echo ""

    # Get dist size
    DIST_SIZE=$(du -sh dist 2>/dev/null | cut -f1)
    echo -e "📦 Total dist size: ${YELLOW}${DIST_SIZE}${NC}"

    # Count chunks
    JS_CHUNKS=$(find dist/assets/js -name "*.js" 2>/dev/null | wc -l)
    echo -e "📄 JavaScript chunks: ${YELLOW}${JS_CHUNKS}${NC}"

    # Largest chunks
    echo ""
    echo "🔝 Largest chunks:"
    find dist/assets/js -name "*.js" -exec ls -lh {} \; 2>/dev/null | \
        awk '{print $5 "\t" $9}' | \
        sort -hr | \
        head -5

    echo ""
    echo -e "${GREEN}Opening analysis report in browser...${NC}"

    # Open in browser (cross-platform)
    if command -v xdg-open > /dev/null; then
        xdg-open dist/stats.html
    elif command -v open > /dev/null; then
        open dist/stats.html
    else
        echo "⚠️  Could not open browser automatically"
        echo "   Please open dist/stats.html manually"
    fi
else
    echo "❌ Analysis failed - stats.html not found"
    exit 1
fi

echo ""
echo "✨ Done!"
