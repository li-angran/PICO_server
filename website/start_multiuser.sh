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
echo -e "${BLUE}Access at: http://localhost:5000${NC}"
echo ""
echo -e "${YELLOW}Default accounts:${NC}"
echo "  • admin / admin123"
echo "  • user1 / user123"
echo "  • user2 / user123"
echo "  • researcher / research123"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the application
python app_multiuser.py
