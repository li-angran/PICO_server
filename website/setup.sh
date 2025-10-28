#!/bin/bash

# PICO Platform Setup Script

set -e

echo "=========================================="
echo "PICO Calcium Processing Platform Setup"
echo "=========================================="
echo ""

# Check if running from website directory
if [ ! -f "app.py" ]; then
    echo "Error: Please run this script from the website directory"
    exit 1
fi

# # Create virtual environment if it doesn't exist
# if [ ! -d "venv" ]; then
#     echo "Creating virtual environment..."
#     python3 -m venv venv
#     echo "✓ Virtual environment created"
# else
#     echo "✓ Virtual environment already exists"
# fi

# # Activate virtual environment
# source venv/bin/activate

# # Upgrade pip
# echo ""
# echo "Upgrading pip..."
# pip install --upgrade pip

# # Install dependencies
# echo ""
# echo "Installing dependencies..."
# pip install -r requirements.txt
# echo "✓ Dependencies installed"

# # Create necessary directories
# echo ""
# echo "Creating directories..."
# mkdir -p experiments
# mkdir -p templates
# echo "✓ Directories created"

# Initialize database
echo ""
echo "Initializing database..."
python init_db.py init
echo "✓ Database initialized"

# Create default users
echo ""
echo "=========================================="
echo "User Account Setup"
echo "=========================================="
echo ""
echo "Would you like to create user accounts now? (y/n)"
read -r create_users

if [ "$create_users" = "y" ] || [ "$create_users" = "Y" ]; then
    while true; do
        echo ""
        echo "Enter username (or 'done' to finish):"
        read -r username
        
        if [ "$username" = "done" ]; then
            break
        fi
        
        echo "Enter password for $username:"
        read -s password
        
        python init_db.py create "$username" "$password"
    done
fi

# Make scripts executable
echo ""
echo "Setting permissions..."
chmod +x start_server.sh
chmod +x setup.sh
echo "✓ Permissions set"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  1. Development mode:  python app.py"
echo "  2. Production mode:   ./start_server.sh"
echo "  3. Background mode:   nohup ./start_server.sh > server.log 2>&1 &"
echo ""
echo "To manage users:"
echo "  List users:    python init_db.py list"
echo "  Create user:   python init_db.py create <username> <password>"
echo "  Delete user:   python init_db.py delete <username>"
echo ""
echo "Access the platform at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "For production deployment with systemd:"
echo "  sudo cp pico-platform.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable pico-platform"
echo "  sudo systemctl start pico-platform"
echo ""
