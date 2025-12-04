# Node-RED with Industrial Protocol Nodes (READ-ONLY)
# ====================================================
# Pre-installed nodes for industrial communication validation:
# - Siemens S7 (S7-300, S7-400, S7-1200, S7-1500)
# - Rockwell EtherNet/IP (CompactLogix, ControlLogix)
# - OPC-UA Client
# - Modbus TCP/RTU
# - MQTT (built-in)

FROM nodered/node-red:latest

# Install industrial protocol nodes
RUN npm install --save \
    node-red-contrib-s7 \
    node-red-contrib-cip-ethernet-ip \
    node-red-contrib-opcua \
    node-red-contrib-modbus \
    node-red-contrib-influxdb \
    node-red-node-random

# Copy default settings (optional)
# COPY settings.js /data/settings.js

# Expose Node-RED port
EXPOSE 1880

# Run as node-red user
USER node-red
