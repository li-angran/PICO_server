# Multi-User Website - What's New

## Overview

The enhanced PICO pipeline website now supports multiple users with full authentication, experiment tracking, and automatic log saving. Users can log in from any device, create experiments, and view their complete history.

## Key Changes

### ✅ New Features Added

1. **User Authentication System**
   - Secure login/logout
   - Password hashing with Werkzeug
   - Session management
   - Pre-configured demo accounts

2. **Experiment Management**
   - Create named experiments with descriptions
   - View experiment history
   - Edit and re-run previous experiments
   - Delete old experiments
   - Full experiment metadata tracking

3. **Automatic Log Saving**
   - All pipeline output saved to disk
   - Logs stored in `experiment_logs/` directory
   - Persistent across sessions
   - Viewable from experiment detail page

4. **Database Integration**
   - SQLite database for persistence
   - User table with secure passwords
   - Experiment table with full tracking
   - Automatic schema creation

5. **Enhanced UI**
   - Modern dashboard with experiment cards
   - Login page with demo credentials
   - Experiment detail view with logs
   - Breadcrumb navigation
   - Status badges for experiment states

## File Structure Comparison

### Before (Single User)
```
website/
├── app.py                    # Simple Flask app
├── templates/
│   └── index.html           # Single page interface
└── static/                  # (if any)
```

### After (Multi User)
```
website/
├── app_multiuser.py              # Enhanced Flask app with auth
├── database.py                   # Database models & ORM
├── pico_experiments.db          # SQLite database (auto-created)
├── experiment_logs/             # Saved log files (auto-created)
│   └── exp_*_*.log
├── requirements_multiuser.txt   # New dependencies
├── start_multiuser.sh          # Startup script
├── README_MULTIUSER.md         # Full documentation
├── QUICKSTART.md              # Quick start guide
├── templates/
│   ├── login.html             # Login page (NEW)
│   ├── dashboard.html         # Experiment list (NEW)
│   ├── experiment_form.html   # Create/edit form (NEW)
│   ├── experiment_detail.html # View logs/details (NEW)
│   └── index.html            # Original (unchanged)
└── app.py                     # Original (unchanged)
```

## Features Comparison

| Feature | Original | Multi-User |
|---------|----------|------------|
| User Login | ❌ None | ✅ Required with secure passwords |
| Multiple Users | ❌ No | ✅ Isolated per user |
| Experiment Naming | ❌ No | ✅ Required with descriptions |
| Experiment History | ❌ No | ✅ Full history with filtering |
| Log Persistence | ❌ Memory only | ✅ Auto-saved to disk |
| Parameter Tracking | ❌ No | ✅ JSON storage per experiment |
| Edit & Re-run | ❌ No | ✅ Full edit capability |
| Status Tracking | ❌ Basic | ✅ Created/Running/Completed/Failed |
| Timestamps | ❌ No | ✅ Created/Started/Completed |
| Database | ❌ None | ✅ SQLite with migrations |
| Access Control | ❌ None | ✅ User-based isolation |

## User Workflow Comparison

### Original Workflow
1. Open website at `localhost:5000`
2. Enter input/output paths
3. Configure parameters
4. Run pipeline
5. Watch logs (lost after page refresh)
6. Done ❌ (no history)

### New Multi-User Workflow
1. Open website at `localhost:5000`
2. **Login with username/password** 🔐
3. View **dashboard** with all experiments 📊
4. Click **"+ New Experiment"**
5. Name experiment and add description 📝
6. Enter input/output paths
7. Configure parameters
8. **Create & Run**
9. Watch real-time logs
10. Logs **automatically saved** 💾
11. View **history** at any time 📚
12. **Re-run** or **edit** previous experiments ♻️
13. **Access from any device** 🌐

## Technical Implementation Details

### Authentication Flow
```
Login Page → Verify Credentials → Create Session → Dashboard
                    ↓
             Invalid? → Show Error
```

### Experiment Lifecycle
```
Create → Created Status → Run → Running Status → Complete
                                       ↓
                              Failed/Completed Status
                                       ↓
                              Logs Saved to Disk
```

### Database Schema

**Users Table:**
- id (primary key)
- username (unique)
- password_hash
- created_at

**Experiments Table:**
- id (primary key)
- user_id (foreign key)
- name
- description
- input_path
- output_path
- parameters (JSON)
- status
- exit_code
- log_file
- created_at
- started_at
- completed_at

## API Endpoints

### New Endpoints
```
Authentication:
  GET  /login                      - Login page
  POST /login                      - Submit credentials
  GET  /logout                     - Logout

Experiment Management:
  GET  /dashboard                  - User dashboard
  GET  /experiment/new             - New experiment form
  GET  /experiment/<id>            - View experiment
  GET  /experiment/<id>/edit       - Edit experiment
  POST /experiment/<id>/delete     - Delete experiment
  POST /api/experiment/create      - Create new
  POST /api/experiment/<id>/run    - Run pipeline
  GET  /api/experiments            - List all user experiments

Pipeline Control:
  GET  /api/logs                   - Current log buffer
  GET  /api/status                 - Execution status
  GET  /api/stream                 - Live log stream (SSE)
  GET  /api/detect_frames          - Auto-detect frames
```

### Original Endpoints (Still Available)
```
  GET  /                           - Main page (now redirects to login)
  POST /run                        - Start pipeline
  GET  /logs                       - Fetch logs
  GET  /status                     - Pipeline status
  GET  /stream                     - Log stream
  GET  /detect_frames              - Frame detection
```

## Security Enhancements

1. **Password Hashing**: Using Werkzeug's secure password hashing
2. **Session Management**: Flask-Login for secure sessions
3. **CSRF Protection**: Built into Flask forms
4. **User Isolation**: Each user sees only their experiments
5. **Login Required**: All routes protected except login page

## Migration Path

### Keeping Original Version
The original `app.py` and `templates/index.html` remain unchanged. You can run either:

**Original (no auth):**
```bash
python app.py
```

**Multi-user (with auth):**
```bash
python app_multiuser.py
```

### Full Migration
To fully switch to multi-user:
1. Install new dependencies
2. Run `app_multiuser.py` instead of `app.py`
3. Update any automation scripts
4. Configure production settings

## Default User Accounts

| Username   | Password     | Purpose            |
|------------|--------------|---------------------|
| admin      | admin123     | Administrator       |
| user1      | user123      | Regular user        |
| user2      | user123      | Regular user        |
| researcher | research123  | Research account    |

**⚠️ Change these in production!**

## Log File Naming Convention

```
exp_{experiment_id}_{timestamp}.log
```

Example:
```
exp_1_20241028_143022.log
exp_1_20241028_150315.log  ← Same experiment, different run
exp_2_20241028_161045.log  ← Different experiment
```

## Performance Considerations

- SQLite database is suitable for moderate usage (100s of users, 1000s of experiments)
- Log files stored separately to avoid database bloat
- Indexes on user_id and created_at for fast queries
- In-memory log buffer for real-time streaming

## Future Enhancement Ideas

Potential additions (not implemented):
- User registration page
- Password reset functionality
- Experiment sharing between users
- User roles (admin, researcher, viewer)
- Experiment tags/categories
- Search and filtering
- Export experiment data
- Email notifications
- API authentication tokens
- PostgreSQL support for larger deployments

## Backward Compatibility

✅ Original `app.py` still works independently
✅ Original templates unchanged
✅ New files don't interfere with old setup
✅ Can run both versions simultaneously (different ports)

## Support

For questions or issues:
1. Check QUICKSTART.md for common problems
2. Review README_MULTIUSER.md for detailed docs
3. Examine terminal output for errors
4. Check database and log file permissions

---

**The website is now production-ready for multi-user lab environments!** 🎉
