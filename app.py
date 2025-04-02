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

        save_transaction(transaction)
        message = f"\u2705 تمت العملية بنجاح! المبلغ المطلوب: {total_price} MRU"

    return render_template("index.html", message=message)

@app.route("/daily-summary")
def daily_summary():
    summaries = defaultdict(lambda: {"total_money": 0, "total_gas": 0, "count": 0})
    with open(DATA_FILE, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            date = row["datetime"].split(" ")[0]
            summaries[date]["total_money"] += float(row["total_price"])
            summaries[date]["total_gas"] += float(row["total_gas"])
            summaries[date]["count"] += 1
    return render_template("daily_summary.html", summaries=summaries)

@app.route("/summary/<date>")
def summary_day(date):
    records = []
    with open(DATA_FILE, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["datetime"].startswith(date):
                records.append(row)
    return render_template("summary_day.html", date=date, records=records)

@app.route("/delete/<id>", methods=["GET", "POST"])
def delete_transaction(id):
    if request.method == "POST":
        rows = []
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["id"] != id:
                    rows.append(row)

        with open(DATA_FILE, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        return redirect(url_for("daily_summary"))

    return render_template("confirm_delete.html", id=id)

@app.route("/delete_day/<date>", methods=["GET", "POST"])
def delete_day(date):
    if request.method == "POST":
        rows = []
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row["datetime"].startswith(date):
                    rows.append(row)

        with open(DATA_FILE, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        return redirect(url_for("daily_summary"))

    return render_template("confirm_delete_day.html", date=date)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
