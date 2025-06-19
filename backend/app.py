import os
import sqlite3
from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')
CORS(app, supports_credentials=True)

DATABASE = os.path.join(os.path.dirname(__file__), '../database/paper_review.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': '未登录'}), 401
            if role and session.get('role') != role:
                return jsonify({'error': '权限不足'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    if not all([username, email, password, role]):
        return jsonify({'error': '信息不完整'}), 400
    if role not in ['admin', 'reviewer', 'author']:
        return jsonify({'error': '角色无效'}), 400
    db = get_db()
    cur = db.execute('SELECT id FROM users WHERE username=? OR email=?', (username, email))
    if cur.fetchone():
        return jsonify({'error': '用户名或邮箱已存在'}), 400
    hashed = generate_password_hash(password)
    db.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)', (username, email, hashed, role))
    db.commit()
    return jsonify({'message': '注册成功'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username=?', (username,))
    user = cur.fetchone()
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': '用户名或密码错误'}), 401
    session['user_id'] = user['id']
    session['role'] = user['role']
    return jsonify({'message': '登录成功', 'role': user['role']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': '已登出'})

@app.route('/api/current_user', methods=['GET'])
def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'user': None})
    db = get_db()
    cur = db.execute('SELECT id, username, email, role FROM users WHERE id=?', (user_id,))
    user = cur.fetchone()
    if not user:
        return jsonify({'user': None})
    return jsonify({'user': dict(user)})

@app.route('/api/papers', methods=['POST'])
@login_required('author')
def submit_paper():
    data = request.json
    title = data.get('title')
    abstract = data.get('abstract')
    if not title or not abstract:
        return jsonify({'error': '标题和摘要不能为空'}), 400
    db = get_db()
    db.execute('INSERT INTO papers (title, abstract, author_id, status) VALUES (?, ?, ?, ?)',
               (title, abstract, session['user_id'], 'submitted'))
    db.commit()
    return jsonify({'message': '论文提交成功'})

@app.route('/api/papers', methods=['GET'])
@login_required()
def get_papers():
    db = get_db()
    role = session.get('role')
    user_id = session.get('user_id')
    if role == 'author':
        cur = db.execute('SELECT * FROM papers WHERE author_id=?', (user_id,))
        papers = [dict(row) for row in cur.fetchall()]
    elif role == 'reviewer':
        cur = db.execute('''SELECT p.* FROM papers p
                            JOIN assignments a ON p.id = a.paper_id
                            WHERE a.reviewer_id=?''', (user_id,))
        papers = [dict(row) for row in cur.fetchall()]
    elif role == 'admin':
        cur = db.execute('SELECT * FROM papers')
        papers = [dict(row) for row in cur.fetchall()]
    else:
        papers = []
    return jsonify({'papers': papers})

@app.route('/api/papers/assign', methods=['POST'])
@login_required('admin')
def assign_papers():
    db = get_db()
    # 获取所有待分配论文
    papers = db.execute("SELECT id, author_id FROM papers WHERE status='submitted'").fetchall()
    reviewers = db.execute("SELECT id FROM users WHERE role='reviewer'").fetchall()
    if not papers or not reviewers:
        return jsonify({'error': '无可分配论文或评审'}), 400
    # 统计每个评审已分配数量
    reviewer_load = {r['id']: db.execute('SELECT COUNT(*) FROM assignments WHERE reviewer_id=?', (r['id'],)).fetchone()[0] for r in reviewers}
    # 分配，每篇论文3个评审，且每个评审5-10篇
    for paper in papers:
        assigned = db.execute('SELECT reviewer_id FROM assignments WHERE paper_id=?', (paper['id'],)).fetchall()
        assigned_ids = set([a['reviewer_id'] for a in assigned])
        candidates = [r['id'] for r in reviewers if r['id'] != paper['author_id'] and reviewer_load[r['id']] < 10 and r['id'] not in assigned_ids]
        if len(candidates) < 3 - len(assigned_ids):
            continue  # 跳过无法分配的论文
        selected = candidates[:3-len(assigned_ids)]
        for rid in selected:
            db.execute('INSERT INTO assignments (paper_id, reviewer_id, status) VALUES (?, ?, ?)', (paper['id'], rid, 'assigned'))
            reviewer_load[rid] += 1
        # 更新论文状态
        db.execute('UPDATE papers SET status=? WHERE id=?', ('under_review', paper['id']))
    db.commit()
    return jsonify({'message': '分配完成'})

@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        with open(os.path.join(os.path.dirname(__file__), '../database/schema.sql'), 'r', encoding='utf-8') as f:
            conn = sqlite3.connect(DATABASE)
            conn.executescript(f.read())
            conn.commit()
            conn.close()
    app.run(host='0.0.0.0', port=5000, debug=True)
    