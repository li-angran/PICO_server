# PICO Platform - Complete Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [User Management](#user-management)
5. [Running the Server](#running-the-server)
6. [Using the Platform](#using-the-platform)
7. [Monitoring](#monitoring)
8. [Backup & Maintenance](#backup--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- Linux server (Ubuntu 18.04+ recommended)
- Python 3.7+
- CUDA-capable GPU(s)
- At least 8GB RAM
- Sufficient disk space for experiment outputs

### Required Python Packages
All dependencies are listed in `requirements.txt` and will be installed automatically.

---

## Installation

### Step 1: Navigate to Website Directory
```bash
cd /data/home/angran/BBNC/code/PICO_ca_processing/website
```

### Step 2: Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

This script will:
- Create a Python virtual environment
- Install all dependencies
- Initialize the database
- Create necessary directories
- Prompt for user account creation

### Step 3: Create User Accounts

During setup, you'll be prompted to create users. Alternatively:

```bash
source venv/bin/activate
python init_db.py create <username> <password>
```

Example:
```bash
python init_db.py create researcher1 mypassword123
python init_db.py create researcher2 securepass456
```

---

## Configuration

### Basic Configuration

Edit `app.py` to change:

1. **Secret Key** (IMPORTANT for production):
```python
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **Database** (optional - default is SQLite):
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pico_platform.db'
```

3. **Process Script Path** (if needed):
```python
script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'process_script.py')
```

### Advanced Configuration

Edit `config.py` for:
- Server host and port
- Worker processes
- Timeout settings
- Auto-refresh intervals
- Output directories

---

## User Management

### List All Users
```bash
python init_db.py list
```

### Create New User
```bash
python init_db.py create <username> <password>
```

### Delete User
```bash
python init_db.py delete <username>
```

### Change Password
Delete and recreate the user with a new password.

---

## Running the Server

### Development Mode (Testing Only)
```bash
python app.py
```
- Good for: Testing, development
- Auto-reloads on code changes
- Single worker process
- **Not for production!**

### Production Mode (Recommended)
```bash
./start_server.sh
```
- Multiple worker processes
- Better performance
- Logging to files
- Suitable for production

### Background Mode (Persistent)
```bash
nohup ./start_server.sh > server.log 2>&1 &
```
- Runs in background
- Survives terminal closure
- Logs to server.log

### Check if Running
```bash
ps aux | grep gunicorn
# or
ps aux | grep "python app.py"
```

### Stop the Server
```bash
# For gunicorn
pkill -f gunicorn

# For development mode
# Press Ctrl+C in the terminal
```

---

## Using the Platform

### Accessing the Platform

1. Find your server IP:
```bash
hostname -I
```

2. Open browser and navigate to:
```
http://<server-ip>:5000
```

### Login
- Use credentials created during setup
- Each user has their own experiment workspace

### Creating an Experiment

1. Click "**+ New Experiment**"
2. Fill in details:
   - **Name**: Descriptive name (e.g., "Mouse 1 Session A")
   - **Description**: Optional notes
   - **GPU ID**: Select available GPU (check GPU info on dashboard)
   - **Parameters**: Adjust as needed

3. Click "**Save Experiment**"

### Parameter Configuration

Key parameters you'll modify:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `data_path` | Input frames directory | `/mnt/nas01/data/mouse1/frames` |
| `out_path` | Output directory | `/mnt/nas01/data/mouse1/analysis` |
| `fr` | Frame rate | `10` |
| `gpu_ids` | GPU device ID | `0` |
| `mc_chunk_size` | Motion correction chunk size | `1000` |
| `rmbg_chunk_size` | Background removal chunk size | `2000` |

See `params.json` for all available parameters.

### Running an Experiment

1. Click "**▶ Start**" on experiment card
2. Monitor progress:
   - Status badge updates in real-time
   - GPU utilization shown in dashboard
   - Click card to view detailed logs

3. To stop: Click "**⏹ Stop**" button

### Viewing Results

1. Click on experiment card
2. View:
   - Real-time logs (auto-refreshes every 3 seconds)
   - Process status
   - Runtime information
   - Output files list

3. Download files:
   - Click "**Download**" next to any output file
   - Files include: processed images, masks, traces, etc.

---

## Monitoring

### Web Dashboard
- Real-time experiment status
- GPU utilization
- System resources
- Auto-refreshes every 5 seconds

### Command Line Monitoring

#### One-time Status Check
```bash
python monitor.py --once
```

#### Continuous Monitoring
```bash
python monitor.py --interval 10
```

Displays:
- System CPU, memory, disk usage
- GPU usage and temperature
- All experiments by status
- Process information (PID, CPU, memory)
- Runtime statistics

### Log Files

#### Server Logs
```bash
tail -f access.log    # HTTP requests
tail -f error.log     # Server errors
tail -f server.log    # Combined output
```

#### Experiment Logs
```bash
# Navigate to experiment output directory
cd experiments/exp_<id>_<timestamp>/
tail -f process.log
```

---

## Backup & Maintenance

### Manual Backup
```bash
./backup.sh
```

Creates timestamped backup in `backups/` directory.
Keeps last 10 backups automatically.

### Automated Backups (Cron)

Add to crontab:
```bash
crontab -e
```

Add line for daily backup at 2 AM:
```
0 2 * * * cd /data/home/angran/BBNC/code/PICO_ca_processing/website && ./backup.sh
```

### Restore from Backup
```bash
cd backups
tar -xzf pico_platform_backup_<timestamp>.tar.gz
cd pico_platform_backup_<timestamp>
cp pico_platform.db ../../
```

### Clean Old Experiments

Manually delete old experiment directories:
```bash
cd experiments
rm -rf exp_<old_id>_*
```

Or keep only recent ones:
```bash
find experiments -type d -mtime +30 -exec rm -rf {} +
```

---

## System Service (Production)

For automatic startup on boot:

### Install Service

1. Edit service file if paths differ:
```bash
nano pico-platform.service
```

2. Install:
```bash
sudo cp pico-platform.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pico-platform
sudo systemctl start pico-platform
```

### Manage Service

```bash
# Start
sudo systemctl start pico-platform

# Stop
sudo systemctl stop pico-platform

# Restart
sudo systemctl restart pico-platform

# Status
sudo systemctl status pico-platform

# View logs
sudo journalctl -u pico-platform -f
```

---

## Troubleshooting

### Cannot Access from Other Devices

**Problem**: Can access on server but not from other computers

**Solution**: 
1. Check firewall:
```bash
sudo ufw status
sudo ufw allow 5000/tcp
```

2. Verify server is listening on all interfaces:
```bash
netstat -tulpn | grep 5000
# Should show 0.0.0.0:5000
```

### Port Already in Use

**Problem**: "Address already in use" error

**Solution**:
1. Find process using port:
```bash
lsof -i :5000
```

2. Kill process:
```bash
kill -9 <PID>
```

3. Or change port in `app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=False)
```

### Experiment Won't Start

**Problem**: Click "Start" but experiment doesn't run

**Solution**:
1. Check `process_script.py` path in `app.py`
2. Verify Python environment has all dependencies
3. Check experiment logs for errors
4. Verify GPU availability
5. Check file permissions on data paths

### Database Locked

**Problem**: "Database is locked" error

**Solution**:
1. Stop all server processes
2. Check for stale connections:
```bash
fuser pico_platform.db
```
3. Restart server

### High Memory Usage

**Problem**: Server consuming too much memory

**Solution**:
1. Reduce worker count in `start_server.sh`:
```bash
WORKERS=2
```

2. Reduce chunk sizes in experiment parameters
3. Monitor with: `python monitor.py`

### GPU Not Detected

**Problem**: GPU info not showing

**Solution**:
1. Install GPUtil:
```bash
pip install GPUtil
```

2. Verify CUDA installation:
```bash
nvidia-smi
```

3. Platform will work without GPU info (shows placeholder)

### Login Issues

**Problem**: Cannot login with correct credentials

**Solution**:
1. Check database:
```bash
python init_db.py list
```

2. Recreate user:
```bash
python init_db.py delete <username>
python init_db.py create <username> <new_password>
```

3. Clear browser cookies/cache

---

## Security Best Practices

### Production Deployment

1. **Change Secret Key**: 
   - Never use default key in production
   - Generate cryptographically secure key

2. **Use HTTPS**: 
   - Set up reverse proxy (nginx) with SSL
   - Use Let's Encrypt for free SSL certificates

3. **Firewall**: 
   - Only allow necessary ports
   - Use SSH key authentication

4. **Regular Updates**:
   - Keep Python packages updated
   - Monitor security advisories

5. **Backup**:
   - Regular automated backups
   - Test restore procedures

6. **User Management**:
   - Strong password policy
   - Regular audit of user accounts
   - Remove inactive users

### Example Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Performance Tuning

### Optimize Worker Count
```bash
# In start_server.sh
WORKERS=$(( 2 * $(nproc) + 1 ))
```

### Database Optimization
For heavy use, consider PostgreSQL instead of SQLite:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/pico_platform'
```

### Disk Space Management
- Regularly clean old experiments
- Consider separate partition for experiments
- Monitor disk usage: `df -h`

---

## Support & Contact

For issues related to:
- **Platform**: Check logs, refer to this guide
- **Process Script**: Refer to main PICO documentation
- **System**: Check system logs, monitor resources

---

## Changelog

### Version 1.0 (Initial Release)
- User authentication
- Experiment management
- Real-time monitoring
- GPU selection
- Log viewing
- File download
- Dashboard interface

---

## License

This platform is designed for use with the PICO calcium processing pipeline.

---

**Happy Processing! 🧠🔬**
