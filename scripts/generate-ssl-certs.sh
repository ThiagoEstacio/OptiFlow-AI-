#!/bin/bash
# ===========================================
# OptiFlow AI Platform - SSL Certificate Generator
# ===========================================
#
# This script generates SSL certificates for OptiFlow.
#
# Options:
#   1. Self-signed (development/testing)
#   2. Let's Encrypt (production with certbot)
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_ROOT/nginx/ssl"
CERTBOT_DIR="$PROJECT_ROOT/certbot"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "================================================"
echo "  OptiFlow AI Platform - SSL Certificate Setup"
echo "================================================"
echo -e "${NC}"

# Create directories
mkdir -p "$SSL_DIR"
mkdir -p "$CERTBOT_DIR/www"
mkdir -p "$CERTBOT_DIR/conf"

usage() {
    echo "Usage: $0 [self-signed|letsencrypt] [domain]"
    echo ""
    echo "Options:"
    echo "  self-signed    Generate self-signed certificates (for dev/testing)"
    echo "  letsencrypt    Use Let's Encrypt for production certificates"
    echo ""
    echo "Examples:"
    echo "  $0 self-signed"
    echo "  $0 letsencrypt optiflow.example.com"
    exit 1
}

generate_self_signed() {
    echo -e "${YELLOW}Generating self-signed SSL certificates...${NC}"

    DOMAIN=${1:-localhost}

    # Generate private key
    openssl genrsa -out "$SSL_DIR/privkey.pem" 2048

    # Generate self-signed certificate
    openssl req -new -x509 \
        -key "$SSL_DIR/privkey.pem" \
        -out "$SSL_DIR/fullchain.pem" \
        -days 365 \
        -subj "/C=BR/ST=State/L=City/O=OptiFlow/OU=Development/CN=$DOMAIN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:*.$DOMAIN,IP:127.0.0.1"

    # Create chain (same as fullchain for self-signed)
    cp "$SSL_DIR/fullchain.pem" "$SSL_DIR/chain.pem"

    # Set permissions
    chmod 600 "$SSL_DIR/privkey.pem"
    chmod 644 "$SSL_DIR/fullchain.pem"
    chmod 644 "$SSL_DIR/chain.pem"

    echo -e "${GREEN}"
    echo "================================================"
    echo "  Self-signed certificates generated!"
    echo "================================================"
    echo -e "${NC}"
    echo "Location: $SSL_DIR/"
    echo ""
    echo "Files created:"
    echo "  - privkey.pem   (private key)"
    echo "  - fullchain.pem (certificate + chain)"
    echo "  - chain.pem     (CA chain)"
    echo ""
    echo -e "${YELLOW}WARNING: Self-signed certificates will show browser warnings.${NC}"
    echo "For production, use Let's Encrypt: $0 letsencrypt your-domain.com"
}

setup_letsencrypt() {
    DOMAIN=$1

    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}Error: Domain is required for Let's Encrypt${NC}"
        echo "Usage: $0 letsencrypt your-domain.com"
        exit 1
    fi

    echo -e "${YELLOW}Setting up Let's Encrypt for $DOMAIN...${NC}"

    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot
        else
            echo -e "${RED}Please install certbot manually${NC}"
            exit 1
        fi
    fi

    # Create docker-compose for certbot
    cat > "$CERTBOT_DIR/docker-compose.certbot.yml" << 'EOF'
version: '3.8'

services:
  certbot:
    image: certbot/certbot
    volumes:
      - ./www:/var/www/certbot
      - ./conf:/etc/letsencrypt
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
EOF

    echo ""
    echo -e "${BLUE}Let's Encrypt Setup Instructions:${NC}"
    echo ""
    echo "1. First, start nginx with HTTP only (for ACME challenge):"
    echo "   docker compose -f docker-compose.prod.yml up -d nginx"
    echo ""
    echo "2. Run certbot to obtain certificates:"
    echo "   sudo certbot certonly --webroot -w $CERTBOT_DIR/www -d $DOMAIN -d www.$DOMAIN"
    echo ""
    echo "3. Copy certificates to nginx ssl directory:"
    echo "   sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/"
    echo "   sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/"
    echo "   sudo cp /etc/letsencrypt/live/$DOMAIN/chain.pem $SSL_DIR/"
    echo ""
    echo "4. Restart nginx to enable HTTPS:"
    echo "   docker compose -f docker-compose.prod.yml restart nginx"
    echo ""
    echo "5. Set up auto-renewal (add to crontab):"
    echo "   0 0 1 * * certbot renew --quiet && docker compose -f docker-compose.prod.yml restart nginx"
    echo ""

    # Create a renewal script
    cat > "$PROJECT_ROOT/scripts/renew-ssl.sh" << EOF
#!/bin/bash
# SSL Certificate Renewal Script
# Run this monthly via cron

certbot renew --quiet
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/
cp /etc/letsencrypt/live/$DOMAIN/chain.pem $SSL_DIR/
docker compose -f $PROJECT_ROOT/docker-compose.prod.yml restart nginx

echo "[\$(date)] SSL certificates renewed for $DOMAIN" >> /var/log/optiflow-ssl-renewal.log
EOF
    chmod +x "$PROJECT_ROOT/scripts/renew-ssl.sh"

    echo -e "${GREEN}Let's Encrypt setup files created!${NC}"
    echo "Renewal script: $PROJECT_ROOT/scripts/renew-ssl.sh"
}

# Main
case "$1" in
    self-signed)
        generate_self_signed "$2"
        ;;
    letsencrypt)
        setup_letsencrypt "$2"
        ;;
    *)
        usage
        ;;
esac
