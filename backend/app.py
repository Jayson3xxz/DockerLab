import os
import time
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

def get_db():
    """Подключение к БД с повторными попытками"""
    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
        try:
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST", "postgres"),
                database=os.environ.get("POSTGRES_DB", "taskdb"),
                user=os.environ.get("POSTGRES_USER", "appuser"),
                password=os.environ.get("POSTGRES_PASSWORD", "changeme"),
                connect_timeout=5
            )
            print(f"✅ Connected to database (attempt {attempt + 1})")
            return conn
        except psycopg2.OperationalError as e:
            attempt += 1
            print(f"❌ Database connection attempt {attempt} failed: {e}")
            if attempt == max_attempts:
                print("❌ All database connection attempts failed")
                raise e
            time.sleep(3)  # Ждем 3 секунды перед следующей попыткой

def init_db():
    """Создание таблицы если её нет"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Создаем таблицу tasks
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized successfully - tasks table is ready")
        
        # Проверим, есть ли тестовые данные
        check_tables()
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def check_tables():
    """Проверка наличия таблиц и данных"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Проверяем, есть ли таблица
        cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tasks'
        )
        """)
        exists = cur.fetchone()[0]
        print(f"📊 Table 'tasks' exists: {exists}")
        
        if exists:
            # Считаем количество записей
            cur.execute("SELECT COUNT(*) FROM tasks")
            count = cur.fetchone()[0]
            print(f"📊 Tasks in database: {count}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error checking tables: {e}")

# Инициализация БД при запуске
print("🚀 Starting application...")
init_db()

@app.route("/api/health", methods=["GET"])
def health():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем подключение к БД
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({
            "status": "ok",
            "database": "connected",
            "service": "running"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }), 500

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Получение всех задач"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(tasks)
    except Exception as e:
        print(f"❌ Error getting tasks: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks", methods=["POST"])
def create_task():
    """Создание новой задачи"""
    try:
        data = request.get_json()
        
        # Валидация
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        if 'title' not in data:
            return jsonify({"error": "Title is required"}), 400
        
        title = data['title'].strip()
        if not title:
            return jsonify({"error": "Title cannot be empty"}), 400
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING *",
            (title,)
        )
        task = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Task created: {task['id']} - {task['title']}")
        return jsonify(task), 201
        
    except psycopg2.Error as e:
        print(f"❌ Database error creating task: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def toggle_task(task_id):
    """Переключение статуса задачи (выполнено/не выполнено)"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "UPDATE tasks SET done = NOT done WHERE id = %s RETURNING *",
            (task_id,)
        )
        task = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if task is None:
            return jsonify({"error": "Task not found"}), 404
        
        print(f"✅ Task {task_id} toggled: done={task['done']}")
        return jsonify(task)
        
    except Exception as e:
        print(f"❌ Error toggling task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Удаление задачи"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        if deleted == 0:
            return jsonify({"error": "Task not found"}), 404
        
        print(f"✅ Task {task_id} deleted")
        return jsonify({
            "deleted": task_id,
            "success": True,
            "message": "Task deleted successfully"
        })
        
    except Exception as e:
        print(f"❌ Error deleting task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug/db", methods=["GET"])
def debug_db():
    """Отладочный endpoint для проверки БД"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Информация о подключении
        cur.execute("SELECT current_database(), current_user, version()")
        db_info = cur.fetchone()
        
        # Список таблиц
        cur.execute("""
            SELECT table_name, table_schema 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        """)
        tables = cur.fetchall()
        
        # Структура таблицы tasks
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "database": {
                "name": db_info[0],
                "user": db_info[1],
                "version": db_info[2].split(',')[0]
            },
            "tables": [{"name": t[0], "schema": t[1]} for t in tables],
            "tasks_schema": [{"column": c[0], "type": c[1], "nullable": c[2]} for c in columns]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # При прямом запуске
    print("🚀 Starting in development mode...")
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)