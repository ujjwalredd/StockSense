# 📈 StockSense: Your Smart Portfolio Tracker

**StockSense** is a modern portfolio dashboard that allows users to visualize, track, and manage their favorite stocks in an intuitive and stylish interface. Built with Flask and PostgreSQL, the platform combines real-time data analysis with user-friendly design.

**Website Link**: https://stocksense-q0gm.onrender.com
---

## 🌟 Features

- 🔐 Secure user **authentication** (signup, login, logout)
- 📊 Dashboard with **stock statistics and performance charts**
- 📈 Candlestick, line, and area charts using **Chart.js**
- 📋 Create and manage **custom watchlists**
- 🎨 Sleek **dark mode UI** using Bootstrap 5

---

## 🧰 Tech Stack

- **Frontend**: HTML, CSS, Bootstrap 5, Chart.js
- **Backend**: Python (Flask)
- **Database**: PostgreSQL
- **Visualization**: Chart.js + chartjs-chart-financial plugin
- **Dataset**: https://www.kaggle.com/datasets/camnugent/sandp500

---

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- PostgreSQL installed and running

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/stocksense.git
   cd stocksense
2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
3. **Configure the database**
   - Create a PostgreSQL database named `StockSense`
   - Update credentials in `app.py` under `get_db_connection()`
4. **Run the application**
   
   ```bash
   python app.py
5. **Access in browser**
   ```bash
   [python app.py](http://127.0.0.1:5000/)

---

### Folder Structure

```
├── app.py                      # Flask backend
├── templates/
│   ├── index.html              # Dashboard
│   ├── login.html              # Login page
│   ├── signup.html             # Registration page
│   ├── main.html               # Landing page
│   ├── stock.html              # Stock detail page
│   ├── watchlists.html         # List of user watchlists
│   └── watchlist_stocks.html   # Stocks inside a watchlist
```
--- 

### 📸 Screenshots
![Dashboard](landing.png)

--- 

### 👤 Author
- Dhanush Chandra Shekar
- Rujul Jadav Prakash
- Ujjwal Reddy Kalvolu Sreenivasa Reddy


