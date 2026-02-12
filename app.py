from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urlparse

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

{% if error %}
<p style="color:red;">⚠️ {{ error }}</p>
{% endif %}

<h2>🚗 Car Compare</h2>

<form method="post">
  <input name="url"
         placeholder="Paste full AutoTrader link (https://...)"
         style="width:95%;padding:8px">
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

def normalize_autotrader_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def is_autotrader_car_url(url):
    return (
        url.startswith("http")
        and "autotrader.co.uk/car-details/" in url
    )

def scrape_autotrader(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code != 200:
        raise ValueError("Failed to fetch AutoTrader page")

    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    vehicle_data = None

    for script in scripts:
        try:
            data = json.loads(script.string)

            # Sometimes it's a list of objects
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Vehicle":
                        vehicle_data = item
                        break
            else:
                if data.get("@type") == "Vehicle":
                    vehicle_data = data

        except Exception:
            continue

        if vehicle_data:
            break

    if not vehicle_data:
        raise ValueError("AutoTrader vehicle data not found")

    return {
        "make": vehicle_data.get("brand", {}).get("name", "Unknown"),
        "model": vehicle_data.get("model", "Unknown"),
        "year": int(vehicle_data.get("productionDate", "0")[:4] or 0),
        "price": int(vehicle_data.get("offers", {}).get("price", 0)),
        "mileage": int(
            vehicle_data.get("mileageFromOdometer", {}).get("value", 0)
        ),
        "image": vehicle_data.get("image", [None])[0]
    }


def score_car(car):
    age = datetime.now().year - car["year"]
    score = 10
    score -= age * 0.7
    score -= car["mileage"] / 25000
    return round(max(0, score), 1)

@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        try:
            url = request.form["url"].strip()

            if not is_autotrader_car_url(url):
                raise ValueError(
                    "Please paste a valid AutoTrader car listing link"
                )

            url = normalize_autotrader_url(url)
            car = scrape_autotrader(url)
            car["score"] = score_car(car)

            cars.append(car)

        except Exception as e:
            error = str(e)

    return render_template_string(
        HTML,
        cars=cars,
        error=error
    )

if __name__ == "__main__":
    app.run()
