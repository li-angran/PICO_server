#!/usr/bin/env python3
"""Simple web interface for running the PICO calcium processing pipeline."""

from __future__ import annotations

import os
import queue
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request, Response

# Flask app configuration
app = Flask(__name__, template_folder="templates", static_folder="static")

# Paths and global state
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = PROJECT_ROOT / "somm_processingv1.py"

_history_lock = threading.Lock()
_process_lock = threading.Lock()
_log_history: list[str] = []
_log_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
_LOG_HISTORY_MAX = 10000
_current_process: Optional[subprocess.Popen[str]] = None
_last_exit_code: Optional[int] = None


def _append_log(message: str) -> None:
    """Store a log message and notify any listeners."""
    sanitized = message.rstrip("\n")
    with _history_lock:
        _log_history.append(sanitized)
        overflow = len(_log_history) - _LOG_HISTORY_MAX
        if overflow > 0:
            del _log_history[:overflow]
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


def _monitor_process(proc: subprocess.Popen[str]) -> None:
    """Stream the pipeline output until completion."""
    global _current_process, _last_exit_code

    try:
        assert proc.stdout is not None  # keep mypy quiet
        for raw_line in proc.stdout:
            _append_log(raw_line)
    finally:
        if proc.stdout is not None:
            proc.stdout.close()
        return_code = proc.wait()
        _last_exit_code = return_code
        _append_log(f"Pipeline finished with exit code {return_code}")
        _log_queue.put({"type": "done", "code": return_code})
        with _process_lock:
            _current_process = None


@app.get("/")
def index() -> str:
    """Render the main dashboard."""
    defaults = {
        "input_path": "",
        "output_path": "",
        "script_exists": PIPELINE_SCRIPT.exists(),
    }
    return render_template("index.html", defaults=defaults)


@app.post("/run")
def run_pipeline() -> Response:
    """Kick off a pipeline run with the provided paths."""
    global _current_process, _last_exit_code

    payload = request.get_json(silent=True) or request.form

    input_raw = (payload.get("input_path") or "").strip()
    output_raw = (payload.get("output_path") or "").strip()
    # Optional advanced args
    # We accept additional fields matching somm_processingv1.py CLI args.
    # Types will be normalized below when building the command.

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
            return jsonify({"ok": False, "message": "Pipeline is already running."}), 409

        _reset_logs()
        _last_exit_code = None

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

        # Map of supported args and their types/formatters
        bool_keys = [
            "jump_to_rmbg",
            "jump_to_seg",
            "jump_to_vis",
            "save_movie",
            "pw_rigid",
            "shifts_opencv",
            "intensity_corr_flag",
            "bad_frame_detect_flag",
        ]
        int_keys = [
            "set_frame_num",
            "fr",
            "mc_chunk_size",
            "num_frames_split",
            "max_deviation_rigid",
            "up_sample",
            "rmbg_chunk_size",
            "rmbg_gsize",
            "patch_size",
            "pixel_size",
            "minArea",
            "avgArea",
            "thresh_pmap",
            "thresh_COM0",
            "thresh_COM",
            "cons",
            "avi_quality",
        ]
        float_keys = [
            "downsample_ratio",
            "thresh_mask",
        ]
        str_keys = [
            "border_nan",
            "ckpt_pth",
            "device",
            "gpu_ids",
        ]
        tuple_keys = [
            "max_shifts",
            "strides",
            "overlaps",
        ]
        list_multi_token = {
            # value is a comma or whitespace separated list of ints; we will split into multiple CLI tokens
            "crop_parameter": int,
        }

        def _has_value(key: str) -> bool:
            val = payload.get(key)
            return val is not None and str(val).strip() != ""

        # set_frame_num special handling for auto flag from UI: if auto==true and no explicit number, use 0
        if str(payload.get("auto_set_frame") or "").lower() in {"true", "1", "yes", "on"}:
            if not (payload.get("set_frame_num") and str(payload.get("set_frame_num")).strip()):
                payload = dict(payload)
                payload["set_frame_num"] = 0

        # Booleans -> 'true'/'false'
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

        # Tuples like "100,100" or "(100, 100)" pass as single string; parser accepts both
        for k in tuple_keys:
            if _has_value(k):
                raw = str(payload.get(k)).strip()
                # sanitize spaces
                raw = raw.strip().strip("()")
                cmd.extend([f"--{k}", raw])

        # List-like (multi-token)
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

        _append_log(f"Starting pipeline run at project root: {PROJECT_ROOT}")
        _append_log("Command: " + " ".join(shlex.quote(part) for part in cmd))

        try:
            proc = subprocess.Popen(  # noqa: PLW1510
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )
        except Exception as exc:  # pylint: disable=broad-except
            _append_log(f"Failed to start pipeline: {exc}")
            _log_queue.put({"type": "done", "code": -1})
            _last_exit_code = -1
            return jsonify({"ok": False, "message": f"Failed to start pipeline: {exc}"}), 500

        _current_process = proc
        threading.Thread(target=_monitor_process, args=(proc,), daemon=True).start()

    return jsonify({"ok": True, "message": "Pipeline started.", "running": True})


@app.get("/logs")
def fetch_logs() -> Response:
    """Return the current log buffer."""
    with _history_lock:
        logs = list(_log_history)
    return jsonify({"logs": logs})


@app.get("/status")
def fetch_status() -> Response:
    """Expose whether the pipeline is running and the last exit code."""
    with _process_lock:
        running = _current_process is not None and _current_process.poll() is None
    return jsonify({"running": running, "exit_code": _last_exit_code})


@app.get("/stream")
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


@app.get("/detect_frames")
def detect_frames() -> Response:
    """Detect number of frames in an input directory by scanning common image extensions."""
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
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"ok": False, "message": f"Failed to scan directory: {exc}"}), 500

    return jsonify({"ok": True, "frames": total, "counts": counts})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
