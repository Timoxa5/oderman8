from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)
DATABASE = 'journal.db'

API_KEY = "76f98c866b7943592d34bf6b8bb560e9"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def get_menu():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu")
    menu_items = cursor.fetchall()
    conn.close()
    return menu_items


def add_menu_item(name, ingredients, price):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu (name, ingredients, price) VALUES (?, ?, ?)",
        (name, ingredients, price),
    )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    weather = get_weather("Київ")  # or any other city
    return render_template("index.html", weather=weather)


@app.route("/menu")
def menu():
    pizzas = get_menu()
    sort_order = request.args.get("sort", "asc")

    if sort_order == "asc":
        pizzas = sorted(pizzas, key=lambda x: x[3])
    elif sort_order == "desc":
        pizzas = sorted(pizzas, key=lambda x: x[3], reverse=True)

    return render_template("menu.html", pizzas=pizzas, sort_order=sort_order)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        ingredients = request.form["ingredients"]
        price = float(request.form["price"])
        add_menu_item(name, ingredients, price)
        return redirect(url_for("menu"))

    return render_template("add.html")

@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("menu"))


def edit_menu_item(id, name, ingredients, price):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu SET name = ?, ingredients = ?, price = ? WHERE id = ?",
        (name, ingredients, price, id)
    )
    conn.commit()
    conn.close()


def get_weather(city):
    url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric&lang=ru"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Ошибка запроса: {response.status_code}")
        return None

    data = response.json()

    if data.get("cod") != 200:
        print(f"Ошибка API: {data.get('message')}")
        return None

    print("Полученные данные о погоде:", data)

    weather_data = {
        "city": data.get("name", "Неизвестный город"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "temp": data["main"]["temp"] if "main" in data else "Неизвестно",
        "description": data["weather"][0]["description"] if "weather" in data else "Неизвестно"
    }

    if weather_data["temp"] < 10:
        weather_data["pizza_recommendation"] = "Скоріш за все вам сподобаються піци з гарячими інгредієнтами, як піца з пепероні чи маргарита."
    elif weather_data["temp"] > 30:
        weather_data["pizza_recommendation"] = "Сьогодні жарко, спробуйте легкі піци з овочами або морепродуктами!"
    else:
        weather_data["pizza_recommendation"] = "Якщо погода м'яка, вам може підійти класична піца з сиром і овочами."

    return weather_data


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu WHERE id = ?", (id,))
    item = cursor.fetchone()
    conn.close()

    if request.method == "POST":
        name = request.form["name"]
        ingredients = request.form["ingredients"]
        price = float(request.form["price"])
        edit_menu_item(id, name, ingredients, price)
        return redirect(url_for("menu"))

    return render_template("edit.html", item=item)


if __name__ == "__main__":
    init_db()
    app.run(port=5006, debug=True)
