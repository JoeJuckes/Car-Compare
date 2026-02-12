from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

app = Flask(__name__)
cars = []

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-GB,en;q=0.9"
}

HTML = """
<!doctype html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Car Compare</title>

<h2>🚗 Car Compare</h2>
<form method="post">
  <input name="url" placeholder="Paste AutoTrader link" style="width:95%;padding:8px">
  <button style="padding:8px;margin-top:8px">Add Car</button>
</form>

{% for car in cars %}
<hr>
<img src="{{ car.image }}" width="100%">
<b>{{ car.make }} {{ car.model }}</b><br>
Year: {{ car.year }}<br>
Mileage: {{ car.mileage }}<br>
Price: £{{ car.price }}<br>
⭐ Score: {{ car.score }}/10
{% endfor %}
"""

def scrape_autotrader(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    script = soup.find("script", type="application/ld+json")
    data = json.loads(script.string)

    return {
        "make": data["brand"]["name"],
        "model": data["model"],
        "year": int(data["productionDate"][:4]),
        "price": int(data["offers"]["price"]),
        "mileage": int(data["mileageFromOdometer"]["value"]),
        "image": data["image"][0]
    }

def score_car(car):
    age = datetime.now().year - car["year"]
    score = 10
    score -= age * 0.7
    score -= car["mileage"] / 25000
    return round(max(0, score), 1)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        car = scrape_autotrader(request.form["url"])
        car["score"] = score_car(car)
        cars.append(car)
    return render_template_string(HTML, cars=cars)

if __name__ == "__main__":
    app.run()
