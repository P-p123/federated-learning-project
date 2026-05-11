from flask import Flask, jsonify, render_template
import subprocess
import sys
import socket
import json
import os
import glob
import time
from threading import Thread

from centralized_model import run_centralized
from client import USE_DP

app = Flask(__name__)

# ✅ GLOBAL STATE
training_status = {'status': 'idle'}
client_processes = []


# 🏠 HOME ROUTE - Advanced Dashboard
@app.route('/')
def home():
    return render_template('index_advanced.html')


# 📊 BEHAVIOR ANALYSIS PAGE
@app.route('/analysis')
def analysis():
    return render_template('behavior_analysis.html')


# ✅ VERIFICATION PAGE
@app.route('/verify-page')
def verify_page():
    return render_template('verification.html')


# 🚀 START TRAINING (NON-BLOCKING)
@app.route('/start')
def start_training():
    def wait_for_port(host, port, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except OSError:
                time.sleep(0.5)
        return False

    def run_training():
        global training_status

        try:
            training_status['status'] = 'running'
            subprocess.run([sys.executable, 'server.py'])
            training_status['status'] = 'done'

        except Exception as e:
            print('ERROR:', e)
            training_status['status'] = 'error'

    if training_status['status'] == 'running':
        return jsonify({'message': 'Training already running'}), 400

    Thread(target=run_training, daemon=True).start()

    # Launch clients after server starts
    def launch_clients():
        if not wait_for_port('127.0.0.1', 8081, timeout=30):
            print('ERROR: FL server did not start on port 8081')
            return

        global client_processes
        for client_id in range(10):
            process = subprocess.Popen([sys.executable, 'client.py', '--cid', str(client_id)])
            client_processes.append(process)

    Thread(target=launch_clients, daemon=True).start()

    return jsonify({'message': 'Training and clients started 🚀'})


# 📊 CLIENT STATUS
@app.route('/clients')
def get_clients():
    clients = []
    for path in sorted(glob.glob('client_logs/client_*.json')):
        try:
            with open(path, 'r') as f:
                client_history = json.load(f)
        except json.JSONDecodeError:
            client_history = []

        if client_history:
            latest_client = client_history[-1]
            # Extract client_id from filename (client_0.json -> 0)
            client_id = int(path.split('client_')[1].split('.json')[0])
            latest_client['client_id'] = client_id
            latest_client['contribution'] = 1.0  # Each client contributes equally
            clients.append(latest_client)

    return jsonify({'clients': clients})


# 📊 GET RESULTS
@app.route('/results')
def get_results():
    try:
        centralized = run_centralized()

        if os.path.exists('federated_results.json'):
            with open('federated_results.json', 'r') as f:
                federated = json.load(f)
        else:
            federated = {
                'accuracy': 0,
                'precision': 0,
                'recall': 0,
                'f1_score': 0,
                'training_time': 0
            }

        return jsonify({
            'accuracy': federated.get('accuracy', 0),
            'precision': federated.get('precision', 0),
            'recall': federated.get('recall', 0),
            'f1': federated.get('f1_score', 0),
            'time': federated.get('training_time', 0),

            'c_accuracy': centralized.get('accuracy', 0),
            'c_precision': centralized.get('precision', 0),
            'c_recall': centralized.get('recall', 0),
            'c_f1': centralized.get('f1_score', 0),
            'c_time': centralized.get('training_time', 0),

            'status': training_status['status'],
            'privacy': 'ON' if USE_DP else 'OFF'
        })

    except Exception as e:
        return jsonify({'error': str(e)})


# 📋 DETAILED CLIENT BEHAVIOR ANALYSIS
@app.route('/client_details/<int:client_id>')
def get_client_details(client_id):
    """Get full history and behavior details for a specific client"""
    try:
        path = os.path.join('client_logs', f'client_{client_id}.json')
        if not os.path.exists(path):
            return jsonify({'error': 'Client not found'}), 404
        
        with open(path, 'r') as f:
            history = json.load(f)
        
        if not history:
            return jsonify({'error': 'No data for this client'}), 404
        
        # Calculate statistics
        total_rounds = len(history)
        trained_rounds = sum(1 for h in history if h.get('trained', False))
        skipped_rounds = sum(1 for h in history if h.get('skipped', False))
        avg_delay = sum(h.get('delay', 0) for h in history) / total_rounds if total_rounds > 0 else 0
        avg_accuracy = sum(h.get('accuracy', 0) for h in history) / total_rounds if total_rounds > 0 else 0
        
        behavior = history[0].get('behavior', 'unknown')
        hospital_name = history[0].get('hospital_name', f'Client {client_id}')
        
        return jsonify({
            'client_id': client_id,
            'hospital_name': hospital_name,
            'behavior': behavior,
            'history': history,
            'stats': {
                'total_rounds': total_rounds,
                'trained_rounds': trained_rounds,
                'skipped_rounds': skipped_rounds,
                'avg_delay': round(avg_delay, 3),
                'avg_accuracy': round(avg_accuracy, 4),
                'final_accuracy': history[-1].get('accuracy', 0) if history else 0
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 📊 BEHAVIOR SUMMARY ACROSS ALL CLIENTS
@app.route('/behavior_summary')
def get_behavior_summary():
    """Get summary of all client behaviors and performance"""
    try:
        behavior_map = {
            'honest': [],
            'slow': [],
            'sleepy': [],
            'fast': [],
            'unreliable': []
        }
        
        for path in sorted(glob.glob('client_logs/client_*.json')):
            try:
                with open(path, 'r') as f:
                    history = json.load(f)
                if history:
                    client_id = int(path.split('client_')[1].split('.json')[0])
                    behavior = history[0].get('behavior', 'unknown')
                    hospital_name = history[0].get('hospital_name', f'Client {client_id}')
                    final_accuracy = history[-1].get('accuracy', 0)
                    trained = sum(1 for h in history if h.get('trained', False))
                    skipped = sum(1 for h in history if h.get('skipped', False))
                    
                    if behavior in behavior_map:
                        behavior_map[behavior].append({
                            'client_id': client_id,
                            'hospital_name': hospital_name,
                            'final_accuracy': round(final_accuracy, 4),
                            'trained_rounds': trained,
                            'skipped_rounds': skipped,
                            'total_rounds': len(history)
                        })
            except:
                continue
        
        # Calculate behavior statistics
        behavior_stats = {}
        for behavior_type, clients in behavior_map.items():
            if clients:
                avg_accuracy = sum(c['final_accuracy'] for c in clients) / len(clients)
                avg_trained = sum(c['trained_rounds'] for c in clients) / len(clients)
                behavior_stats[behavior_type] = {
                    'count': len(clients),
                    'avg_accuracy': round(avg_accuracy, 4),
                    'avg_trained_rounds': round(avg_trained, 1),
                    'clients': clients
                }
        
        return jsonify(behavior_stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 📈 PER-ROUND BEHAVIOR BREAKDOWN
@app.route('/round_breakdown/<int:round_num>')
def get_round_breakdown(round_num):
    """Get behavior details for a specific round across all clients"""
    try:
        round_data = {
            'round': round_num,
            'clients': [],
            'summary': {
                'total_clients': 0,
                'trained': 0,
                'skipped': 0,
                'avg_accuracy': 0,
                'avg_delay': 0
            }
        }
        
        total_accuracy = 0
        total_delay = 0
        trained_count = 0
        
        for path in sorted(glob.glob('client_logs/client_*.json')):
            try:
                with open(path, 'r') as f:
                    history = json.load(f)
                
                if len(history) >= round_num:
                    client_id = int(path.split('client_')[1].split('.json')[0])
                    round_data_entry = history[round_num - 1]
                    
                    client_info = {
                        'client_id': client_id,
                        'hospital_name': round_data_entry.get('hospital_name', f'Client {client_id}'),
                        'behavior': round_data_entry.get('behavior', 'unknown'),
                        'trained': round_data_entry.get('trained', False),
                        'skipped': round_data_entry.get('skipped', False),
                        'delay': round_data_entry.get('delay', 0),
                        'accuracy': round_data_entry.get('accuracy', 0),
                        'precision': round_data_entry.get('precision', 0),
                        'recall': round_data_entry.get('recall', 0),
                        'f1_score': round_data_entry.get('f1_score', 0)
                    }
                    
                    round_data['clients'].append(client_info)
                    
                    if round_data_entry.get('trained', False):
                        trained_count += 1
                        total_accuracy += client_info['accuracy']
                    
                    total_delay += client_info['delay']
            except:
                continue
        
        round_data['summary']['total_clients'] = len(round_data['clients'])
        round_data['summary']['trained'] = trained_count
        round_data['summary']['skipped'] = len(round_data['clients']) - trained_count
        round_data['summary']['avg_accuracy'] = round(total_accuracy / trained_count, 4) if trained_count > 0 else 0
        round_data['summary']['avg_delay'] = round(total_delay / len(round_data['clients']), 3) if round_data['clients'] else 0
        
        return jsonify(round_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ✅ VERIFICATION ENDPOINT
@app.route('/verify')
def verify_system():
    """Verify that all 10 clients are present and have logged data"""
    try:
        verification = {
            'timestamp': time.time(),
            'status': 'success',
            'total_clients_expected': 10,
            'clients_found': 0,
            'clients': {},
            'all_present': False,
            'total_rounds_completed': 0,
            'federated_accuracy': 0,
            'issues': []
        }
        
        client_data = []
        for path in sorted(glob.glob('client_logs/client_*.json')):
            try:
                client_id = int(path.split('client_')[1].split('.json')[0])
                with open(path, 'r') as f:
                    history = json.load(f)
                
                if history:
                    latest = history[-1]
                    verification['clients'][f'client_{client_id}'] = {
                        'hospital': latest.get('hospital_name', f'Unknown'),
                        'behavior': latest.get('behavior', 'unknown'),
                        'rounds_completed': len(history),
                        'final_accuracy': round(latest.get('accuracy', 0), 4),
                        'trained_rounds': sum(1 for h in history if h.get('trained', False)),
                        'skipped_rounds': sum(1 for h in history if h.get('skipped', False))
                    }
                    verification['clients_found'] += 1
                    client_data.append(len(history))
            except Exception as e:
                verification['issues'].append(f"Error reading client {client_id}: {str(e)}")
        
        if verification['clients_found'] == 10:
            verification['all_present'] = True
        else:
            verification['issues'].append(f"Only {verification['clients_found']}/10 clients found")
        
        if client_data:
            verification['total_rounds_completed'] = max(client_data)
        
        # Get federated accuracy
        if os.path.exists('federated_results.json'):
            with open('federated_results.json', 'r') as f:
                fed_data = json.load(f)
                verification['federated_accuracy'] = fed_data.get('accuracy', 0)
        
        return jsonify(verification)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
