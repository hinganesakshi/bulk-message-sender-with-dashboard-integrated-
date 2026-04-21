from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
import mysql.connector

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

# MySQL Database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="yourPassword",  # enter you databse password
            database="whatsapp_bulk_sender"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

# Route for the root URL
@app.route('/')
def index():
    return render_template('index.html')

# API route for getting analytics data
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    status_filter = request.args.get('status', 'all')
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    query = 'SELECT * FROM message_stats'
    if status_filter != 'all':
        query += ' WHERE status = %s'
        cursor.execute(query, (status_filter,))
    else:
        cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    total_sent = len(results)
    successful = sum(1 for r in results if r[5] == 'Sent')
    delivered = sum(1 for r in results if r[5] == 'Delivered')
    read = sum(1 for r in results if r[5] == 'Read')
    failed = total_sent - (successful + delivered + read)
    
    return jsonify({
        'total_sent': total_sent,
        'successful': successful,
        'delivered': delivered,
        'read': read,
        'failed': failed,
        'details': results
    })

# API route for exporting data
@app.route('/api/export', methods=['GET'])
def export_data():
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM message_stats')
        results = cursor.fetchall()
        output = "id,date,contact_name,contact_number,message,status\n"
        for row in results:
            output += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"
        cursor.close()
        return output, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=message_stats.csv'}
    except mysql.connector.Error as e:
        return jsonify({'error': f'Database query error: {e}'}), 500
    finally:
        if conn.is_connected():
            conn.close()

# SocketIO handler for real-time messages
@socketio.on('update')
def handle_update(data):
    print(f"Update received: {data}")
    # Broadcast the update to all connected clients
    socketio.emit('update', data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
