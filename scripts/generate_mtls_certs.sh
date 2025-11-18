#!/bin/bash
# PDCA #2: Generate mTLS Certificates for Gateway ↔ Backend
# ==========================================================
#
# Creates a test PKI infrastructure with:
# - Root CA (Certificate Authority)
# - Gateway client certificate
# - Backend server certificate
#
# For production, use HashiCorp Vault PKI backend instead!

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CERTS_DIR="$PROJECT_ROOT/certs"

echo "=================================================="
echo "OptiFlow AI - mTLS Certificate Generation"
echo "=================================================="
echo ""

# Create certs directory
mkdir -p "$CERTS_DIR"
cd "$CERTS_DIR"

echo "📁 Working directory: $CERTS_DIR"
echo ""

# ========================================
# 1. Generate Root CA (Certificate Authority)
# ========================================
echo "🔐 Step 1/5: Generating Root CA..."

# Generate CA private key (4096-bit RSA for security)
openssl genrsa -out ca.key 4096

# Generate CA certificate (valid for 10 years)
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/C=BR/ST=SaoPaulo/L=SaoPaulo/O=OptiFlow/OU=Security/CN=OptiFlow Root CA"

echo "✅ Root CA created: ca.crt (valid 10 years)"
echo ""

# ========================================
# 2. Generate Gateway Client Certificate
# ========================================
echo "🔐 Step 2/5: Generating Gateway client certificate..."

# Generate gateway private key
openssl genrsa -out gateway.key 2048

# Generate Certificate Signing Request (CSR)
openssl req -new -key gateway.key -out gateway.csr \
  -subj "/C=BR/ST=SaoPaulo/L=SaoPaulo/O=OptiFlow/OU=Gateway/CN=optiflow-gateway"

# Sign certificate with CA (valid for 90 days - rotation policy)
openssl x509 -req -days 90 -in gateway.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out gateway.crt

# Cleanup CSR
rm gateway.csr

echo "✅ Gateway certificate created: gateway.crt (valid 90 days)"
echo ""

# ========================================
# 3. Generate Backend Server Certificate
# ========================================
echo "🔐 Step 3/5: Generating Backend server certificate..."

# Generate backend private key
openssl genrsa -out backend.key 2048

# Create config file for SAN (Subject Alternative Names)
cat > backend.cnf <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = BR
ST = SaoPaulo
L = SaoPaulo
O = OptiFlow
OU = Backend
CN = optiflow-backend

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = optiflow-backend
DNS.2 = backend
DNS.3 = localhost
IP.1 = 127.0.0.1
EOF

# Generate CSR with SAN
openssl req -new -key backend.key -out backend.csr -config backend.cnf

# Sign certificate with CA (valid for 90 days)
openssl x509 -req -days 90 -in backend.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out backend.crt -extensions v3_req -extfile backend.cnf

# Cleanup
rm backend.csr backend.cnf

echo "✅ Backend certificate created: backend.crt (valid 90 days)"
echo ""

# ========================================
# 4. Set Proper Permissions
# ========================================
echo "🔐 Step 4/5: Setting file permissions..."

# Private keys should be readable only by owner
chmod 600 *.key

# Certificates can be readable by all
chmod 644 *.crt

echo "✅ File permissions set (private keys: 600, certificates: 644)"
echo ""

# ========================================
# 5. Verify Certificates
# ========================================
echo "🔐 Step 5/5: Verifying certificates..."

# Verify gateway certificate
echo "  - Verifying gateway.crt..."
openssl verify -CAfile ca.crt gateway.crt

# Verify backend certificate
echo "  - Verifying backend.crt..."
openssl verify -CAfile ca.crt backend.crt

echo ""
echo "=================================================="
echo "✅ mTLS Certificates Generated Successfully!"
echo "=================================================="
echo ""

# Display certificate expiration dates
echo "📅 Certificate Expiration Dates:"
echo ""
echo "CA Certificate:"
openssl x509 -in ca.crt -noout -dates

echo ""
echo "Gateway Certificate:"
openssl x509 -in gateway.crt -noout -dates

echo ""
echo "Backend Certificate:"
openssl x509 -in backend.crt -noout -dates

echo ""
echo "=================================================="
echo "📂 Certificate Files:"
echo "=================================================="
ls -lh "$CERTS_DIR"

echo ""
echo "=================================================="
echo "⚠️  IMPORTANT NOTES:"
echo "=================================================="
echo ""
echo "1. These are TEST certificates for development only"
echo "2. For PRODUCTION, use HashiCorp Vault PKI backend"
echo "3. Certificates expire in 90 days (rotation policy)"
echo "4. Private keys (*.key) must be kept secure"
echo "5. Do NOT commit *.key files to git!"
echo ""
echo "To enable mTLS in docker-compose.yml:"
echo "  gateway:"
echo "    environment:"
echo "      MTLS_ENABLED: \"true\""
echo "    volumes:"
echo "      - ./certs:/app/certs:ro"
echo ""
echo "  backend:"
echo "    volumes:"
echo "      - ./certs:/app/certs:ro"
echo ""
echo "=================================================="
