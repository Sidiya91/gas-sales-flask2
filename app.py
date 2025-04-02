from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import csv
import os
import uuid
from collections import defaultdict

app = Flask(__name__)

DATA_FILE = 'transactions.csv'

PRICES = {
    0: {'large': 3330, 'medium': 1600, 'small': 730},
    1: {'large': 3130, 'medium': 1505, 'small': 685},
    2: {'large': 3200, 'medium': 1535, 'small': 700}
}

WEIGHTS = {'large': 12, 'medium': 6, 'small': 2.7}

def archive_if_new_day():
    today = datetime.now().strftime('%Y-%m-%d')
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if rows:
                first_date = rows[0]['datetime'].split(' ')[0]
                if first_date != today:
                    archive_name = f"transactions_{first_date}.csv"
                    os.rename(DATA_FILE, archive_name)
                    with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
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

        total_gas_kg = (
            large_qty * WEIGHTS['large'] +
            medium_qty * WEIGHTS['medium'] +
            small_qty * WEIGHTS['small']
        )
        total_gas = total_gas_kg / 1000

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

        archive_if_new_day()
        save_transaction(transaction)
        message = f"✅ تمت العملية بنجاح! المبلغ المطلوب: {total_price} MRU"

    return render_template("index.html", message=message)

@app.route("/daily-summary")
def daily_summary():
    transactions = read_transactions_for_today()
    total_money = sum(t["total_price"] for t in transactions)
    total_gas = sum(t["total_gas"] for t in transactions)
    return render_template("daily_summary.html", transactions=transactions, total_money=total_money, total_gas=total_gas)

@app.route("/delete/<id>", methods=["GET", "POST"])
def delete_transaction(id):
    if request.method == "POST":
        delete_transaction_by_id(id)
        return redirect(url_for("daily_summary"))
    return render_template("confirm_delete.html", id=id)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
