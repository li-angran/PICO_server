# PICO Pipeline Multi-User Web Interface

A Flask-based web application for managing and running calcium imaging processing pipelines with multi-user support, experiment tracking, and automatic log saving.

## Features

### 🔐 Multi-User Authentication
- User login system with secure password hashing
- Pre-configured demo accounts
- Session management across devices
- User-specific experiment isolation

### 🧪 Experiment Management
- Create and name experiments with descriptions
- View experiment history and details
- Edit and re-run previous experiments
- Delete old experiments
- Track experiment status (created, running, completed, failed)

### 📝 Automatic Log Saving
- All pipeline execution logs automatically saved to disk
- Logs stored in `experiment_logs/` directory
- View historical logs from completed experiments
- Copy logs to clipboard

### 🚀 Pipeline Execution
- Full parameter configuration interface
- Auto-detect frame counts from input directories
- Real-time log streaming during execution
- Track execution time and exit codes
- Pipeline parameters saved with each experiment

## Installation

1. **Install dependencies:**
   ```bash
   cd website
   pip install -r requirements_multiuser.txt
   ```

2. **Run the application:**
   ```bash
   python app_multiuser.py
   ```

3. **Access the application:**
   - Open your browser to `http://localhost:5000`
   - Log in with one of the demo accounts

## Default User Accounts

The following accounts are created automatically on first run:

| Username   | Password     | Use Case          |
|------------|--------------|-------------------|
| admin      | admin123     | Administrator     |
| user1      | user123      | Regular user      |
| user2      | user123      | Regular user      |
| researcher | research123  | Research account  |

**⚠️ IMPORTANT:** Change these passwords in production! Edit `database.py` to modify default accounts or remove the auto-creation feature.

## Usage

### Creating an Experiment

1. **Login** with your credentials
2. Click **"+ New Experiment"** on the dashboard
3. Fill in:
   - **Experiment Name** (required)
   - **Description** (optional)
   - **Input Directory** - Path to raw image frames
   - **Output Directory** - Where results will be saved
   - **Pipeline Parameters** - Configure motion correction, segmentation, etc.
4. Click **"Create & Run Experiment"**

### Viewing Experiment History

- The **Dashboard** shows all your experiments sorted by creation date
- Each card displays:
  - Experiment name and status
  - Creation and completion timestamps
  - Input/output paths
  - Exit code (if completed)
- Click **"View Details"** to see full logs and parameters

### Re-running Experiments

1. Find the experiment in your dashboard
2. Click **"Edit & Run"**
3. Modify parameters as needed
4. Click **"Save & Run Pipeline"**
- Previous runs are preserved; each run generates a new log file

### Monitoring Execution

- Real-time terminal output streams during pipeline execution
- Status indicator shows current state (Ready, Running, Completed, Failed)
- Logs are automatically saved to `experiment_logs/exp_{id}_{timestamp}.log`

## File Structure

```
website/
├── app_multiuser.py              # Main Flask application
├── database.py                   # Database models and initialization
├── requirements_multiuser.txt    # Python dependencies
├── pico_experiments.db          # SQLite database (auto-created)
├── experiment_logs/             # Stored log files (auto-created)
│   └── exp_1_20241028_143022.log
└── templates/
    ├── login.html               # Login page
    ├── dashboard.html           # Experiment list
    ├── experiment_form.html     # Create/edit experiment
    └── experiment_detail.html   # View experiment details
```

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `password_hash` - Hashed password
- `created_at` - Account creation timestamp

### Experiments Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `name` - Experiment name
- `description` - Optional description
- `input_path` - Input directory path
- `output_path` - Output directory path
- `parameters` - JSON blob of pipeline parameters
- `status` - Current status (created, running, completed, failed)
- `exit_code` - Process exit code
- `log_file` - Path to saved log file
- `created_at` - Creation timestamp
- `started_at` - Execution start time
- `completed_at` - Execution completion time

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Submit credentials
- `GET /logout` - Logout

### Experiment Management
- `GET /dashboard` - User dashboard with experiment list
- `GET /experiment/new` - New experiment form
- `GET /experiment/<id>` - View experiment details
- `GET /experiment/<id>/edit` - Edit experiment form
- `POST /experiment/<id>/delete` - Delete experiment
- `POST /api/experiment/create` - Create new experiment
- `POST /api/experiment/<id>/run` - Run pipeline for experiment

### Pipeline Control
- `GET /api/logs` - Fetch current log buffer
- `GET /api/status` - Get pipeline execution status
- `GET /api/stream` - Server-sent events for live logs
- `GET /api/detect_frames` - Auto-detect frame count
- `GET /api/experiments` - List all user experiments

## Configuration

### Environment Variables

```bash
# Secret key for session management (REQUIRED in production)
export SECRET_KEY="your-secure-random-key-here"

# Database URI (default: SQLite in current directory)
export SQLALCHEMY_DATABASE_URI="sqlite:///pico_experiments.db"
```

### Production Deployment

For production use:

1. **Change secret key:**
   ```bash
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   ```

2. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app_multiuser:app
   ```

3. **Configure reverse proxy** (nginx/Apache) with HTTPS

4. **Update default users** or disable auto-creation in `database.py`

5. **Set up proper database backups** for the SQLite file

## Differences from Original Single-User Version

| Feature | Original (`app.py`) | Multi-User (`app_multiuser.py`) |
|---------|---------------------|----------------------------------|
| Authentication | None | Login required |
| Experiment Tracking | No | Full history with metadata |
| Log Persistence | In-memory only | Auto-saved to disk |
| Multiple Users | No | Yes, with isolation |
| Experiment Naming | No | Required for each experiment |
| Parameter History | No | Saved with each experiment |
| Re-run Capability | No | Edit and re-run previous experiments |

## Troubleshooting

### "Pipeline script not found"
- Ensure `somm_processingv1.py` exists in the parent directory
- Check the `PIPELINE_SCRIPT` path in `app_multiuser.py`

### Cannot login
- Check default credentials
- Ensure database was created (look for `pico_experiments.db`)
- Delete database file to recreate with fresh users

### Logs not appearing
- Check `experiment_logs/` directory exists and is writable
- Verify log file path in experiment details
- Check file permissions

### Pipeline fails to start
- Verify input/output paths are valid
- Check that the PICO conda environment is activated
- Review terminal output for specific errors

## License

Part of the PICO calcium imaging processing pipeline.
