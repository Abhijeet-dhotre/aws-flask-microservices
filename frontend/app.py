from flask import Flask, render_template_string, request, redirect, url_for
import requests
import os

app = Flask(__name__)

# The backend URL is determined by the Docker service name.
# Fallback for local development without Docker.
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5001')

# The HTML template is now much cleaner. It's just for display.
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>RDS Table Manager</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; margin: 0; color: #333; }
        h1 { text-align: center; color: #005a9c; padding: 20px 0; }
        .container { max-width: 900px; margin: auto; padding: 20px; background: #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 10px; }
        .status-indicator { text-align: center; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; border: 1px solid; }
        .status-exists { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
        .status-not-exists { background-color: #fff3cd; color: #856404; border-color: #ffeeba; }
        .menu { display: flex; justify-content: center; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
        .menu a, .menu .disabled { text-decoration: none; padding: 12px 20px; border-radius: 8px; transition: all 0.3s ease; font-size: 1em; text-align: center; }
        .menu a { background: #007bff; color: white; border: 1px solid #007bff; }
        .menu a:hover { background: #0056b3; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .menu .disabled { background: #e9ecef; color: #6c757d; cursor: not-allowed; border: 1px solid #ced4da; }
        .form-section { border-top: 1px solid #dee2e6; padding-top: 20px; margin-top: 25px; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .form-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; }
        .form-card h3 { text-align: center; color: #007bff; margin-top: 0; }
        form { display: flex; flex-direction: column; gap: 10px; }
        input[type="number"], input[type="text"] { padding: 10px; border: 1px solid #ccc; border-radius: 6px; width: 100%; }
        button { background: #28a745; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; transition: background 0.3s ease; font-size: 1em; }
        button:hover { background: #218838; }
        form[action="/delete"] button { background-color: #dc3545; }
        form[action="/delete"] button:hover { background-color: #c82333; }
        form[action="/update"] button { background-color: #ffc107; color: #212529; }
        form[action="/update"] button:hover { background-color: #e0a800; }
        table { width: 100%; margin-top: 25px; border-collapse: collapse; background: #fff; }
        th, td { padding: 12px; border: 1px solid #dee2e6; text-align: center; }
        th { background-color: #007bff; color: white; }
        .message { margin: 20px 0; text-align: center; font-weight: bold; padding: 15px; border-radius: 8px; border: 1px solid; }
        .message.error { color: #721c24; background-color: #f8d7da; border-color: #f5c6cb; }
        .message.success { color: #155724; background-color: #d4edda; border-color: #c3e6cb; }
        .message.warning { color: #856404; background-color: #fff3cd; border-color: #ffeeba; }
        .stats { display: flex; justify-content: space-around; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .stat-card { background: #e9ecef; padding: 15px; border-radius: 8px; text-align: center; flex-grow: 1; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .stat-label { color: #6c757d; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>RDS Table Manager</h1>
    <div class="container">
        <div class="status-indicator {% if table_exists %}status-exists{% else %}status-not-exists{% endif %}">
            {% if table_exists %}✅ Students table exists.{% else %}⚠️ Students table does not exist. Create it first.{% endif %}
        </div>

        {% if table_exists and stats %}
        <div class="stats">
            <div class="stat-card"><div class="stat-number">{{ stats.total_students }}</div><div class="stat-label">Total Students</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.avg_marks or 0 }}</div><div class="stat-label">Average Marks</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.highest_marks or 0 }}</div><div class="stat-label">Highest Marks</div></div>
        </div>
        {% endif %}

        <div class="menu">
            {% if not table_exists %}
                <a href="/create">🧱 Create Table</a>
                <span class="disabled">📥 Insert Sample</span>
                <span class="disabled">📊 View Students</span>
                <span class="disabled">🗑️ Drop Table</span>
            {% else %}
                <span class="disabled">🧱 Table Exists</span>
                <a href="/insert">📥 Insert Sample</a>
                <a href="/view">📊 View Students</a>
                <a href="/drop">🗑️ Drop Table</a>
            {% endif %}
        </div>

        {% if message %}
            <div class="message {{ message_class }}">{{ message }}</div>
        {% endif %}

        {% if table_exists %}
        <div class="form-section">
            <div class="form-grid">
                <div class="form-card">
                    <h3>➕ Add New Student</h3>
                    <form method="POST" action="/add"><input type="number" name="id" placeholder="ID" required /><input type="text" name="name" placeholder="Name" required /><input type="number" name="marks" placeholder="Marks" required /><button type="submit">Add Student</button></form>
                </div>
                <div class="form-card">
                    <h3>✏️ Update Student</h3>
                    <form method="POST" action="/update"><input type="number" name="id" placeholder="ID to Update" required /><input type="text" name="name" placeholder="New Name" required /><input type="number" name="marks" placeholder="New Marks" required /><button type="submit">Update Student</button></form>
                </div>
                <div class="form-card">
                    <h3>❌ Delete Student</h3>
                    <form method="POST" action="/delete"><input type="number" name="id" placeholder="ID to Delete" required /><button type="submit">Delete Student</button></form>
                </div>
            </div>
        </div>
        {% endif %}
        
        {% if students %}
            <table>
                <tr><th>ID</th><th>Name</th><th>Marks</th><th>Grade</th></tr>
                {% for student in students %}
                <tr>
                    <td>{{ student.id }}</td><td>{{ student.name }}</td><td>{{ student.marks }}</td>
                    <td>{% if student.marks >= 90 %}A+{% elif student.marks >= 80 %}A{% elif student.marks >= 70 %}B{% elif student.marks >= 60 %}C{% else %}F{% endif %}</td>
                </tr>
                {% endfor %}
            </table>
        {% endif %}
    </div>
</body>
</html>
'''

def get_status():
    """Helper function to get table status and stats from backend."""
    try:
        status_res = requests.get(f'{BACKEND_URL}/table/status')
        status_res.raise_for_status()
        table_exists = status_res.json().get('exists', False)
        
        stats = None
        if table_exists:
            stats_res = requests.get(f'{BACKEND_URL}/stats')
            stats_res.raise_for_status()
            stats = stats_res.json()
            
        return table_exists, stats, None
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Cannot connect to backend service: {e}"
        return False, None, error_msg

@app.route('/')
def home():
    table_exists, stats, error = get_status()
    if error:
        return render_template_string(HTML_TEMPLATE, message=error, message_class="error")
    return render_template_string(HTML_TEMPLATE, table_exists=table_exists, stats=stats)

@app.route('/create')
def create_table():
    try:
        res = requests.post(f'{BACKEND_URL}/table/create')
        res.raise_for_status()
        message = res.json().get('message', 'Table created.')
        m_class = "success"
    except requests.exceptions.RequestException as e:
        message = f"Error creating table: {e.response.json().get('error', str(e))}"
        m_class = "error"
    
    table_exists, stats, _ = get_status()
    return render_template_string(HTML_TEMPLATE, table_exists=table_exists, stats=stats, message=message, message_class=m_class)

@app.route('/insert')
def insert_data():
    try:
        res = requests.post(f'{BACKEND_URL}/students/sample')
        res.raise_for_status()
        message = res.json().get('message', 'Sample data inserted.')
        m_class = "success"
    except requests.exceptions.RequestException as e:
        message = f"Error inserting data: {e.response.json().get('error', str(e))}"
        m_class = "error"

    table_exists, stats, _ = get_status()
    return render_template_string(HTML_TEMPLATE, table_exists=table_exists, stats=stats, message=message, message_class=m_class)

@app.route('/view')
def view_data():
    table_exists, stats, error = get_status()
    if error:
        return render_template_string(HTML_TEMPLATE, message=error, message_class="error")
    if not table_exists:
        return redirect(url_for('home'))

    try:
        res = requests.get(f'{BACKEND_URL}/students')
        res.raise_for_status()
        students = res.json()
        if not students:
            return render_template_string(HTML_TEMPLATE, table_exists=True, stats=stats, message="📋 Table is empty.", message_class="warning")
        return render_template_string(HTML_TEMPLATE, table_exists=True, stats=stats, students=students)
    except requests.exceptions.RequestException as e:
        message = f"Error fetching students: {e.response.json().get('error', str(e))}"
        return render_template_string(HTML_TEMPLATE, table_exists=True, stats=stats, message=message, message_class="error")

@app.route('/drop')
def drop_table():
    try:
        res = requests.post(f'{BACKEND_URL}/table/drop')
        res.raise_for_status()
        message = res.json().get('message', 'Table dropped.')
        m_class = "success"
    except requests.exceptions.RequestException as e:
        message = f"Error dropping table: {e.response.json().get('error', str(e))}"
        m_class = "error"

    table_exists, stats, _ = get_status()
    return render_template_string(HTML_TEMPLATE, table_exists=table_exists, stats=stats, message=message, message_class=m_class)

@app.route('/<action>', methods=['POST'])
def handle_form(action):
    try:
        student_id = request.form.get('id')
        name = request.form.get('name')
        marks = request.form.get('marks')
        
        if action == 'add':
            payload = {'id': student_id, 'name': name, 'marks': marks}
            res = requests.post(f'{BACKEND_URL}/students', json=payload)
        elif action == 'update':
            payload = {'name': name, 'marks': marks}
            res = requests.put(f'{BACKEND_URL}/students/{student_id}', json=payload)
        elif action == 'delete':
            res = requests.delete(f'{BACKEND_URL}/students/{student_id}')
        else:
            return "Invalid action", 400
        
        res.raise_for_status()
        message = res.json().get('message', 'Operation successful.')
        m_class = "success"
    except requests.exceptions.RequestException as e:
        message = f"Error: {e.response.json().get('error', str(e))}"
        m_class = "error"
    except Exception as e:
        message = f"An unexpected error occurred: {e}"
        m_class = "error"

    table_exists, stats, _ = get_status()
    return render_template_string(HTML_TEMPLATE, table_exists=table_exists, stats=stats, message=message, message_class=m_class)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)