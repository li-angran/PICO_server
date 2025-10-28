# System Architecture - Multi-User PICO Pipeline

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browsers                            │
│            (User 1)    (User 2)    (User N)                     │
└──────────────────┬──────────┬──────────┬───────────────────────┘
                   │          │          │
                   │   HTTPS  │          │
                   ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Flask Application                           │
│                   (app_multiuser.py)                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Routes     │  │    Auth      │  │   Pipeline   │         │
│  │  /dashboard  │  │ Flask-Login  │  │   Control    │         │
│  │  /experiment │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────┬───────────────────┬───────────────┬──────────────┘
              │                   │               │
              │                   │               │
              ▼                   ▼               ▼
┌─────────────────────┐  ┌────────────────┐  ┌─────────────────┐
│   SQLite Database   │  │  Subprocess    │  │   File System   │
│ pico_experiments.db │  │  Management    │  │ experiment_logs/│
│                     │  │                │  │  exp_*.log      │
│  ┏━━━━━━━━━━━━┓    │  │  Pipeline      │  └─────────────────┘
│  ┃   Users    ┃    │  │  Execution     │
│  ┣━━━━━━━━━━━━┫    │  │                │
│  ┃ Experiments┃    │  │  Log Stream    │
│  ┗━━━━━━━━━━━━┛    │  └────────────────┘
└─────────────────────┘
```

## Component Details

### 1. Web Browser Layer
```
┌─────────────────────────────────────┐
│        User Interface               │
├─────────────────────────────────────┤
│ • Login Page                        │
│ • Dashboard (Experiment List)       │
│ • Experiment Form (Create/Edit)     │
│ • Experiment Detail (View Logs)     │
│ • Real-time Log Streaming (SSE)     │
└─────────────────────────────────────┘
```

### 2. Flask Application
```
┌─────────────────────────────────────────────┐
│           app_multiuser.py                  │
├─────────────────────────────────────────────┤
│                                             │
│  Authentication Layer                       │
│  ├── @login_required decorator              │
│  ├── Session management                     │
│  └── Password verification                  │
│                                             │
│  Route Handlers                             │
│  ├── /login, /logout                        │
│  ├── /dashboard                             │
│  ├── /experiment/*                          │
│  └── /api/*                                 │
│                                             │
│  Business Logic                             │
│  ├── Experiment CRUD                        │
│  ├── Pipeline execution                     │
│  ├── Log management                         │
│  └── Real-time streaming                    │
│                                             │
└─────────────────────────────────────────────┘
```

### 3. Database Layer
```
┌─────────────────────────────────────────────┐
│           database.py                       │
├─────────────────────────────────────────────┤
│                                             │
│  ORM Models (SQLAlchemy)                    │
│  ├── User                                   │
│  │   ├── id, username, password_hash       │
│  │   └── experiments (relationship)        │
│  │                                          │
│  └── Experiment                             │
│      ├── id, user_id, name, description    │
│      ├── input_path, output_path           │
│      ├── parameters (JSON)                  │
│      ├── status, exit_code                  │
│      ├── log_file                           │
│      └── timestamps                         │
│                                             │
└─────────────────────────────────────────────┘
```

## Data Flow

### User Login Flow
```
Browser              Flask                Database
   │                  │                     │
   │──── POST /login ─→                    │
   │                  │                     │
   │                  │─── Query User ─────→
   │                  │←── User Record ─────│
   │                  │                     │
   │                  │ Verify Password     │
   │                  │ Create Session      │
   │                  │                     │
   │←─ Redirect /dashboard ─               │
   │                  │                     │
```

### Create & Run Experiment Flow
```
Browser              Flask                Database         Subprocess
   │                  │                     │                  │
   │── Create Exp ───→│                     │                  │
   │                  │─── Insert Exp ─────→                  │
   │                  │←── Exp ID ──────────│                  │
   │                  │                     │                  │
   │── Run Pipeline ─→│                     │                  │
   │                  │─── Update Status ──→                  │
   │                  │    (running)        │                  │
   │                  │                     │                  │
   │                  │─── Start Pipeline ─────────────────→  │
   │                  │                     │                  │
   │← SSE Stream ─────│←─── Stdout ───────────────────────────│
   │  (real-time)     │                     │                  │
   │                  │                     │                  │
   │                  │ Write to Log File   │                  │
   │                  │ experiment_logs/    │                  │
   │                  │                     │                  │
   │                  │←─── Exit Code ────────────────────────│
   │                  │                     │                  │
   │                  │─── Update Status ──→                  │
   │                  │    (completed)      │                  │
   │                  │─── Set exit_code ──→                  │
   │                  │─── Set log_file ───→                  │
   │                  │                     │                  │
```

### View Experiment History
```
Browser              Flask                Database         Filesystem
   │                  │                     │                  │
   │── GET /dashboard →                     │                  │
   │                  │                     │                  │
   │                  │─── Query Exps ─────→                  │
   │                  │    (user_id)        │                  │
   │                  │←── Exp List ────────│                  │
   │                  │                     │                  │
   │← Render Dashboard                      │                  │
   │                  │                     │                  │
   │── GET /exp/123 ─→│                     │                  │
   │                  │─── Query Exp ──────→                  │
   │                  │←── Exp Data ────────│                  │
   │                  │                     │                  │
   │                  │─── Read Log File ──────────────────→  │
   │                  │←── Log Content ────────────────────────│
   │                  │                     │                  │
   │← Render Detail ──│                     │                  │
   │                  │                     │                  │
```

## Concurrency Model

```
┌──────────────────────────────────────────────────┐
│            Main Flask Thread                     │
│  (Handles HTTP requests)                         │
└──────────┬───────────────────────────────────────┘
           │
           │ Spawn on pipeline start
           ▼
┌──────────────────────────────────────────────────┐
│        Pipeline Monitor Thread                   │
│  (Reads subprocess output)                       │
│                                                  │
│  • Streams stdout line by line                   │
│  • Writes to log file                            │
│  • Queues messages for SSE                       │
│  • Updates database on completion                │
└──────────────────────────────────────────────────┘
           │
           │ Communicates via
           ▼
┌──────────────────────────────────────────────────┐
│         Thread-Safe Queue                        │
│  (Log messages for SSE streaming)                │
└──────────────────────────────────────────────────┘
           │
           │ Consumed by
           ▼
┌──────────────────────────────────────────────────┐
│         SSE Event Stream                         │
│  (GET /api/stream)                               │
│                                                  │
│  • Blocks on queue.get()                         │
│  • Yields Server-Sent Events                     │
│  • Keeps connection open                         │
└──────────────────────────────────────────────────┘
```

## File System Layout

```
website/
├── app_multiuser.py          ← Main application
├── database.py               ← ORM models
├── start_multiuser.sh        ← Startup script
│
├── pico_experiments.db       ← SQLite database (auto-created)
│
├── experiment_logs/          ← Log file directory (auto-created)
│   ├── exp_1_20241028_143022.log
│   ├── exp_1_20241028_150315.log
│   ├── exp_2_20241028_161045.log
│   └── ...
│
├── templates/                ← Jinja2 templates
│   ├── login.html           ← Login page
│   ├── dashboard.html       ← Experiment list
│   ├── experiment_form.html ← Create/edit form
│   ├── experiment_detail.html ← View logs
│   └── index.html           ← Original (unused)
│
└── static/                   ← Static files (if any)
```

## Security Architecture

```
┌─────────────────────────────────────────────┐
│           Security Layers                   │
├─────────────────────────────────────────────┤
│                                             │
│  1. Session Management                      │
│     • Flask secret key                      │
│     • Secure cookies                        │
│     • Session timeout                       │
│                                             │
│  2. Password Security                       │
│     • Werkzeug password hashing             │
│     • Salted hashes                         │
│     • Never store plaintext                 │
│                                             │
│  3. Authentication                          │
│     • Flask-Login integration               │
│     • @login_required decorators            │
│     • User loader callback                  │
│                                             │
│  4. Authorization                           │
│     • User ownership checks                 │
│     • Experiment isolation                  │
│     • No cross-user access                  │
│                                             │
│  5. Input Validation                        │
│     • Path validation                       │
│     • Parameter type checking               │
│     • SQL injection prevention (ORM)        │
│                                             │
└─────────────────────────────────────────────┘
```

## State Management

### Experiment States
```
                    ┌─────────┐
                    │ CREATED │
                    └────┬────┘
                         │
                    Click "Run"
                         │
                         ▼
                    ┌─────────┐
                    │ RUNNING │
                    └────┬────┘
                         │
                Pipeline completes
                         │
              ┌──────────┴──────────┐
              │                     │
         Exit code 0           Exit code != 0
              │                     │
              ▼                     ▼
         ┌──────────┐          ┌────────┐
         │COMPLETED │          │ FAILED │
         └──────────┘          └────────┘
```

### Global Process State
```
_current_process: None | Popen
    ↓
    Currently running pipeline subprocess

_current_experiment_id: None | int
    ↓
    ID of experiment being executed

_log_queue: Queue
    ↓
    Thread-safe queue for SSE streaming

_log_history: List[str]
    ↓
    In-memory buffer (last N lines)

_log_file_handle: None | File
    ↓
    Open file handle for current run
```

## Scalability Considerations

### Current Design (Single Server)
- SQLite database (suitable for < 100 concurrent users)
- Single process execution (one pipeline at a time)
- In-memory log buffer (limited history)
- File-based log storage (efficient for reads)

### Future Scaling Options

**Horizontal Scaling:**
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Flask 1  │     │ Flask 2  │     │ Flask 3  │
└─────┬────┘     └─────┬────┘     └─────┬────┘
      │                │                │
      └────────────────┼────────────────┘
                       │
              ┌────────▼────────┐
              │  Load Balancer  │
              └────────┬────────┘
                       │
      ┌────────────────┼────────────────┐
      │                │                │
┌─────▼────┐   ┌───────▼──────┐  ┌─────▼────┐
│PostgreSQL│   │ Redis/RabbitMQ│  │ Shared   │
│          │   │ (Job Queue)   │  │ Storage  │
└──────────┘   └──────────────┘  └──────────┘
```

**Task Queue Architecture:**
```
Web Server ──→ Queue Job ──→ Worker Nodes ──→ Store Results
                              (Celery)
```

## Deployment Architecture

### Development (Current)
```
┌────────────────────────────────┐
│   localhost:5000               │
│                                │
│   Flask Development Server     │
│   • Debug mode                 │
│   • Auto-reload                │
│   • Single threaded            │
└────────────────────────────────┘
```

### Production (Recommended)
```
Internet
   │
   ▼
┌────────────────────────────────┐
│    Nginx / Apache              │
│    • SSL/TLS termination       │
│    • Static file serving       │
│    • Rate limiting             │
└──────────┬─────────────────────┘
           │ Reverse Proxy
           ▼
┌────────────────────────────────┐
│    Gunicorn / uWSGI            │
│    • 4-8 workers               │
│    • Process management        │
│    • Load balancing            │
└──────────┬─────────────────────┘
           │
           ▼
┌────────────────────────────────┐
│    Flask Application           │
│    app_multiuser.py            │
└────────────────────────────────┘
```

---

This architecture supports the current requirements while maintaining flexibility for future enhancements. The modular design allows individual components to be upgraded or replaced as needed.
