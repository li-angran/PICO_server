# PICO Platform Configuration

# Flask Configuration
SECRET_KEY = 'your-secret-key-change-this-in-production'
DEBUG = False

# Database Configuration
DATABASE_URI = 'sqlite:///pico_platform.db'

# Server Configuration
HOST = '0.0.0.0'
PORT = 5000
WORKERS = 4
TIMEOUT = 3600

# Process Script Configuration
PROCESS_SCRIPT_PATH = '../process_script.py'

# Output Configuration
EXPERIMENTS_DIR = 'experiments'
MAX_LOG_LINES = 1000

# Auto-refresh intervals (milliseconds)
REFRESH_EXPERIMENTS = 5000
REFRESH_GPU_INFO = 5000
REFRESH_LOG = 3000
