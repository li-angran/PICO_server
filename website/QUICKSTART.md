# PICO Platform - Quick Start Guide

## Installation (5 minutes)

1. Navigate to the website directory:
```bash
cd /data/home/angran/BBNC/code/PICO_ca_processing/website
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Follow the prompts to create user accounts.

## Starting the Server

### Option 1: Development Mode (Testing)
```bash
python app.py
```

### Option 2: Production Mode (Recommended)
```bash
./start_server.sh
```

### Option 3: Background Mode (Persistent)
```bash
nohup ./start_server.sh > server.log 2>&1 &
```

To check if running:
```bash
ps aux | grep gunicorn
```

To stop:
```bash
pkill -f gunicorn
```

## Accessing the Platform

Open a web browser and navigate to:
```
http://<server-ip>:5000
```

Replace `<server-ip>` with your server's IP address.

## First Time Usage

1. **Login**
   - Use the username and password created during setup

2. **Create an Experiment**
   - Click "New Experiment"
   - Enter name: e.g., "Test Run 1"
   - Enter description: e.g., "Testing with sample data"
   - Select GPU ID (check GPU info on dashboard)
   - Modify parameters if needed (defaults loaded from params.json)
   - Click "Save Experiment"

3. **Configure Parameters**
   - `data_path`: Path to input frames
   - `out_path`: Path for output files
   - Other parameters match process_script.py arguments

4. **Start Processing**
   - Click "Start" button on the experiment card
   - Monitor progress in real-time by clicking the card
   - View logs, GPU usage, and status

5. **View Results**
   - Click on completed experiment
   - View output files
   - Download results

## User Management

### Create New User
```bash
python init_db.py create <username> <password>
```

### List All Users
```bash
python init_db.py list
```

### Delete User
```bash
python init_db.py delete <username>
```

## Troubleshooting

### Can't access from other devices
Check firewall:
```bash
sudo ufw allow 5000/tcp
```

### Port already in use
Change port in `app.py` (line at bottom):
```python
app.run(host='0.0.0.0', port=8080, debug=False)
```

### View server logs
```bash
tail -f server.log
tail -f error.log
```

### Check experiment logs
Navigate to: `experiments/exp_<id>_<timestamp>/process.log`

## System Service (Optional)

For automatic startup on boot:

1. Update service file paths if needed:
```bash
nano pico-platform.service
```

2. Install service:
```bash
sudo cp pico-platform.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pico-platform
sudo systemctl start pico-platform
```

3. Check status:
```bash
sudo systemctl status pico-platform
```

4. View logs:
```bash
sudo journalctl -u pico-platform -f
```

## Tips

- **GPU Selection**: Check GPU utilization on dashboard before starting
- **Parameter Presets**: Save commonly used parameter sets by creating template experiments
- **Multiple Experiments**: You can queue multiple experiments on different GPUs
- **Log Monitoring**: Logs refresh automatically every 3 seconds when viewing running experiments
- **Stop Safely**: Always use the "Stop" button rather than killing processes manually

## Common Parameters

Key parameters you'll often modify:

- `data_path`: Input data location
- `out_path`: Output directory
- `gpu_ids`: GPU device ID (also set via GPU ID dropdown)
- `fr`: Frame rate
- `mc_chunk_size`: Memory chunk size for motion correction
- `rmbg_chunk_size`: Chunk size for background removal
- `patch_size`: Size of patches for processing

## Support

For issues with:
- **Platform**: Check logs in `website/` directory
- **Processing**: Check experiment logs in `experiments/exp_*/process.log`
- **Process Script**: Refer to main PICO documentation

## Security Notes

⚠️ **Important**: 
- Change the SECRET_KEY in `app.py` before production use
- Use HTTPS in production (setup reverse proxy with nginx)
- Keep user passwords secure
- Regular backup of `pico_platform.db`
