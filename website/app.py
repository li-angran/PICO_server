from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import subprocess
import json
import os
import signal
import psutil
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pico_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    experiments = db.relationship('Experiment', backref='user', lazy=True)

class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    parameters = db.Column(db.Text, nullable=False)  # JSON string
    gpu_id = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='created')  # created, running, completed, failed, stopped
    pid = db.Column(db.Integer, nullable=True)  # Process ID when running
    output_path = db.Column(db.String(500))
    log_file = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/experiments', methods=['GET'])
@login_required
def get_experiments():
    experiments = Experiment.query.filter_by(user_id=session['user_id']).order_by(Experiment.created_at.desc()).all()
    return jsonify([{
        'id': exp.id,
        'name': exp.name,
        'description': exp.description,
        'status': exp.status,
        'gpu_id': exp.gpu_id,
        'created_at': exp.created_at.isoformat(),
        'started_at': exp.started_at.isoformat() if exp.started_at else None,
        'completed_at': exp.completed_at.isoformat() if exp.completed_at else None,
        'output_path': exp.output_path
    } for exp in experiments])

@app.route('/api/experiments/<int:exp_id>', methods=['GET'])
@login_required
def get_experiment(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    return jsonify({
        'id': exp.id,
        'name': exp.name,
        'description': exp.description,
        'parameters': json.loads(exp.parameters),
        'gpu_id': exp.gpu_id,
        'status': exp.status,
        'pid': exp.pid,
        'output_path': exp.output_path,
        'log_file': exp.log_file,
        'created_at': exp.created_at.isoformat(),
        'started_at': exp.started_at.isoformat() if exp.started_at else None,
        'completed_at': exp.completed_at.isoformat() if exp.completed_at else None
    })

@app.route('/api/experiments', methods=['POST'])
@login_required
def create_experiment():
    data = request.get_json()
    
    # Create experiment
    experiment = Experiment(
        name=data['name'],
        description=data.get('description', ''),
        parameters=json.dumps(data['parameters']),
        gpu_id=data.get('gpu_id', 0),
        user_id=session['user_id']
    )
    
    db.session.add(experiment)
    db.session.commit()
    
    return jsonify({'success': True, 'id': experiment.id})

@app.route('/api/experiments/<int:exp_id>', methods=['PUT'])
@login_required
def update_experiment(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    if exp.status == 'running':
        return jsonify({'success': False, 'message': 'Cannot edit running experiment'}), 400
    
    data = request.get_json()
    exp.name = data.get('name', exp.name)
    exp.description = data.get('description', exp.description)
    exp.parameters = json.dumps(data.get('parameters', json.loads(exp.parameters)))
    exp.gpu_id = data.get('gpu_id', exp.gpu_id)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/experiments/<int:exp_id>/start', methods=['POST'])
@login_required
def start_experiment(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    if exp.status == 'running':
        return jsonify({'success': False, 'message': 'Experiment already running'}), 400
    
    # Parse parameters
    params = json.loads(exp.parameters)
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_base = os.path.join('experiments', f'exp_{exp.id}_{timestamp}')
    os.makedirs(output_base, exist_ok=True)
    
    # Update output path
    exp.output_path = output_base
    log_file = os.path.join(output_base, 'process.log')
    exp.log_file = log_file
    
    # Build command
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'process_script.py')
    cmd = ['python', script_path]
    
    # Add all parameters as command line arguments
    for key, value in params.items():
        if isinstance(value, bool):
            cmd.extend([f'--{key}', str(value).lower()])
        elif isinstance(value, list):
            cmd.extend([f'--{key}'] + [str(v) for v in value])
        else:
            cmd.extend([f'--{key}', str(value)])
    
    # Set GPU environment variable
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = str(exp.gpu_id)
    
    # Start process
    try:
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=os.path.dirname(script_path)
            )
        
        exp.pid = process.pid
        exp.status = 'running'
        exp.started_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'pid': process.pid})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/experiments/<int:exp_id>/stop', methods=['POST'])
@login_required
def stop_experiment(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    if exp.status != 'running':
        return jsonify({'success': False, 'message': 'Experiment not running'}), 400
    
    if exp.pid:
        try:
            # Kill process tree
            parent = psutil.Process(exp.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            
            exp.status = 'stopped'
            exp.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'success': True})
        except psutil.NoSuchProcess:
            exp.status = 'stopped'
            exp.completed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Process already terminated'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'No PID recorded'}), 400

@app.route('/api/experiments/<int:exp_id>/status', methods=['GET'])
@login_required
def check_experiment_status(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    # Check if process is still running
    if exp.status == 'running' and exp.pid:
        try:
            process = psutil.Process(exp.pid)
            if process.status() == psutil.STATUS_ZOMBIE:
                raise psutil.NoSuchProcess(exp.pid)
        except psutil.NoSuchProcess:
            # Process completed, check exit status
            exp.status = 'completed'
            exp.completed_at = datetime.utcnow()
            db.session.commit()
    
    return jsonify({
        'status': exp.status,
        'pid': exp.pid,
        'started_at': exp.started_at.isoformat() if exp.started_at else None,
        'completed_at': exp.completed_at.isoformat() if exp.completed_at else None
    })

@app.route('/api/experiments/<int:exp_id>/log', methods=['GET'])
@login_required
def get_experiment_log(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    if not exp.log_file or not os.path.exists(exp.log_file):
        return jsonify({'log': 'No log file available'})
    
    # Get last N lines
    lines = int(request.args.get('lines', 100))
    
    try:
        with open(exp.log_file, 'r') as f:
            all_lines = f.readlines()
            log_content = ''.join(all_lines[-lines:])
        return jsonify({'log': log_content})
    except Exception as e:
        return jsonify({'log': f'Error reading log: {str(e)}'})

@app.route('/api/experiments/<int:exp_id>/outputs', methods=['GET'])
@login_required
def get_experiment_outputs(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    if not exp.output_path or not os.path.exists(exp.output_path):
        return jsonify({'files': []})
    
    files = []
    for root, dirs, filenames in os.walk(exp.output_path):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, exp.output_path)
            files.append({
                'name': relpath,
                'size': os.path.getsize(filepath),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            })
    
    return jsonify({'files': files})

@app.route('/api/experiments/<int:exp_id>/download/<path:filename>', methods=['GET'])
@login_required
def download_file(exp_id, filename):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    if not exp.output_path:
        return jsonify({'error': 'No output path'}), 404
    
    filepath = os.path.join(exp.output_path, filename)
    
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True)

@app.route('/api/experiments/<int:exp_id>', methods=['DELETE'])
@login_required
def delete_experiment(exp_id):
    exp = Experiment.query.filter_by(id=exp_id, user_id=session['user_id']).first_or_404()
    
    if exp.status == 'running':
        return jsonify({'success': False, 'message': 'Cannot delete running experiment'}), 400
    
    db.session.delete(exp)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/gpu/info', methods=['GET'])
@login_required
def get_gpu_info():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        gpu_info = [{
            'id': gpu.id,
            'name': gpu.name,
            'memory_free': gpu.memoryFree,
            'memory_used': gpu.memoryUsed,
            'memory_total': gpu.memoryTotal,
            'load': gpu.load * 100
        } for gpu in gpus]
        return jsonify({'gpus': gpu_info})
    except:
        # Fallback if GPUtil not available
        return jsonify({'gpus': [{'id': i, 'name': f'GPU {i}', 'memory_free': 0, 'memory_used': 0, 'memory_total': 0, 'load': 0} for i in range(4)]})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
