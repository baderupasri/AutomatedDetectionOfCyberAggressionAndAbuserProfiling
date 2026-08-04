from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_mysqldb import MySQL
from detection_engine import predict_aggression
import os

app = Flask(__name__)
app.secret_key = "secretkey"

socketio = SocketIO(app)

os.makedirs("logs", exist_ok=True)

# ------------------ In-memory tracking ------------------
aggression_count = {}
online_users = set()

# ⭐ NEW: map socket id to username
socket_users = {}

# ------------------ MySQL Config -----------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '#Paste your DB Password'
app.config['MYSQL_DB'] = '#Paste Your Database Name'

mysql = MySQL(app)

# ------------------ START PAGE -------------------------
@app.route('/')
def start():
    return redirect(url_for('login'))

# ------------------ USERS PAGE -------------------------
@app.route('/users')
def users_list():

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("userslist.html")

# ------------------ CHAT PAGE --------------------------
@app.route('/chat/<receiver>')
def chat(receiver):

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("index.html", receiver=receiver)

# ------------------ REGISTER ---------------------------
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO users(username,password) VALUES(%s,%s)",
            (username,password)
        )

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))

    return render_template("register.html")

# ------------------ LOGIN ------------------------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username,password)
        )

        user = cur.fetchone()
        cur.close()

        if user:
            session['user'] = username
            return redirect(url_for('users_list'))
        else:
            return "Invalid Login"

    return render_template("login.html")

# ------------------ LOGOUT -----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------ GET USERS LIST ---------------------
@app.route('/get_users')
def get_users():

    cur = mysql.connection.cursor()
    cur.execute("SELECT username FROM users")

    users = cur.fetchall()
    cur.close()

    current_user = session['user']

    user_list = [u[0] for u in users if u[0] != current_user]

    return jsonify({"users": user_list})

# ---------------- SEND REQUEST ----------------
@app.route('/send_request', methods=['POST'])
def send_request():

    sender = session['user']
    receiver = request.form['receiver']

    cur = mysql.connection.cursor()

    # ⭐ prevent duplicate request
    cur.execute(
        "SELECT * FROM friend_requests WHERE sender=%s AND receiver=%s",
        (sender,receiver)
    )

    existing = cur.fetchone()

    if existing:
        cur.close()
        return jsonify({"status":"already_sent"})

    cur.execute(
        "INSERT INTO friend_requests(sender,receiver,status) VALUES(%s,%s,'pending')",
        (sender,receiver)
    )

    mysql.connection.commit()
    cur.close()

    socketio.emit("new_request",{
        "sender": sender,
        "receiver": receiver
    })

    return jsonify({"status":"request_sent"})

# ------------------ GET PENDING REQUESTS ----------------
@app.route('/get_requests')
def get_requests():

    user = session['user']

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT DISTINCT sender
        FROM friend_requests
        WHERE receiver=%s AND status='pending'
    """,(user,))

    requests = cur.fetchall()

    # get abusers
    cur.execute("SELECT username FROM abusers")
    abusers = [a[0] for a in cur.fetchall()]

    cur.close()

    data = []

    for r in requests:

        sender = r[0]

        data.append({
            "sender": sender,
            "is_abuser": sender in abusers
        })

    return jsonify({"requests":data})

# ---------------- GET SENT REQUESTS ----------------
@app.route('/get_sent_requests')
def get_sent_requests():

    sender = session['user']

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT receiver, MAX(status)
        FROM friend_requests
        WHERE sender=%s
        GROUP BY receiver
    """,(sender,))

    requests = cur.fetchall()
    cur.close()

    data = []

    for r in requests:
        data.append({
            "receiver": r[0],
            "status": r[1]
        })

    return jsonify({"requests":data})

# ---------------- GET FRIENDS ----------------
@app.route('/get_friends')
def get_friends():

    user = session['user']

    cur = mysql.connection.cursor()

    # get accepted friendships
    cur.execute("""
        SELECT sender, receiver
        FROM friend_requests
        WHERE status='accepted'
        AND (sender=%s OR receiver=%s)
    """,(user,user))

    rows = cur.fetchall()

    # get abusers
    cur.execute("SELECT username FROM abusers")
    abusers = [a[0] for a in cur.fetchall()]

    cur.close()

    friends = set()

    for sender,receiver in rows:

        friend = receiver if sender == user else sender

        # ⭐ hide abusers
        if friend not in abusers:
            friends.add(friend)

    return jsonify({"friends":list(friends)})

# ---------------- ACCEPT REQUEST ----------------
@app.route('/accept_request', methods=['POST'])
def accept_request():

    sender = request.form['sender']
    receiver = session['user']

    cur = mysql.connection.cursor()

    cur.execute(
        "UPDATE friend_requests SET status='accepted' WHERE sender=%s AND receiver=%s",
        (sender,receiver)
    )

    mysql.connection.commit()
    cur.close()

    socketio.emit("accepted_redirect",{
        "user": receiver
    })

    return jsonify({"status":"accepted"})

# ---------------- REJECT REQUEST ----------------
@app.route('/reject_request', methods=['POST'])
def reject_request():

    sender = request.form['sender']
    receiver = session['user']

    cur = mysql.connection.cursor()

    cur.execute(
        "UPDATE friend_requests SET status='rejected' WHERE sender=%s AND receiver=%s",
        (sender,receiver)
    )

    mysql.connection.commit()
    cur.close()

    return jsonify({"status":"rejected"})
# ------------------ ADMIN LOGIN ------------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM admins WHERE username=%s AND password=%s",
            (username,password)
        )
        # simple admin credentials
        user = cur.fetchone()
        cur.close()

        if user:
            session['user'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid Login"

    return render_template("admin_login.html")
#------------------- ADMIN LOGOUT -------------------
@app.route('/admin_logout')
def admin_logout():

    session.pop('admin', None)

    return redirect(url_for('admin_login'))
# ------------------ ADMIN DASHBOARD --------------------
@app.route('/admin')
def admin_dashboard():
    if 'user' not in session:
        return redirect(url_for('admin_login'))
    cur = mysql.connection.cursor()

    cur.execute("SELECT username, violations FROM abusers")
    abusers_data = cur.fetchall()

    cur.execute("SELECT username, message FROM blocked_messages")
    blocked_messages_data = cur.fetchall()

    cur.close()

    aggressive_users_db = {user: violations for user, violations in abusers_data}

    blocked_messages_db = [
        {"user": user, "message": msg}
        for user, msg in blocked_messages_data
    ]

    return render_template(
        "admin.html",
        aggressive_users=aggressive_users_db,
        blocked_messages=blocked_messages_db
    )

# ------------------ PRIVATE CHAT ROOM ------------------
@socketio.on('join_private')
def join_private(data):

    user1 = session['user']
    user2 = data['receiver']

    room = "_".join(sorted([user1,user2]))

    join_room(room)

# ------------------ PRIVATE MESSAGE SOCKET --------------------
@socketio.on('private_message')
def private_message(data):

    sender = socket_users.get(request.sid)
    receiver = data['receiver']
    message = data['message']
    # ⭐ check if receiver is online
    if receiver not in online_users:

        emit('receiver_offline',{
            "msg": f"{receiver} is currently offline."
        })

        return
    room = "_".join(sorted([sender, receiver]))

    # -------- aggression detection --------
    result = predict_aggression(message)

    if result["blocked"]:

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO blocked_messages(username,message) VALUES(%s,%s)",
            (sender, message)
        )

        mysql.connection.commit()
        cur.close()

        aggression_count[sender] = aggression_count.get(sender, 0) + 1
        count = aggression_count[sender]

        if count > 3:

            cur = mysql.connection.cursor()

            cur.execute(
                "SELECT * FROM abusers WHERE username=%s",
                (sender,)
            )

            exists = cur.fetchone()

            if not exists:

                cur.execute(
                    "INSERT INTO abusers(username,violations) VALUES(%s,%s)",
                    (sender, count)
                )

            else:

                cur.execute(
                    "UPDATE abusers SET violations=%s WHERE username=%s",
                    (count, sender)
                )

            mysql.connection.commit()
            cur.close()

        # send warning to sender
        emit('sender_warning',{
            "msg": f"⚠ Warning {count}/3: Aggressive message detected."
        })

        # notify receiver
        emit('receiver_alert',{
            "msg":"🚨 Aggressive message detected and blocked."
        }, room=room)

        # show blocked message info
        emit('receive_message',{
            "user":"system",
            "message":"⚠ Message blocked due to policy",
            "type":"blocked"
        }, room=room)

    else:

        # -------- NORMAL PRIVATE MESSAGE --------
        emit('receive_message',{
            "user": sender,
            "message": message,
            "type": "normal"
        }, room=room)

# ------------------ ONLINE USERS -----------------------
@socketio.on('connect')
def connect():

    if 'user' in session:

        username = session['user']
        socket_users[request.sid] = username
        online_users.add(username)

        emit('update_users', list(online_users), broadcast=True)

@socketio.on('disconnect')
def disconnect():

    sid = request.sid

    if sid in socket_users:

        username = socket_users[sid]
        online_users.discard(username)

        del socket_users[sid]

        emit('update_users', list(online_users), broadcast=True)
# ------------------ RUN APP ----------------------------
if __name__ == "__main__":
    socketio.run(app, debug=True)