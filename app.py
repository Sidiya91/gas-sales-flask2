from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import csv
import os
import uuid

app = Flask(__name__)

DATA_FILE = 'transactions.csv'

PRICES = {
    0: {'large': 333, 'medium': 160, 'small': 73},
    1: {'large': 313, 'medium': 150.5, 'small': 68.5},
    2: {'large': 320, 'medium': 153.5, 'small': 70}
}

WEIGHTS = {'large': 12, 'medium': 6, 'small': 2.7}

# Create CSV file with headers if not exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'datetime', 'customer_type', 'large_qty', 'medium_qty', 'small_qty', 'total_price', 'total_gas'])

def save_transaction(transaction):
    with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            transaction['id'],
            transaction['datetime'],
            transaction['customer_type'],
            transaction['large_qty'],
            transaction['medium_qty'],
            transaction['small_qty'],
            transaction['total_price'],
            transaction['total_gas']
        ])

def read_transactions_for_today():
    today = datetime.now().strftime('%Y-%m-%d')
    transactions = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if today in row['datetime']:
                    transactions.append({
                        "id": row['id'],
                        "datetime": row['datetime'],
                        "customer_type": int(row['customer_type']),
                        "large_qty": int(row['large_qty']),
                        "medium_qty": int(row['medium_qty']),
                        "small_qty": int(row['small_qty']),
                        "total_price": float(row['total_price']),
                        "total_gas": float(row['total_gas'])
                    })
    return transactions

def delete_transaction_by_id(transaction_id):
    rows = []
    with open(DATA_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['id'] != transaction_id:
                rows.append(row)
    with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['id', 'datetime', 'customer_type', 'large_qty', 'medium_qty', 'small_qty', 'total_price', 'total_gas'])
        writer.writeheader()
        writer.writerows(rows)

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        customer_type = int(request.form["customer_type"])
        large_qty = int(request.form["large_qty"])
        medium_qty = int(request.form["medium_qty"])
        small_qty = int(request.form["small_qty"])

        price_table = PRICES[customer_type]

        total_price = (
            large_qty * price_table['large'] +
            medium_qty * price_table['medium'] +
            small_qty * price_table['small']
        )

        total_gas = (
            large_qty * WEIGHTS['large'] +
            medium_qty * WEIGHTS['medium'] +
            small_qty * WEIGHTS['small']
        )

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

        save_transaction(transaction)
        message = f"✅ تمت العملية بنجاح! المبلغ المطلوب: {total_price} MRU"

    return render_template("index.html", message=message)

@app.route("/daily-summary")
def daily_summary():
    today_transactions = read_transactions_for_today()
    total_money = sum(t["total_price"] for t in today_transactions)
    total_gas = sum(t["total_gas"] for t in today_transactions)
    return render_template("daily_summary.html", total_money=total_money, total_gas=total_gas, transactions=today_transactions)

@app.route("/delete/<transaction_id>")
def delete_transaction(transaction_id):
    delete_transaction_by_id(transaction_id)
    return redirect(url_for('daily_summary'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
