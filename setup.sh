#!/bin/bash

# Set colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================"
echo "        Project Management System Setup"
echo -e "================================================${NC}"
echo

# Check if running with sudo/root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}[ERROR] This script must be run as root!"
    echo -e "Please run: sudo $0${NC}"
    exit 1
fi

# Check internet connection using multiple methods
echo "Checking internet connection..."
check_connection() {
    if command -v curl >/dev/null 2>&1; then
        curl -s --connect-timeout 2 https://google.com >/dev/null
        return $?
    elif command -v wget >/dev/null 2>&1; then
        wget -q --spider --timeout=2 https://google.com
        return $?
    elif command -v ping >/dev/null 2>&1; then
        ping -c 1 -W 2 google.com >/dev/null 2>&1
        return $?
    else
        # If no tools available, assume connection exists
        return 0
    fi
}

if ! check_connection; then
    echo -e "${RED}[ERROR] No internet connection detected!"
    echo -e "Please check your internet connection and try again.${NC}"
    exit 1
fi

# Install Python if not present
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 is not installed. Installing Python 3.11...${NC}"
    
    # Detect OS
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt update
        apt install -y software-properties-common
        add-apt-repository -y ppa:deadsnakes/ppa
        apt update
        apt install -y python3.11 python3.11-venv python3.11-dev
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        yum install -y epel-release
        yum install -y python3.11 python3.11-devel
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        pacman -Sy python
    else
        echo -e "${RED}[ERROR] Unsupported operating system!"
        echo "Please install Python 3.11 manually.${NC}"
        exit 1
    fi
fi

# Verify Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info[1])')
if [ "$PYTHON_VERSION" -lt 11 ]; then
    echo -e "${RED}[ERROR] Python version must be 3.11 or higher!"
    echo -e "Current version: $PYTHON_VERSION${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${GREEN}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Updating existing virtual environment..."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment!${NC}"
        exit 1
    fi
fi
source venv/bin/activate

# Install requirements
echo -e "\n${GREEN}Installing required packages...${NC}"
python -m pip install --upgrade pip

# Install packages with progress
packages=(
    "Flask==2.3.3"
    "Werkzeug==2.3.7"
    "Flask-SQLAlchemy==3.1.1"
    "Flask-Login==0.6.2"
    "Flask-WTF==1.2.1"
    "Flask-Migrate==4.0.5"
    "SQLAlchemy==2.0.26"
    "email-validator==2.1.0"
    "python-dotenv==1.0.0"
    "Jinja2==3.1.3"
    "itsdangerous==2.1.2"
    "Flask-Bcrypt==1.0.1"
    "Pillow==10.2.0"
    "alembic==1.13.1"
)

for package in "${packages[@]}"; do
    echo "Installing $package..."
    pip install "$package"
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install $package${NC}"
        exit 1
    fi
done

# Create project structure
echo -e "\n${GREEN}Creating project structure...${NC}"
directories=(
    "instance"
    "app/static/css"
    "app/static/js"
    "app/static/img"
    "app/templates/errors"
    "app/templates/admin"
    "app/templates/manager"
    "logs"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
done

# Create .env file
echo -e "\n${GREEN}Creating configuration files...${NC}"
if [ ! -f .env ]; then
    cat > .env << EOL
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///instance/site.db
EOL
fi

# Initialize database
echo -e "\n${GREEN}Initializing database...${NC}"
flask db init
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to initialize database!${NC}"
    exit 1
fi

flask db migrate -m "Initial database setup"
flask db upgrade

# Create admin user
echo -e "\n${GREEN}Creating admin user...${NC}"
python3 -c "
from app import create_app, db
from app.models import User, UserRole
from werkzeug.security import generate_password_hash
app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        role=UserRole.ADMIN
    )
    db.session.add(admin)
    db.session.commit()
print('Admin user created successfully!')
"

echo -e "\n${BLUE}================================================"
echo "              Setup Complete!"
echo -e "================================================${NC}"
echo
echo "Default admin credentials:"
echo "  Username: admin@example.com"
echo "  Password: admin123"
echo
echo "To start the application:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo
echo "2. Run the application:"
echo "   python run.py"
echo
echo "The application will be available at:"
echo "http://localhost:5000"
echo

read -p "Would you like to start the application now? (y/n): " start_now
if [[ $start_now == "y" ]]; then
    source venv/bin/activate
    python run.py
fi
