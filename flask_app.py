import sqlite3
import os
import time
from flask import Flask, request, redirect, url_for, session, send_from_directory, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'broconnect_super_secret_key_123'

# PythonAnywhere requires absolute paths
DB_PATH = '/home/spibody/broconnect.db'
UPLOAD_FOLDER = '/home/spibody/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# PROFESSIONAL HTML TEMPLATES
# ==========================================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BroConnect</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h1 { color: #1877f2; text-align: center; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 12px; background: #1877f2; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button:hover { background: #166fe5; }
        .error { background: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; }
        .link { text-align: center; margin-top: 15px; color: #1877f2; text-decoration: none; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>BroConnect</h1>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form action="/signup" method="POST" enctype="multipart/form-data">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="text" name="bio" placeholder="Bio (optional)">
            <label style="font-size: 14px; color: #666;">Profile Picture:</label>
            <input type="file" name="profile_pic" accept="image/*">
            <button type="submit">Sign Up</button>
        </form>
        <a href="/login" class="link">Already have an account? Log In</a>
    </div>
</body>
</html>
"""

FEED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BroConnect - Feed</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; margin: 0; padding-bottom: 50px; }
        .navbar { background: #1877f2; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .navbar h2 { margin: 0; }
        .navbar a { color: white; text-decoration: none; font-weight: bold; margin-left: 15px; }
        .container { max-width: 600px; margin: 20px auto; padding: 0 15px; }
        .card { background: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        textarea { width: 100%; border: 1px solid #ddd; border-radius: 6px; padding: 10px; font-size: 16px; resize: vertical; box-sizing: border-box; }
        .post-header { display: flex; align-items: center; margin-bottom: 10px; }
        .avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; background: #e4e6eb; }
        .username { font-weight: bold; color: #050505; text-decoration: none; }
        .time { font-size: 12px; color: #65676b; }
        .post-content { font-size: 15px; line-height: 1.5; margin-bottom: 10px; }
        .post-image { width: 100%; border-radius: 8px; margin-bottom: 10px; }
        .actions { display: flex; border-top: 1px solid #e4e6eb; padding-top: 10px; }
        .action-btn { flex: 1; background: none; border: none; color: #65676b; font-weight: bold; padding: 8px; cursor: pointer; border-radius: 4px; }
        .action-btn:hover { background: #f0f2f5; }
        .comments { margin-top: 10px; background: #f0f2f5; padding: 10px; border-radius: 8px; }
        .comment { margin-bottom: 8px; font-size: 14px; }
        .comment strong { color: #1877f2; text-decoration: none; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="navbar">
        <h2>BroConnect</h2>
        <div>
            <a href="/profile/{{ username }}">Profile</a>
            <a href="/logout">Logout</a>
        </div>
    </div>
    <div class="container">
        <div class="card">
            <form action="/post" method="POST" enctype="multipart/form-data">
                <textarea name="content" placeholder="What's on your mind, {{ username }}?" rows="3" required></textarea>
                <input type="file" name="image" accept="image/*" style="margin-top: 10px;">
                <button type="submit" style="width: 100%; margin-top: 10px;">Post</button>
            </form>
        </div>

        {% for post in posts %}
        <div class="card">
            <div class="post-header">
                <img src="/uploads/{{ post.profile_pic or 'default.png' }}" class="avatar" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2240%22 height=%2240%22><rect fill=%22%231877f2%22 width=%2240%22 height=%2240%22/></svg>'">
                <div>
                    <a href="/profile/{{ post.username }}" class="username">{{ post.username }}</a>
                    <div class="time">{{ post.created_at }}</div>
                </div>
            </div>
            <div class="post-content">{{ post.content }}</div>
            {% if post.image_path %}
                <img src="/uploads/{{ post.image_path }}" class="post-image">
            {% endif %}
            <div style="color: #65676b; font-size: 14px; margin-bottom: 10px;">{{ post.like_count }} Likes</div>
            <div class="actions">
                <form action="/like" method="POST" style="flex: 1; margin: 0;">
                    <input type="hidden" name="post_id" value="{{ post.id }}">
                    <button type="submit" class="action-btn">{{ '❤️ Unlike' if post.user_liked > 0 else '🤍 Like' }}</button>
                </form>
                <button class="action-btn" onclick="document.getElementById('c-{{ post.id }}').classList.toggle('hidden')">💬 Comment</button>
            </div>
            <div id="c-{{ post.id }}" class="comments hidden">
                {% for comment in post.comments %}
                <div class="comment"><a href="/profile/{{ comment.username }}" class="username">{{ comment.username }}</a>: {{ comment.content }}</div>
                {% endfor %}
                <form action="/comment" method="POST" style="display: flex; margin-top: 10px;">
                    <input type="hidden" name="post_id" value="{{ post.id }}">
                    <input type="text" name="comment" placeholder="Write a comment..." required style="flex: 1; padding: 8px; border-radius: 20px; border: 1px solid #ddd;">
                    <button type="submit" style="width: auto; margin: 0 0 0 10px; padding: 8px 15px;">Post</button>
                </form>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

PROFILE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ profile_username }} - BroConnect</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; margin: 0; }
        .navbar { background: #1877f2; color: white; padding: 15px 20px; }
        .navbar a { color: white; text-decoration: none; font-weight: bold; }
        .header { background: white; border-radius: 0 0 8px 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); text-align: center; padding-bottom: 20px; }
        .cover { height: 200px; background: linear-gradient(135deg, #1877f2, #00c6ff); }
        .profile-pic { width: 150px; height: 150px; border-radius: 50%; border: 4px solid white; margin-top: -75px; object-fit: cover; background: #e4e6eb; }
        .info { padding: 10px 20px; }
        .name { font-size: 28px; font-weight: bold; margin: 10px 0 5px; }
        .bio { color: #65676b; margin-bottom: 15px; }
        .stats { color: #65676b; margin-bottom: 15px; }
        .stats span { font-weight: bold; color: #050505; }
        .btn { padding: 10px 20px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; font-size: 15px; margin: 5px; }
        .btn-primary { background: #1877f2; color: white; }
        .btn-secondary { background: #e4e6eb; color: #050505; }
        .container { max-width: 600px; margin: 20px auto; padding: 0 15px; }
        .card { background: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        .post-header { display: flex; align-items: center; margin-bottom: 10px; }
        .avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; }
        .username { font-weight: bold; color: #050505; text-decoration: none; }
        .post-image { width: 100%; border-radius: 8px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="navbar"><a href="/feed">← Back to Feed</a></div>
    <div class="header">
        <div class="cover"></div>
        <img src="/uploads/{{ profile_pic or 'default.png' }}" class="profile-pic" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22150%22 height=%22150%22><rect fill=%22%231877f2%22 width=%22150%22 height=%22150%22/></svg>'">
        <div class="info">
            <div class="name">{{ profile_username }}</div>
            <div class="bio">{{ profile_bio or 'No bio yet.' }}</div>
            <div class="stats"><span>{{ follower_count }}</span> followers · <span>{{ following_count }}</span> following</div>
            
            {% if is_own_profile %}
            <form action="/update-pic" method="POST" enctype="multipart/form-data" style="display: inline;">
                <input type="file" name="profile_pic" accept="image/*" style="display: none;" id="picInput" onchange="this.form.submit()">
                <button type="button" class="btn btn-secondary" onclick="document.getElementById('picInput').click()">📷 Change Picture</button>
            </form>
            {% else %}
            <form action="/follow" method="POST" style="display: inline;">
                <input type="hidden" name="target_username" value="{{ profile_username }}">
                <button type="submit" class="btn {{ 'btn-secondary' if is_following else 'btn-primary' }}">{{ 'Unfollow' if is_following else 'Follow' }}</button>
            </form>
            {% endif %}
        </div>
    </div>

    <div class="container">
        {% for post in posts %}
        <div class="card">
            <div class="post-header">
                <img src="/uploads/{{ post.profile_pic or 'default.png' }}" class="avatar">
                <div>
                    <div class="username">{{ post.username }}</div>
                    <div style="font-size: 12px; color: #65676b;">{{ post.created_at }}</div>
                </div>
            </div>
            <div>{{ post.content }}</div>
            {% if post.image_path %}<img src="/uploads/{{ post.image_path }}" class="post-image">{% endif %}
            <div style="color: #65676b; font-size: 14px; margin-top: 10px;">{{ post.like_count }} Likes</div>
        </div>
        {% endfor %}
        {% if not posts %}<div class="card" style="text-align: center; color: #65676b;">No posts yet.</div>{% endif %}
    </div>
</body>
</html>
"""

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def home():
    if 'username' in session: return redirect(url_for('feed'))
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/login')
def login_page():
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    bio = request.form.get('bio', '')
    
    pic_path = None
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"pic_{int(time.time())}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            pic_path = filename

    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password, bio, profile_pic) VALUES (?, ?, ?, ?)", (username, password, bio, pic_path))
        conn.commit()
        return redirect(url_for('login_page'))
    except sqlite3.IntegrityError:
        return render_template_string(LOGIN_TEMPLATE, error="Username already taken!")
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    if user:
        session['username'] = username
        return redirect(url_for('feed'))
    return render_template_string(LOGIN_TEMPLATE, error="Invalid username or password!")

@app.route('/feed')
def feed():
    if 'username' not in session: return redirect(url_for('home'))
    username = session['username']
    conn = get_db()
    user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()['id']
    
    posts = conn.execute('''
        SELECT posts.*, users.username, users.profile_pic,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id AND likes.user_id = ?) as user_liked
        FROM posts JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    ''', (user_id,)).fetchall()

    for post in posts:
        post['comments'] = conn.execute('''
            SELECT comments.content, users.username FROM comments 
            JOIN users ON comments.user_id = users.id WHERE comments.post_id = ?
        ''', (post['id'],)).fetchall()

    conn.close()
    return render_template_string(FEED_TEMPLATE, username=username, posts=posts)

@app.route('/profile/<username>')
def profile(username):
    if 'username' not in session: return redirect(url_for('home'))
    current_user = session['username']
    conn = get_db()
    current_id = conn.execute("SELECT id FROM users WHERE username = ?", (current_user,)).fetchone()['id']
    profile_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    if not profile_user: return "User not found", 404
    
    p_id = profile_user['id']
    is_own = (current_id == p_id)
    followers = conn.execute("SELECT COUNT(*) FROM follows WHERE following_id = ?", (p_id,)).fetchone()[0]
    following = conn.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ?", (p_id,)).fetchone()[0]
    is_following = conn.execute("SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?", (current_id, p_id)).fetchone() is not None if not is_own else False
    
    posts = conn.execute('''
        SELECT posts.*, users.username, users.profile_pic,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) as like_count
        FROM posts JOIN users ON posts.user_id = users.id WHERE posts.user_id = ?
        ORDER BY posts.created_at DESC
    ''', (p_id,)).fetchall()
    conn.close()
    
    return render_template_string(PROFILE_TEMPLATE, 
        profile_username=username, profile_bio=profile_user['bio'], profile_pic=profile_user['profile_pic'],
        follower_count=followers, following_count=following, is_own_profile=is_own, is_following=is_following, posts=posts)

@app.route('/post', methods=['POST'])
def create_post():
    if 'username' not in session: return redirect(url_for('home'))
    content = request.form['content']
    img_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_path = filename
    conn = get_db()
    user_id = conn.execute("SELECT id FROM users WHERE username = ?", (session['username'],)).fetchone()['id']
    conn.execute("INSERT INTO posts (content, user_id, image_path) VALUES (?, ?, ?)", (content, user_id, img_path))
    conn.commit(); conn.close()
    return redirect(url_for('feed'))

@app.route('/update-pic', methods=['POST'])
def update_pic():
    if 'username' not in session: return redirect(url_for('home'))
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"pic_{int(time.time())}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn = get_db()
            conn.execute("UPDATE users SET profile_pic = ? WHERE username = ?", (filename, session['username']))
            conn.commit(); conn.close()
    return redirect(url_for('profile', username=session['username']))

@app.route('/like', methods=['POST'])
def like_post():
    if 'username' not in session: return redirect(url_for('home'))
    conn = get_db()
    user_id = conn.execute("SELECT id FROM users WHERE username = ?", (session['username'],)).fetchone()['id']
    post_id = request.form['post_id']
    exists = conn.execute("SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id)).fetchone()
    if exists: conn.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    else: conn.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('feed'))

@app.route('/comment', methods=['POST'])
def add_comment():
    if 'username' not in session: return redirect(url_for('home'))
    conn = get_db()
    user_id = conn.execute("SELECT id FROM users WHERE username = ?", (session['username'],)).fetchone()['id']
    conn.execute("INSERT INTO comments (content, user_id, post_id) VALUES (?, ?, ?)", (request.form['comment'], user_id, request.form['post_id']))
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('feed'))

@app.route('/follow', methods=['POST'])
def follow_user():
    if 'username' not in session: return redirect(url_for('home'))
    conn = get_db()
    current_id = conn.execute("SELECT id FROM users WHERE username = ?", (session['username'],)).fetchone()['id']
    target_id = conn.execute("SELECT id FROM users WHERE username = ?", (request.form['target_username'],)).fetchone()['id']
    exists = conn.execute("SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?", (current_id, target_id)).fetchone()
    if exists: conn.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (current_id, target_id))
    else: conn.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (current_id, target_id))
    conn.commit(); conn.close()
    return redirect(request.referrer or url_for('feed'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
