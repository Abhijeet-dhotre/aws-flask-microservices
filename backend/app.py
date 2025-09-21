from flask import Flask, jsonify, request
import pymysql
import os

app = Flask(__name__)
# Trigger CI/CD workflow
# --- Database Configuration ---
RDS_CONFIG = {
    'host': os.environ.get('RDS_HOST', 'database-1.ctuycmgmwnw4.ap-south-1.rds.amazonaws.com'),
    'user': os.environ.get('RDS_USER', 'admin'),
    'password': os.environ.get('RDS_PASSWORD', 'abhijeet23'),
    'database': os.environ.get('RDS_DB', 'abhijeetdb'),
    'cursorclass': pymysql.cursors.DictCursor # Returns rows as dictionaries
}

def get_connection():
    try:
        return pymysql.connect(**RDS_CONFIG)
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        return None

# --- API Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

@app.route('/table/status', methods=['GET'])
def get_table_status():
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'students'")
            exists = cursor.fetchone() is not None
        return jsonify({'exists': exists})
    finally:
        conn.close()

@app.route('/table/create', methods=['POST'])
def create_table():
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE students (
                    id INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    marks INT CHECK (marks >= 0 AND marks <= 100)
                );
            """)
        conn.commit()
        return jsonify({'message': "'students' table created successfully."})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/table/drop', methods=['POST'])
def drop_table():
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE students")
        conn.commit()
        return jsonify({'message': "'students' table dropped successfully."})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/students', methods=['GET'])
def get_students():
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students ORDER BY id")
            students = cursor.fetchall()
        return jsonify(students)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/students', methods=['POST'])
def add_student():
    data = request.json
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO students (id, name, marks) VALUES (%s, %s, %s)",
                         (data['id'], data['name'], data['marks']))
        conn.commit()
        return jsonify({'message': f"Student {data['name']} added."}), 201
    except pymysql.IntegrityError:
        return jsonify({'error': f"Student with ID {data['id']} already exists."}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/students/sample', methods=['POST'])
def insert_sample_data():
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    sample_data = [
        (101, 'Aditi Sharma', 92), (102, 'Rohan Gupta', 75),
        (103, 'Priya Singh', 88), (104, 'Vikram Reddy', 64)
    ]
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM students WHERE id IN (101, 102, 103, 104)")
            if cursor.fetchone()['count'] > 0:
                return jsonify({'message': 'Sample data already exists.'}), 200

            cursor.executemany("INSERT INTO students (id, name, marks) VALUES (%s, %s, %s)", sample_data)
        conn.commit()
        return jsonify({'message': f"{len(sample_data)} sample records inserted."}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    data = request.json
    conn = get_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            rows_affected = cursor.execute("UPDATE students SET name = %s, marks = %s WHERE id = %s",
                                           (data['name'], data['marks'], student_id))
        conn.commit()
        if rows_affected == 0:
            return jsonify({'error': f"Student with ID {student_id} not found."}), 404
        return jsonify({'message': f"Student with ID {student_id} updated."})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = get_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            rows_affected = cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()
        if rows_affected == 0:
            return jsonify({'error': f"Student with ID {student_id} not found."}), 404
        return jsonify({'message': f"Student with ID {student_id} deleted."})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/stats', methods=['GET'])
def get_stats():
    conn = get_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total, AVG(marks) as avg_marks, MAX(marks) as max_marks FROM students")
            result = cursor.fetchone()
            stats = {
                'total_students': result['total'],
                'avg_marks': round(result['avg_marks'], 1) if result['avg_marks'] else 0,
                'highest_marks': result['max_marks'] or 0
            }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)