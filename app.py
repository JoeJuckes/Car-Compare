from flask import Flask, request, jsonify, render_template_string
import requests
import json
from datetime import datetime

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    "Accept-Language": "en-GB,en;q=0.9"
}

HTML = """
<!doctype html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Car Compare</title>

<h2>🚗 Car Compare</h2>

<input id="url" placeholder="Paste AutoTrader link"
       style="width:95%;padding:10px;font-size:16px">
<button onclick="addCar()" style="padding:10px;margin-top:10px">
Add Car
</button>

<p id="error" style="color:red;"></p>

<div id="cars"></div>

<script>
async function addCar() {
  const url = document.getElementById("url").value.trim();
  document.getElementById("error").textContent = "";

  const res = await fetch("/fetch", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ url })
  });

  const data = await res.json();

  if (data.error) {
    document.getElementById("error").textContent = data.error;
    return;
  }

  document.getElementById("cars").innerHTML += `
    <hr>
    <img src="${data.image}" width="100%">
    <b>${data.make} ${data.model}</b><br>
    Year: ${data.year}<br>
    Mileage: ${data.mileage}<br>
    Price: £${data.price}<br>
    ⭐ Score: ${data.score}/10
  `;
}
</script>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/fetch", methods=["POST"])
def fetch():
    url = request.json.get("url", "")

    if "autotrader.co.uk/car-details/" not in url:
        return jsonify(error="Please paste a valid AutoTrader car link")

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return jsonify(error="AutoTrader blocked this request")

        html = r.text

        # Extract Next.js data
        start = html.find("__NEXT_DATA__")
        if start == -1:
            return jsonify(error="Vehicle data not found")

        json_start = html.find("{", start)
        json_end = html.find("</script>", json_start)

        data = json.loads(html[json_start:json_end])

        car = data["props"]["pageProps"]["listing"]

        score = score_car(car)

        return jsonify({
            "make": car["make"],
            "model": car["model"],
            "year": car["year"],
            "mileage": car["mileage"],
            "price": car["price"],
            "image": car["media"]["images"][0]["url"],
            "score": score
        })

    except Exception as e:
        return jsonify(error=str(e))

if __name__ == "__main__":
    app.run()
