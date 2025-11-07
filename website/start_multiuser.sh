#!/bin/bash
# Startup script for PICO multi-user web interface

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  PICO Pipeline Multi-User Interface${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in the website directory
if [ ! -f "app_multiuser.py" ]; then
    echo -e "${YELLOW}Changing to website directory...${NC}"
    cd "$(dirname "$0")"
fi

# Check if requirements are installed
echo -e "${GREEN}Checking dependencies...${NC}"
if ! python -c "import flask, flask_sqlalchemy, flask_login" 2>/dev/null; then
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install -r requirements_multiuser.txt
else
    echo -e "${GREEN}✓ All dependencies installed${NC}"
fi

# Create experiment_logs directory if it doesn't exist
if [ ! -d "experiment_logs" ]; then
    echo -e "${GREEN}Creating experiment_logs directory...${NC}"
    mkdir -p experiment_logs
fi

# Check if database exists
if [ ! -f "pico_experiments.db" ]; then
    echo -e "${YELLOW}Database will be created on first run with default users${NC}"
fi

echo ""
echo -e "${GREEN}Starting PICO multi-user web interface...${NC}"

# Determine primary IP (best-effort)
PRIMARY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$PRIMARY_IP" ]; then
    PRIMARY_IP="<server-ip>"
fi

echo -e "${BLUE}Access URLs:${NC}"
echo -e "  • On this machine:   http://127.0.0.1:5010"
echo -e "  • From your network: http://$PRIMARY_IP:5010"
echo ""
echo -e "${YELLOW}User accounts:${NC}"
echo "  • Create or manage users with: python manage_users.py add|list|password|delete"
echo "    (first run creates the database automatically)"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the application
python app_multiuser.py
