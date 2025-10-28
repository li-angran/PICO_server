#!/usr/bin/env python3
"""Multi-user web interface for running the PICO calcium processing pipeline."""

from __future__ import annotations

import os
import queue
import shlex
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request, Response, redirect, url_for, session, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from database import db, init_db, User, Experiment

# Flask app configuration
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pico_experiments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
init_db(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Paths and global state
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = PROJECT_ROOT / "process_script.py"
LOGS_DIR = Path(__file__).resolve().parent / "experiment_logs"
LOGS_DIR.mkdir(exist_ok=True)

_history_lock = threading.Lock()
_process_lock = threading.Lock()
_log_history: list[str] = []
_log_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
_LOG_HISTORY_MAX = 10000
_current_process: Optional[subprocess.Popen[str]] = None
_current_experiment_id: Optional[int] = None
_last_exit_code: Optional[int] = None
_log_file_handle: Optional[Any] = None


@login_manager.user_loader
def load_user(user_id: int):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


def _append_log(message: str) -> None:
    """Store a log message and notify any listeners."""
    sanitized = message.rstrip("\n")
    with _history_lock:
        _log_history.append(sanitized)
        overflow = len(_log_history) - _LOG_HISTORY_MAX
        if overflow > 0:
            del _log_history[:overflow]
    
    # Write to log file if available
    global _log_file_handle
    if _log_file_handle:
        try:
            _log_file_handle.write(sanitized + "\n")
            _log_file_handle.flush()
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    _log_queue.put({"type": "line", "data": sanitized})


def _reset_logs() -> None:
    """Clear existing logs and pending queue items."""
    with _history_lock:
        _log_history.clear()
    while not _log_queue.empty():
        try:
            _log_queue.get_nowait()
        except queue.Empty:
            break


def _monitor_process(proc: subprocess.Popen[str], experiment_id: int) -> None:
    """Stream the pipeline output until completion."""
    global _current_process, _last_exit_code, _log_file_handle

    try:
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            _append_log(raw_line)
    finally:
        if proc.stdout is not None:
            proc.stdout.close()
        return_code = proc.wait()
        _last_exit_code = return_code
        _append_log(f"Pipeline finished with exit code {return_code}")
        _log_queue.put({"type": "done", "code": return_code})
        
        # Close log file
        if _log_file_handle:
            try:
                _log_file_handle.close()
                _log_file_handle = None
            except Exception:
                pass
        
        # Update experiment status
        with app.app_context():
            experiment = Experiment.query.get(experiment_id)
            if experiment:
                experiment.status = "completed" if return_code == 0 else "failed"
                experiment.exit_code = return_code
                experiment.completed_at = datetime.utcnow()
                db.session.commit()
        
        with _process_lock:
            _current_process = None


@app.route("/")
def index() -> Any:
    """Redirect to login or dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login() -> Any:
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        else:
            flash("Invalid username or password", "error")
    
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout() -> Any:
    """User logout."""
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard() -> str:
    """Render the main dashboard with experiment list."""
    experiments = Experiment.query.filter_by(user_id=current_user.id).order_by(Experiment.created_at.desc()).limit(50).all()
    return render_template("dashboard.html", experiments=experiments)


@app.route("/experiment/new")
@login_required
def new_experiment() -> str:
    """Render the new experiment form."""
    defaults = {
        "input_path": "",
        "output_path": "",
        "script_exists": PIPELINE_SCRIPT.exists(),
    }
    return render_template("experiment_form.html", defaults=defaults, experiment=None)


@app.route("/experiment/<int:experiment_id>")
@login_required
def view_experiment(experiment_id: int) -> Any:
    """View experiment details."""
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check ownership
    if experiment.user_id != current_user.id:
        flash("You don't have permission to view this experiment", "error")
        return redirect(url_for("dashboard"))
    
    # Read log file if it exists
    log_content = ""
    if experiment.log_file:
        log_path = Path(experiment.log_file)
        if log_path.exists():
            try:
                with open(log_path, "r") as f:
                    log_content = f.read()
            except Exception as e:
                log_content = f"Error reading log file: {e}"
    
    return render_template("experiment_detail.html", experiment=experiment, log_content=log_content)


@app.route("/experiment/<int:experiment_id>/edit")
@login_required
def edit_experiment(experiment_id: int) -> Any:
    """Edit an existing experiment."""
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check ownership
    if experiment.user_id != current_user.id:
        flash("You don't have permission to edit this experiment", "error")
        return redirect(url_for("dashboard"))
    
    # Can only edit experiments that are not running
    if experiment.status == "running":
        flash("Cannot edit a running experiment", "error")
        return redirect(url_for("view_experiment", experiment_id=experiment_id))
    
    defaults = {
        "input_path": experiment.input_path,
        "output_path": experiment.output_path,
        "script_exists": PIPELINE_SCRIPT.exists(),
    }
    
    return render_template("experiment_form.html", defaults=defaults, experiment=experiment)


@app.route("/experiment/<int:experiment_id>/download_log")
@login_required
def download_log(experiment_id: int) -> Any:
    """Download the log file for an experiment."""
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check ownership
    if experiment.user_id != current_user.id:
        flash("You don't have permission to download this log", "error")
        return redirect(url_for("dashboard"))
    
    if not experiment.log_file:
        flash("No log file available for this experiment", "error")
        return redirect(url_for("view_experiment", experiment_id=experiment_id))
    
    log_path = Path(experiment.log_file)
    if not log_path.exists():
        flash("Log file not found", "error")
        return redirect(url_for("view_experiment", experiment_id=experiment_id))
    
    return send_file(
        log_path,
        as_attachment=True,
        download_name=f"{experiment.name}_log_{experiment.id}.log",
        mimetype="text/plain"
    )


@app.route("/experiment/<int:experiment_id>/delete", methods=["POST"])
@login_required
def delete_experiment(experiment_id: int) -> Any:
    """Delete an experiment."""
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check ownership
    if experiment.user_id != current_user.id:
        return jsonify({"ok": False, "message": "Permission denied"}), 403
    
    # Cannot delete running experiments
    if experiment.status == "running":
        return jsonify({"ok": False, "message": "Cannot delete running experiment"}), 400
    
    # Delete log file
    if experiment.log_file:
        log_path = Path(experiment.log_file)
        if log_path.exists():
            try:
                log_path.unlink()
            except Exception as e:
                print(f"Error deleting log file: {e}")
    
    db.session.delete(experiment)
    db.session.commit()
    
    return jsonify({"ok": True, "message": "Experiment deleted"})


@app.post("/api/experiment/<int:experiment_id>/update")
@login_required
def update_experiment(experiment_id: int) -> Response:
    """Update an experiment's basic information and parameters without running."""
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check ownership
    if experiment.user_id != current_user.id:
        return jsonify({"ok": False, "message": "Permission denied"}), 403
    
    payload = request.get_json(silent=True) or request.form
    
    name = (payload.get("name") or "").strip()
    description = (payload.get("description") or "").strip()
    
    if name:
        experiment.name = name
    if "description" in payload:
        experiment.description = description
    
    db.session.commit()
    
    return jsonify({"ok": True, "message": "Experiment updated", "experiment_id": experiment.id})


@app.post("/api/experiment/create")
@login_required
def create_experiment() -> Response:
    """Create a new experiment."""
    payload = request.get_json(silent=True) or request.form
    
    name = (payload.get("name") or "").strip()
    description = (payload.get("description") or "").strip()
    
    if not name:
        return jsonify({"ok": False, "message": "Experiment name is required"}), 400
    
    # Create experiment
    experiment = Experiment(
        user_id=current_user.id,
        name=name,
        description=description,
        input_path="",
        output_path="",
        status="created"
    )
    
    db.session.add(experiment)
    db.session.commit()
    
    return jsonify({"ok": True, "experiment_id": experiment.id, "message": "Experiment created"})


@app.post("/api/experiment/<int:experiment_id>/stop")
@login_required
def stop_experiment(experiment_id: int) -> Response:
    """Stop a running experiment."""
    global _current_process, _current_experiment_id
    
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check ownership
    if experiment.user_id != current_user.id:
        return jsonify({"ok": False, "message": "Permission denied"}), 403
    
    with _process_lock:
        if _current_process and _current_process.poll() is None and _current_experiment_id == experiment_id:
            try:
                _current_process.terminate()
                _append_log("Pipeline stopped by user")
                
                # Update experiment status
                experiment.status = "failed"
                experiment.exit_code = -1
                experiment.completed_at = datetime.utcnow()
                db.session.commit()
                
                return jsonify({"ok": True, "message": "Experiment stopped"})
            except Exception as e:
                return jsonify({"ok": False, "message": f"Failed to stop: {e}"}), 500
        else:
            return jsonify({"ok": False, "message": "No running experiment found"}), 400


@app.post("/api/experiment/<int:experiment_id>/run")
@login_required
def run_experiment(experiment_id: int) -> Response:
    """Run a pipeline for an experiment."""
    global _current_process, _last_exit_code, _current_experiment_id, _log_file_handle
    
    experiment = Experiment.query.get_or_404(experiment_id)
    
    # Check ownership
    if experiment.user_id != current_user.id:
        return jsonify({"ok": False, "message": "Permission denied"}), 403
    
    payload = request.get_json(silent=True) or request.form

    input_raw = (payload.get("input_path") or "").strip()
    output_raw = (payload.get("output_path") or "").strip()

    if not input_raw or not output_raw:
        return jsonify({"ok": False, "message": "Both input and output paths are required."}), 400

    input_path = Path(os.path.expanduser(input_raw)).resolve()
    output_path = Path(os.path.expanduser(output_raw)).resolve()

    if not input_path.exists() or not input_path.is_dir():
        return (
            jsonify({"ok": False, "message": f"Input path '{input_path}' does not exist or is not a directory."}),
            400,
        )

    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return jsonify({"ok": False, "message": f"Unable to create output path: {exc}"}), 400

    if not PIPELINE_SCRIPT.exists():
        return (
            jsonify({"ok": False, "message": f"Pipeline script not found at {PIPELINE_SCRIPT}"}),
            500,
        )

    with _process_lock:
        if _current_process and _current_process.poll() is None:
            return jsonify({"ok": False, "message": "Another pipeline is already running."}), 409

        _reset_logs()
        _last_exit_code = None
        _current_experiment_id = experiment_id

        # Create log file for this experiment
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"exp_{experiment_id}_{timestamp}.log"
        log_filepath = LOGS_DIR / log_filename
        
        try:
            _log_file_handle = open(log_filepath, "w")
        except Exception as e:
            return jsonify({"ok": False, "message": f"Failed to create log file: {e}"}), 500

        # Update experiment
        experiment.input_path = str(input_path)
        experiment.output_path = str(output_path)
        experiment.status = "running"
        experiment.started_at = datetime.utcnow()
        experiment.log_file = str(log_filepath)
        
        # Store parameters
        parameters = {}
        for key in payload.keys():
            if key not in ["input_path", "output_path"]:
                parameters[key] = payload.get(key)
        experiment.parameters = parameters
        
        db.session.commit()

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        cmd: list[str] = [
            sys.executable,
            str(PIPELINE_SCRIPT),
            "--data_path",
            str(input_path),
            "--out_path",
            str(output_path),
        ]

        # Build command with all parameters (same logic as original)
        bool_keys = [
            "jump_to_rmbg", "jump_to_seg", "jump_to_vis", "save_movie", "pw_rigid",
            "shifts_opencv", "intensity_corr_flag", "bad_frame_detect_flag",
        ]
        int_keys = [
            "set_frame_num", "fr", "mc_chunk_size", "num_frames_split", "max_deviation_rigid",
            "up_sample", "rmbg_chunk_size", "rmbg_gsize", "patch_size", "pixel_size",
            "minArea", "avgArea", "thresh_pmap", "thresh_COM0", "thresh_COM", "cons", "avi_quality",
        ]
        float_keys = ["downsample_ratio", "thresh_mask"]
        str_keys = ["border_nan", "ckpt_pth", "device", "gpu_ids"]
        tuple_keys = ["max_shifts", "strides", "overlaps"]
        list_multi_token = {"crop_parameter": int}

        def _has_value(key: str) -> bool:
            val = payload.get(key)
            return val is not None and str(val).strip() != ""

        # Handle auto frame detection
        if str(payload.get("auto_set_frame") or "").lower() in {"true", "1", "yes", "on"}:
            if not (payload.get("set_frame_num") and str(payload.get("set_frame_num")).strip()):
                payload = dict(payload)
                payload["set_frame_num"] = 0

        # Booleans
        for k in bool_keys:
            if k in payload:
                val = payload.get(k)
                if isinstance(val, str):
                    val_norm = val.lower() in {"true", "1", "yes", "on"}
                else:
                    val_norm = bool(val)
                cmd.extend([f"--{k}", "true" if val_norm else "false"])

        # Integers
        for k in int_keys:
            if _has_value(k):
                try:
                    cmd.extend([f"--{k}", str(int(payload.get(k)))])
                except Exception:
                    return jsonify({"ok": False, "message": f"Invalid integer for {k}."}), 400

        # Floats
        for k in float_keys:
            if _has_value(k):
                try:
                    cmd.extend([f"--{k}", str(float(payload.get(k)))])
                except Exception:
                    return jsonify({"ok": False, "message": f"Invalid float for {k}."}), 400

        # Strings
        for k in str_keys:
            if _has_value(k):
                cmd.extend([f"--{k}", str(payload.get(k)).strip()])

        # Tuples
        for k in tuple_keys:
            if _has_value(k):
                raw = str(payload.get(k)).strip()
                raw = raw.strip().strip("()")
                cmd.extend([f"--{k}", raw])

        # Lists
        for k, caster in list_multi_token.items():
            if _has_value(k):
                raw = str(payload.get(k))
                parts = [p for p in raw.replace("[", "").replace("]", "").replace("(", "").replace(")", "").replace("\n", " ").replace("\t", " ").replace(";", ",").replace(" ", ",").split(",") if p != ""]
                try:
                    casted = [str(caster(p)) for p in parts]
                except Exception:
                    return jsonify({"ok": False, "message": f"Invalid list for {k}. Provide comma-separated integers."}), 400
                if casted:
                    cmd.append(f"--{k}")
                    cmd.extend(casted)

        _append_log(f"Starting pipeline for experiment {experiment.name} (ID: {experiment_id})")
        _append_log(f"User: {current_user.username}")
        _append_log(f"Project root: {PROJECT_ROOT}")
        _append_log("Command: " + " ".join(shlex.quote(part) for part in cmd))

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )
        except Exception as exc:
            _append_log(f"Failed to start pipeline: {exc}")
            _log_queue.put({"type": "done", "code": -1})
            _last_exit_code = -1
            
            # Update experiment status
            experiment.status = "failed"
            experiment.exit_code = -1
            experiment.completed_at = datetime.utcnow()
            db.session.commit()
            
            if _log_file_handle:
                _log_file_handle.close()
                _log_file_handle = None
            
            return jsonify({"ok": False, "message": f"Failed to start pipeline: {exc}"}), 500

        _current_process = proc
        threading.Thread(target=_monitor_process, args=(proc, experiment_id), daemon=True).start()

    return jsonify({"ok": True, "message": "Pipeline started.", "running": True})


@app.get("/api/logs")
@login_required
def fetch_logs() -> Response:
    """Return the current log buffer."""
    with _history_lock:
        logs = list(_log_history)
    return jsonify({"logs": logs})


@app.get("/api/status")
@login_required
def fetch_status() -> Response:
    """Expose whether the pipeline is running and the last exit code."""
    with _process_lock:
        running = _current_process is not None and _current_process.poll() is None
        experiment_id = _current_experiment_id
    return jsonify({
        "running": running,
        "exit_code": _last_exit_code,
        "experiment_id": experiment_id
    })


@app.get("/api/stream")
@login_required
def stream_logs() -> Response:
    """Server-sent events feed for live log updates."""

    def event_stream() -> Any:
        while True:
            try:
                item = _log_queue.get(timeout=1.0)
            except queue.Empty:
                yield ": keepalive\n\n"
                continue

            item_type = item.get("type")
            if item_type == "line":
                data = item.get("data", "")
                yield f"data: {data}\n\n"
            elif item_type == "done":
                code = item.get("code")
                yield f"event: done\ndata: {code}\n\n"
            else:
                yield f"data: {item}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


@app.get("/api/detect_frames")
@login_required
def detect_frames() -> Response:
    """Detect number of frames in an input directory."""
    payload = request.args or request.get_json(silent=True) or {}
    input_raw = (payload.get("input_path") or "").strip()
    if not input_raw:
        return jsonify({"ok": False, "message": "Provide input_path."}), 400
    input_path = Path(os.path.expanduser(input_raw)).resolve()
    if not input_path.exists() or not input_path.is_dir():
        return jsonify({"ok": False, "message": f"Input path '{input_path}' is not a directory."}), 400

    exts = [".tif", ".tiff", ".jpg", ".jpeg", ".png"]
    counts: Dict[str, int] = {}
    total = 0
    try:
        for ext in exts:
            c = sum(1 for _ in input_path.glob(f"*{ext}")) + sum(1 for _ in input_path.glob(f"*{ext.upper()}"))
            counts[ext] = c
            total += c
    except Exception as exc:
        return jsonify({"ok": False, "message": f"Failed to scan directory: {exc}"}), 500

    return jsonify({"ok": True, "frames": total, "counts": counts})


@app.get("/api/experiments")
@login_required
def list_experiments() -> Response:
    """List all experiments for the current user."""
    experiments = Experiment.query.filter_by(user_id=current_user.id).order_by(Experiment.created_at.desc()).all()
    return jsonify({"experiments": [exp.to_dict() for exp in experiments]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=False)
