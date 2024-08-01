from flask import Flask, request, jsonify
import MySQLdb
from config import Config
import os

app = Flask(__name__)

# Database connection
def get_db_connection():
    return MySQLdb.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        passwd=Config.DB_PASSWORD,
        db=Config.DB_NAME,
        charset=Config.DB_CHARSET
    )

# Function to read SQL queries from files
def get_query(filename):
    with open(filename, 'r') as file:
        query = file.read()
    return query.strip()

# Routes

@app.route('/create', methods=['POST'])
def create():
    data = request.json
    name = data['name']
    age = data['age']
    query = get_query(os.path.join('queries', 'create.sql'))
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(query, (name, age))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'User created successfully'}), 201


@app.route('/read', methods=['GET'])
def read():
    filters = request.args.to_dict()

    query = get_query(os.path.join('queries', 'read.sql'))
    parameters = []

    if filters:
        where_clauses = []
        for key, value in filters.items():
            if key.isdigit():
                where_clauses.append(f"{key} = %s")
                parameters.append(value)
            else:
                where_clauses.append(f"{key} LIKE %s")
                parameters.append(f"%{value}%")
        query += " WHERE " + " AND ".join(where_clauses)

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(query, parameters)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    users = [{'id': row[0], 'name': row[1], 'age': row[2]} for row in rows]
    return jsonify({'users': users}), 200


@app.route('/update/<int:id>', methods=['PUT'])
def update(id):
    data = request.json
    name = data.get('name')
    age = data.get('age')
    query = get_query(os.path.join('queries', 'update.sql'))
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(query, (name, age, id))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'User updated successfully'}), 200

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    query = get_query(os.path.join('queries', 'delete.sql'))
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(query, (id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'User deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
