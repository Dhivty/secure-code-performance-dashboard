import sqlite3
# workspace.py
from config import DB_PATH
def view_user_history(user_id):
    """View the execution history of a specific user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT f.filename, f.filetype, r.execution_time, r.memory_usage, r.timestamp
            FROM run_logs r
            JOIN files f ON r.file_id = f.file_id
            WHERE r.user_id = ?
            ORDER BY r.timestamp DESC
        ''', (user_id,))

        history = cursor.fetchall()

        if history:
            print("\n--- Execution History ---")
            for row in history:
                print(f"File: {row[0]} ({row[1]}) | Time: {row[2]:.4f}s | Memory: {row[3]:.4f}MB | Run at: {row[4]}")
        else:
            print("No history found for this user.")

    except Exception as e:
        print(f"Error fetching history: {e}")
    finally:
        conn.close()

def view_all_users():
    """Admin function: View all registered users."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT id, username FROM users ORDER BY id')
        users = cursor.fetchall()

        if users:
            print("\n--- Registered Users ---")
            for user in users:
                print(f"ID: {user[0]} | Username: {user[1]}")
        else:
            print("No users registered yet.")

    except Exception as e:
        print(f"Error fetching users: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    while True:
        choice = input("\n1. View My History\n2. View All Users (Admin)\n3. Exit\nChoose an option: ")
        if choice == '1':
            user_id = int(input("Enter your User ID: "))
            view_user_history(user_id)
        elif choice == '2':
            view_all_users()
        elif choice == '3':
            break
        else:
            print("Invalid option. Try again.")


