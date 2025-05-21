from flask import Flask,make_response, jsonify, send_from_directory, request, redirect ,render_template_string
import json
import qrcode
from io import BytesIO
import os
import uuid
import time


app = Flask(__name__, static_folder='static')

EGG_FILE = 'eggs.json'

def load_eggs():
    if os.path.exists(EGG_FILE):
        with open(EGG_FILE) as f:
            return json.load(f)
    return []

def save_eggs(data):
    with open(EGG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_leaderboard(player_id, found_list):
    path = 'players.json'
    try:
        with open(path) as f:
            players = json.load(f)
    except:
        players = {}

    players[player_id] = {
        'found_eggs': found_list,
        'timestamp': time.time()
    }

    with open(path, 'w') as f:
        json.dump(players, f)

@app.route('/api/eggs')
def get_eggs():
    eggs = load_eggs()
    return jsonify(eggs)

@app.route('/found/<egg_id>')
def found_egg_cookie(egg_id):
    player_id = request.cookies.get('player_id') or str(uuid.uuid4())
    found = request.cookies.get('found_eggs', '')

    found_list = found.split(',') if found else []
    if egg_id not in found_list:
        found_list.append(egg_id)

    # Update leaderboard
    update_leaderboard(player_id, found_list)

    # Set cookies
    resp = make_response(redirect('/?found=' + egg_id))
    resp.set_cookie('found_eggs', ','.join(found_list), max_age=60*60*24*365)
    resp.set_cookie('player_id', player_id, max_age=60*60*24*365)
    return resp

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory(app.static_folder, path)

@app.route('/admin.html')
def serve_admin():
    return send_from_directory(app.static_folder, 'admin.html')

@app.route('/admin/add_egg', methods=['POST'])
def add_egg():
    new_egg = request.get_json()
    eggs = load_eggs()

    # ID prüfen (einzigartig)
    if any(e['id'] == new_egg['id'] for e in eggs):
        return jsonify({'error': 'ID bereits vergeben'}), 400

    eggs.append(new_egg)
    save_eggs(eggs)

    # QR-Code erzeugen
    url = f"http://127.0.0.1:5000/found/{new_egg['id']}"
    img = qrcode.make(url)
    qr_path = os.path.join('qrcodes', f"{new_egg['id']}.png")
    os.makedirs('qrcodes', exist_ok=True)
    img.save(qr_path)

    return jsonify({'success': True})

@app.route('/api/top10')
def top10():
    try:
        with open('players.json') as f:
            players = json.load(f)
    except:
        return jsonify([])

    sorted_players = sorted(
        players.items(),
        key=lambda x: (-len(x[1]['found_eggs']), x[1]['timestamp'])
    )

    top = [{
        'rank': i + 1,
        'eggs': len(p['found_eggs']),
        'id': pid[:8]  # nur Kürzel zeigen
    } for i, (pid, p) in enumerate(sorted_players[:10])]

    return jsonify(top)

if __name__ == '__main__':
    app.run(debug=True)
