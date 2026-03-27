"""
database/mysql_db.py
Aura — MySQL Database Layer
Handles users, transactions, goals, and notifications.
"""

import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import secrets

load_dotenv()

# ─── CONNECTION ───────────────────────────────────────────────────────────────

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "aura_db")
    )


# ─── SETUP ────────────────────────────────────────────────────────────────────

def setup_database():
    """Create database and all tables if they don't exist."""
    # First connect without database to create it
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "")
    )
    cursor = conn.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS aura_db")
    cursor.execute("USE aura_db")

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            monthly_income DECIMAL(12,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Goals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            savings_goal DECIMAL(12,2) NOT NULL,
            current_savings DECIMAL(12,2) DEFAULT 0,
            goal_deadline DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            category VARCHAR(50) NOT NULL,
            monthly_budget DECIMAL(12,2) NOT NULL,
            UNIQUE KEY unique_user_category (user_id, category),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            category VARCHAR(50) NOT NULL,
            description VARCHAR(200) NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            transaction_date DATE NOT NULL,
            type ENUM('debit', 'credit') DEFAULT 'debit',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Subscriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            billing_cycle VARCHAR(20) DEFAULT 'monthly',
            last_used DATE,
            status ENUM('active', 'flagged', 'cancel') DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type VARCHAR(50) NOT NULL,
            title VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            severity ENUM('info', 'warning', 'danger') DEFAULT 'info',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Agent actions log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_actions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            amount_saved DECIMAL(12,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("[AURA DB] Database and tables created successfully!")


# ─── USER OPERATIONS ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password: str, stored_hash: str) -> bool:
    salt, hashed = stored_hash.split(":")
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed

def create_user(username: str, email: str, password: str, full_name: str,
                monthly_income: float = 0) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, monthly_income)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, password_hash, full_name, monthly_income))
        user_id = cursor.lastrowid

        # Create default goal
        cursor.execute("""
            INSERT INTO goals (user_id, savings_goal, current_savings, goal_deadline)
            VALUES (%s, %s, %s, %s)
        """, (user_id, 300000, 0, "2025-12-31"))

        # Create default budgets
        default_budgets = [
            ("Dining Out", 8000), ("Groceries", 6000), ("Entertainment", 4000),
            ("Transport", 3500), ("Subscriptions", 2000), ("Utilities", 2500),
            ("Shopping", 5000), ("Healthcare", 2000)
        ]
        for cat, budget in default_budgets:
            cursor.execute("""
                INSERT INTO budgets (user_id, category, monthly_budget)
                VALUES (%s, %s, %s)
            """, (user_id, cat, budget))

        conn.commit()
        return {"status": "success", "user_id": user_id, "username": username}
    except Error as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_user_by_id(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email, full_name, CAST(monthly_income AS FLOAT) as monthly_income, created_at FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


# ─── GOAL OPERATIONS ──────────────────────────────────────────────────────────

def get_user_goal(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM goals WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
    goal = cursor.fetchone()
    cursor.close()
    conn.close()
    return goal

def update_user_goal(user_id: int, savings_goal: float = None,
                     current_savings: float = None, deadline: str = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    fields, values = [], []
    if savings_goal is not None:
        fields.append("savings_goal = %s"); values.append(savings_goal)
    if current_savings is not None:
        fields.append("current_savings = %s"); values.append(current_savings)
    if deadline is not None:
        fields.append("goal_deadline = %s"); values.append(deadline)
    if fields:
        values.append(user_id)
        cursor.execute(f"UPDATE goals SET {', '.join(fields)} WHERE user_id = %s", values)
        conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


# ─── TRANSACTION OPERATIONS ───────────────────────────────────────────────────

def add_transaction(user_id: int, category: str, description: str,
                    amount: float, date: str = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    txn_date = date or datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO transactions (user_id, category, description, amount, transaction_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, category, description, amount, txn_date))
    txn_id = cursor.lastrowid
    conn.commit()

    # Check for overspend and generate notification
    _check_overspend_notification(user_id, category, conn)

    cursor.close()
    conn.close()
    return {"status": "success", "transaction_id": txn_id}

def get_transactions(user_id: int, month: str = None) -> list:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if month:
        cursor.execute("""
            SELECT * FROM transactions
            WHERE user_id = %s AND DATE_FORMAT(transaction_date, '%Y-%m') = %s
            ORDER BY transaction_date DESC
        """, (user_id, month))
    else:
        cursor.execute("""
            SELECT * FROM transactions WHERE user_id = %s
            ORDER BY transaction_date DESC LIMIT 50
        """, (user_id,))
    txns = cursor.fetchall()
    cursor.close()
    conn.close()
    return txns

def get_spend_by_category(user_id: int, month: str = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    month = month or datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = %s AND DATE_FORMAT(transaction_date, '%Y-%m') = %s
        GROUP BY category
    """, (user_id, month))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {r["category"]: float(r["total"]) for r in rows}


# ─── BUDGET OPERATIONS ────────────────────────────────────────────────────────

def get_budgets(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT category, monthly_budget FROM budgets WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {r["category"]: float(r["monthly_budget"]) for r in rows}

def update_budget(user_id: int, category: str, new_budget: float) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budgets (user_id, category, monthly_budget)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE monthly_budget = %s
    """, (user_id, category, new_budget, new_budget))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


# ─── NOTIFICATION OPERATIONS ──────────────────────────────────────────────────

def _check_overspend_notification(user_id: int, category: str, conn):
    """Auto-generate notification if category is over budget."""
    cursor = conn.cursor(dictionary=True)
    month = datetime.now().strftime("%Y-%m")

    cursor.execute("""
        SELECT SUM(amount) as total FROM transactions
        WHERE user_id = %s AND category = %s
        AND DATE_FORMAT(transaction_date, '%Y-%m') = %s
    """, (user_id, category, month))
    row = cursor.fetchone()
    total_spent = float(row["total"] or 0)

    cursor.execute("SELECT monthly_budget FROM budgets WHERE user_id = %s AND category = %s",
                   (user_id, category))
    budget_row = cursor.fetchone()
    if not budget_row:
        cursor.close()
        return

    budget = float(budget_row["monthly_budget"])
    pct = (total_spent / budget * 100) if budget > 0 else 0

    if pct >= 100:
        _create_notification(user_id, "overspend",
            f"{category} Budget Exceeded!",
            f"You've spent Rs{total_spent:,.0f} on {category} — Rs{total_spent-budget:,.0f} over your Rs{budget:,.0f} budget.",
            "danger", conn)
    elif pct >= 80:
        _create_notification(user_id, "warning",
            f"{category} Budget at {pct:.0f}%",
            f"You've used Rs{total_spent:,.0f} of your Rs{budget:,.0f} {category} budget. Slow down!",
            "warning", conn)

    cursor.close()

def _create_notification(user_id: int, ntype: str, title: str,
                          message: str, severity: str, conn):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, severity)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, ntype, title, message, severity))
    cursor.close()

def get_notifications(user_id: int, unread_only: bool = False) -> list:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM notifications WHERE user_id = %s"
    params = [user_id]
    if unread_only:
        query += " AND is_read = FALSE"
    query += " ORDER BY created_at DESC LIMIT 20"
    cursor.execute(query, params)
    notifs = cursor.fetchall()
    cursor.close()
    conn.close()
    return notifs

def mark_notifications_read(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


if __name__ == "__main__":
    setup_database()
    print("Test user creation:")
    result = create_user("priya", "priya@test.com", "aura2025", "Priya Sharma", 85000)
    print(result)