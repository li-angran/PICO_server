# Quick Start Guide - Multi-User PICO Pipeline Web Interface

## 🚀 Quick Setup (3 steps)

### 1. Install Dependencies
```bash
cd website
pip install -r requirements_multiuser.txt
```

### 2. Start the Server
```bash
python app_multiuser.py
```

Or use the startup script:
```bash
bash start_multiuser.sh
```

### 3. Access the Application
Open your browser to: **http://localhost:5000**

## 🔑 Login

Use any of these demo accounts:

| Username   | Password     |
|------------|--------------|
| admin      | admin123     |
| user1      | user123      |
| user2      | user123      |
| researcher | research123  |

## 📋 First Experiment

1. **Login** with your credentials
2. Click **"+ New Experiment"**
3. Fill in the form:
   - **Name:** "Test Calcium Imaging"
   - **Description:** "My first test experiment"
   - **Input path:** `/path/to/your/tiff/files`
   - **Output path:** `/path/to/output/folder`
4. Configure pipeline parameters (or use defaults)
5. Click **"Create & Run Experiment"**
6. Watch real-time logs in the terminal output section

## 📊 View Your Experiments

- Go to **Dashboard** to see all your experiments
- Click **"View Details"** to see logs and parameters
- Click **"Edit & Run"** to modify and re-run

## 🗂️ Where Are Logs Saved?

All logs are automatically saved to:
```
website/experiment_logs/exp_{ID}_{TIMESTAMP}.log
```

Example: `experiment_logs/exp_1_20241028_143022.log`

## 🔄 Re-running Experiments

You can edit and re-run any completed experiment:
1. Find it in your dashboard
2. Click "Edit & Run"
3. Modify parameters
4. Run again - a new log file will be created

## 💾 Database Location

User accounts and experiment metadata are stored in:
```
website/pico_experiments.db
```

**Backup this file** to preserve your experiment history!

## 🛑 Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## 🔧 Troubleshooting

### Can't access the website?
- Make sure the server is running (check terminal)
- Try: http://127.0.0.1:5000
- Check firewall settings

### Pipeline script not found?
- Ensure `somm_processingv1.py` exists in the parent directory
- Check paths in `app_multiuser.py` if needed

### Login not working?
- Delete `pico_experiments.db` to recreate database
- Restart the server

### Need more users?
Edit `database.py` and add them to the `create_default_users()` function.

## 🌐 Access from Other Devices

To allow access from other computers on your network:

1. Find your server's IP address:
   ```bash
   hostname -I
   ```

2. Other devices can access via:
   ```
   http://YOUR_IP_ADDRESS:5000
   ```

3. Example: `http://192.168.1.100:5000`

## 📚 Full Documentation

See [README_MULTIUSER.md](README_MULTIUSER.md) for complete documentation including:
- API endpoints
- Database schema
- Production deployment
- Configuration options

## ⚠️ Security Note

**For production use:**
- Change default passwords
- Set a secure SECRET_KEY environment variable
- Use HTTPS with a reverse proxy
- Configure proper authentication

## 🆘 Need Help?

1. Check the terminal output for error messages
2. Review logs in `experiment_logs/` directory
3. Verify input/output paths are valid
4. Make sure PICO environment is activated

---

**Happy Processing! 🔬**
