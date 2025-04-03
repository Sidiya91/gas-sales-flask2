from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3
import uuid
import os

app = Flask(__name__)
DB_FILE = "database.db"

# أسعار القناني حسب نوع الزبون
PRICES = {
    0: {'large': 3330, 'medium': 1600, 'small': 730},
    1: {'large': 3130, 'medium': 1505, 'small': 685},
    2: {'large': 3200, 'medium': 1535, 'small': 700},
}

WEIGHTS = {'large': 12, 'medium': 6, 'small': 2.7}

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            datetime TEXT,
            customer_type INTEGER,
            large_qty INTEGER,
            medium_qty INTEGER,
            small_qty INTEGER,
            total_price REAL,
            total_gas REAL
        )
        """)

# استدعاء قاعدة البيانات
init_db()

def insert_transaction(data):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['id'], data['datetime'], data['customer_type'],
            data['large_qty'], data['medium_qty'], data['small_qty'],
            data['total_price'], data['total_gas']
        ))

def get_transactions_by_date(date):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM transactions WHERE datetime LIKE ?", (f"{date}%",))
        rows = cur.fetchall()
    return rows

def delete_transaction_by_id(transaction_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

def get_summary_by_date(date):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT SUM(total_price), SUM(total_gas) FROM transactions WHERE datetime LIKE ?", (f"{date}%",))
        result = cur.fetchone()
    return result if result else (0, 0)

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        customer_type = int(request.form["customer_type"])
        large_qty = int(request.form["large_qty"])
        medium_qty = int(request.form["medium_qty"])
        small_qty = int(request.form["small_qty"])

        price_table = PRICES[customer_type]
        total_price = large_qty * price_table['large'] + medium_qty * price_table['medium'] + small_qty * price_table['small']
        total_gas = (large_qty * WEIGHTS['large'] + medium_qty * WEIGHTS['medium'] + small_qty * WEIGHTS['small']) / 1000

        transaction = {
            "id": str(uuid.uuid4()),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_type": customer_type,
            "large_qty": large_qty,
            "medium_qty": medium_qty,
            "small_qty": small_qty,
            "total_price": total_price,
            "total_gas": total_gas
        }

        insert_transaction(transaction)
        message = f"✅ تم تسجيل المعاملة بنجاح. المبلغ: {total_price} MRU"

    return render_template("index.html", message=message)

@app.route("/summary/<date>")
def summary(date):
    rows = get_transactions_by_date(date)
    total_price, total_gas = get_summary_by_date(date)
    is_today = (date == datetime.now().strftime("%Y-%m-%d"))
    return render_template("daily_summary.html", rows=rows, date=date, total_price=total_price, total_gas=total_gas, is_today=is_today)

@app.route("/delete/<id>/<date>", methods=["POST"])
def delete_transaction(id, date):
    if date == datetime.now().strftime("%Y-%m-%d"):
        delete_transaction_by_id(id)
    return redirect(url_for('summary', date=date))

@app.route("/today")
def today():
    return redirect(url_for("summary", date=datetime.now().strftime("%Y-%m-%d")))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
