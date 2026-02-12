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

    next_data = soup.find("script", id="__NEXT_DATA__")
    if not next_data:
        raise ValueError("AutoTrader blocked this request")

    data = json.loads(next_data.string)

    try:
        advert = (
            data["props"]["pageProps"]["advert"]
        )

        return {
            "make": advert["vehicle"]["make"],
            "model": advert["vehicle"]["model"],
            "year": advert["vehicle"]["year"],
            "price": advert["pricing"]["price"],
            "mileage": advert["vehicle"]["odometerReading"]["value"],
            "image": advert["media"]["images"][0]["href"]
        }

    except KeyError:
        raise ValueError("Car data structure changed")


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
