from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import psycopg2
import psycopg2.errors
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'StockSense'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'root'),
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432')
    )

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/main')
def main():
    return render_template("main.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM Users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()
        if user and password == user[0]:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Users WHERE username = %s OR email = %s", (username, email))
        existing = cur.fetchone()
        if existing:
            message = "Username or email already exists."
        else:
            cur.execute("""
                INSERT INTO Users (user_ID, username, email, password_hash)
                VALUES ((SELECT COALESCE(MAX(user_ID), 0) + 1 FROM Users), %s, %s, %s)
            """, (username, email, password))
            conn.commit()
            return redirect(url_for('login'))
        conn.close()
    return render_template('signup.html', message=message)

@app.route('/index')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT stock_name FROM Stock ORDER BY stock_name;")
    stocks = cur.fetchall()

    user_watchlists = []
    user_id = None
    if 'username' in session:
        cur.execute("SELECT user_ID FROM Users WHERE username = %s", (session['username'],))
        user_id = cur.fetchone()[0]
        cur.execute("SELECT watchlist_id, name FROM Watchlists WHERE user_ID = %s", (user_id,))
        user_watchlists = cur.fetchall()

    stock_name = request.args.get('stock_name')
    stock_data = {}
    if stock_name:
        df = pd.read_sql_query("""
            SELECT p.date, p.open, p.high, p.low, p.close, p.volume
            FROM Price p
            WHERE p.stock_name = %s
            ORDER BY p.date ASC
        """, conn, params=(stock_name,))
        if not df.empty:
            avg_close = round(df['close'].mean(), 2)
            high_max = df['high'].max()
            low_min = df['low'].min()
            total_volume = df['volume'].sum()
            df['date'] = df['date'].apply(lambda x: x.isoformat() if isinstance(x, datetime) else str(x))
            candlestick_data = [
                {
                    'x': row['date'],
                    'o': float(row['open']),
                    'h': float(row['high']),
                    'l': float(row['low']),
                    'c': float(row['close'])
                } for _, row in df.iterrows()
                if pd.notnull(row['open']) and pd.notnull(row['high']) and pd.notnull(row['low']) and pd.notnull(row['close'])
            ]
            stock_data = {
                'stock_name': stock_name,
                'avg_close': avg_close,
                'high_max': high_max,
                'low_min': low_min,
                'total_volume': total_volume,
                'candlestick_data': candlestick_data
            }

    conn.close()
    return render_template(
        'index.html',
        stocks=stocks,
        user_watchlists=user_watchlists,
        last_updated=datetime.now().strftime("%b %d, %Y"),
        stock_data=stock_data
    )

@app.route('/watchlists/create', methods=['POST'])
def create_watchlist():
    if 'username' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_ID FROM Users WHERE username = %s", (session['username'],))
    user_id = cur.fetchone()[0]
    cur.execute("INSERT INTO Watchlists (user_ID, name) VALUES (%s, %s)", (user_id, name))
    conn.commit()
    flash(f'✅ Watchlist "{name}" created successfully!', 'success')
    conn.close()
    return redirect(url_for('index'))

@app.route('/watchlists/delete/<int:watchlist_id>', methods=['POST'])
def delete_watchlist(watchlist_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM WatchlistStocks WHERE watchlist_id = %s", (watchlist_id,))
    cur.execute("DELETE FROM Watchlists WHERE watchlist_id = %s", (watchlist_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_all_watchlists'))

@app.route('/watchlists/add_stock', methods=['POST'])
def add_stock_to_watchlist():
    if 'username' not in session:
        return redirect(url_for('login'))
    watchlist_id = request.form['watchlist_id']
    stock_name = request.form['stock_name']
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO WatchlistStocks (watchlist_id, stock_name) VALUES (%s, %s)", (watchlist_id, stock_name))
        conn.commit()
        flash(f'✅ {stock_name} added to watchlist!', 'success')
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        flash(f'⚠️ {stock_name} is already in this watchlist.', 'danger')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Failed to add {stock_name} to watchlist.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/watchlists')
def view_all_watchlists():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_ID FROM Users WHERE username = %s", (session['username'],))
    user_id = cur.fetchone()[0]
    cur.execute("SELECT watchlist_id, name FROM Watchlists WHERE user_ID = %s", (user_id,))
    watchlists = cur.fetchall()
    conn.close()
    return render_template('watchlists.html', watchlists=watchlists)

@app.route('/watchlists/<int:watchlist_id>')
def view_watchlist_stocks(watchlist_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.stock_name 
        FROM WatchlistStocks w 
        JOIN Stock s ON w.stock_name = s.stock_name
        WHERE w.watchlist_id = %s
    """, (watchlist_id,))
    watchlist_stocks = cur.fetchall()
    cur.execute("SELECT stock_name FROM Stock ORDER BY stock_name;")
    all_stocks = cur.fetchall()
    conn.close()
    return render_template('watchlist_stocks.html', 
                           watchlist_id=watchlist_id, 
                           stocks=watchlist_stocks, 
                           all_stocks=all_stocks)

@app.route('/watchlists/<int:watchlist_id>/remove/<stock_name>')
def remove_stock(watchlist_id, stock_name):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM WatchlistStocks WHERE watchlist_id = %s AND stock_name = %s", (watchlist_id, stock_name))
    conn.commit()
    conn.close()
    return redirect(url_for('view_watchlist_stocks', watchlist_id=watchlist_id))

@app.route('/stock/<stock_name>')
def stock_details(stock_name):
    conn = get_db_connection()
    cur = conn.cursor()
    df = pd.read_sql_query("""
        SELECT p.date, p.open, p.high, p.low, p.close, p.volume
        FROM Price p
        WHERE p.stock_name = %s
        ORDER BY p.date ASC
    """, conn, params=(stock_name,))
    user_watchlists = []
    if 'username' in session:
        cur.execute("SELECT user_ID FROM Users WHERE username = %s", (session['username'],))
        user_id = cur.fetchone()[0]
        cur.execute("SELECT watchlist_id, name FROM Watchlists WHERE user_ID = %s", (user_id,))
        user_watchlists = cur.fetchall()
    conn.close()

    if df.empty:
        return f"No data found for {stock_name}"

    avg_close = round(df['close'].mean(), 2)
    high_max = df['high'].max()
    low_min = df['low'].min()
    total_volume = df['volume'].sum()

    df['date'] = df['date'].apply(lambda x: x.isoformat() if isinstance(x, datetime) else str(x))
    candlestick_data = [
        {
            'x': row['date'],
            'o': float(row['open']),
            'h': float(row['high']),
            'l': float(row['low']),
            'c': float(row['close'])
        } for _, row in df.iterrows()
        if pd.notnull(row['open']) and pd.notnull(row['high']) and pd.notnull(row['low']) and pd.notnull(row['close'])
    ]

    return render_template('stock.html', stock_name=stock_name,
                           avg_close=avg_close,
                           high_max=high_max,
                           low_min=low_min,
                           total_volume=total_volume,
                           candlestick_data=candlestick_data,
                           user_watchlists=user_watchlists)

# Deployment entry point for Gunicorn
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
