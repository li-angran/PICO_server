# PICO Calcium Processing Platform

## 🎯 Overview

A complete web-based platform for managing and running calcium signal processing experiments on your server. Users can log in from any device, create experiments, configure parameters, monitor GPU usage, and manage results - all through an intuitive web interface.

## ✨ Features

### Core Functionality
- 🔐 **User Authentication** - Secure login system (no registration, admin creates accounts)
- 🧪 **Experiment Management** - Create, edit, start, stop, and delete experiments
- ⚙️ **Parameter Configuration** - Edit all process_script.py parameters via web UI
- 🎮 **GPU Selection** - Choose which GPU to run each experiment on
- 📊 **Real-time Monitoring** - Live status updates, logs, and GPU utilization
- 📁 **Output Management** - View and download all experiment outputs
- 📚 **Experiment History** - Complete history of all experiments per user

### User Experience
- 📱 **Responsive Design** - Access from desktop, tablet, or mobile
- 🔄 **Auto-refresh** - Status updates every 5 seconds
- 📝 **Live Logs** - Real-time log streaming for running experiments
- 📈 **GPU Monitoring** - Visual GPU memory and load indicators
- 🎨 **Modern UI** - Clean, intuitive interface

## 📁 Project Structure

```
website/
├── app.py                  # Main Flask application
├── init_db.py             # Database management utility
├── config.py              # Configuration settings
├── monitor.py             # System monitoring tool
├── setup.sh               # Automated setup script
├── start_server.sh        # Production server launcher
├── backup.sh              # Database backup script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── QUICKSTART.md         # Quick start guide
├── DEPLOYMENT.md         # Comprehensive deployment guide
├── .gitignore            # Git ignore rules
├── pico-platform.service # Systemd service file
├── templates/            # HTML templates
│   ├── login.html
│   └── dashboard.html
├── experiments/          # Experiment outputs (auto-created)
├── backups/              # Database backups (auto-created)
└── pico_platform.db      # SQLite database (auto-created)
```

## 🚀 Quick Start

### 1. Installation (5 minutes)

```bash
cd /data/home/angran/BBNC/code/PICO_ca_processing/website
./setup.sh
```

Follow prompts to create user accounts.

### 2. Start Server

```bash
./start_server.sh
```

Or for background mode:
```bash
nohup ./start_server.sh > server.log 2>&1 &
```

### 3. Access Platform

Open browser: `http://<server-ip>:5000`

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide with troubleshooting

## 🔧 Common Commands

### User Management
```bash
python init_db.py create <username> <password>  # Create user
python init_db.py list                           # List users
python init_db.py delete <username>              # Delete user
```

### Server Management
```bash
./start_server.sh                    # Start server
pkill -f gunicorn                    # Stop server
ps aux | grep gunicorn               # Check if running
```

### Monitoring
```bash
python monitor.py --once             # One-time status
python monitor.py --interval 10      # Continuous monitoring
tail -f server.log                   # View server logs
```

### Backup
```bash
./backup.sh                          # Manual backup
```

## 🏗️ Architecture

### Backend (Flask)
- **Web Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (upgradeable to PostgreSQL)
- **Process Management**: subprocess + psutil for experiment control
- **Authentication**: Session-based with hashed passwords

### Frontend
- **Pure HTML/CSS/JavaScript** - No build process required
- **RESTful API** - JSON-based communication
- **Auto-refresh** - Periodic updates via JavaScript

### Data Flow
```
User → Web UI → Flask API → Database
                         ↓
                    Subprocess → process_script.py
                         ↓
                    Output Files → Download
```

## 🔐 Security Considerations

⚠️ **Before Production:**
1. Change `SECRET_KEY` in `app.py`
2. Set up HTTPS with nginx reverse proxy
3. Configure firewall (allow port 5000)
4. Regular backups
5. Strong user passwords

## 📊 Technology Stack

- **Python 3.7+**
- **Flask 2.3** - Web framework
- **SQLAlchemy 3.0** - ORM
- **psutil** - Process management
- **GPUtil** - GPU monitoring
- **Gunicorn** - WSGI server

## 🎯 Use Cases

### Typical Workflow

1. **Researcher logs in** from their workstation
2. **Creates experiment** with descriptive name
3. **Configures parameters** - data paths, GPU ID, processing options
4. **Starts experiment** - runs on selected GPU
5. **Monitors progress** - real-time logs and status
6. **Downloads results** - processed files, masks, traces
7. **Experiment history** - keeps complete record

### Multi-User Scenario

- Multiple researchers can run experiments simultaneously
- Each user sees only their own experiments
- Different GPUs can be assigned to avoid conflicts
- Fair resource sharing through GPU monitoring

## 🛠️ Customization

### Adding Parameters

Edit `app.py` to add new parameters from `process_script.py`:

```python
defaultParams = {
    "your_new_param": default_value,
    # ... existing params
}
```

### Changing Defaults

Edit `params.json` or modify defaults in dashboard JavaScript.

### Styling

Modify inline CSS in `templates/*.html` or extract to separate CSS file.

## 📈 Performance

### Capacity
- **Users**: 10-100+ concurrent users
- **Experiments**: Thousands of experiments in history
- **File Size**: No practical limit (depends on disk space)

### Optimization
- Worker count: Adjust in `start_server.sh`
- Database: Switch to PostgreSQL for >1000 experiments
- Caching: Add Redis for session management

## 🐛 Troubleshooting

### Can't Access from Other Devices
```bash
sudo ufw allow 5000/tcp
```

### Port Already in Use
```bash
lsof -i :5000
kill -9 <PID>
```

### Experiments Won't Start
- Check `process_script.py` path in `app.py`
- Verify data paths exist and are accessible
- Check GPU availability

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for comprehensive troubleshooting.

## 🔄 Updates & Maintenance

### Regular Tasks
- **Daily**: Monitor disk space
- **Weekly**: Review experiment logs, cleanup old outputs
- **Monthly**: Backup database, update dependencies

### Backup Strategy
```bash
# Automated daily backup (cron)
0 2 * * * cd /path/to/website && ./backup.sh
```

## 📞 Support

For issues:
1. Check logs: `tail -f error.log`
2. Review experiment logs: `experiments/exp_*/process.log`
3. Consult **[DEPLOYMENT.md](DEPLOYMENT.md)**
4. Check system resources: `python monitor.py --once`

## 🎓 Learning Resources

- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Gunicorn: https://gunicorn.org/

## 📝 Notes

- Designed for internal lab/research use
- Assumes trusted users (no rate limiting, quotas)
- Focus on usability and reliability
- Straightforward deployment and maintenance

## 🙏 Credits

Built for the PICO calcium processing pipeline.

Authors: Yuanlong Zhang, Mingrui Wang, Lekang Yuan

Platform developed for streamlined experiment management and remote access.

---

**Ready to process calcium signals! 🧠✨**

For detailed instructions, see:
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Full Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
