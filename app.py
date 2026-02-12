from flask import Flask, render_template_string

app = Flask(__name__)

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
// Simple scoring function
function scoreCar(year, mileage) {
    const age = new Date().getFullYear() - year;
    let score = 10 - (age * 0.6) - (mileage / 30000);
    return Math.max(0, Math.round(score * 10) / 10);
}

// Main function to fetch and parse car data
async function addCar() {
    const url = document.getElementById("url").value.trim();
    const errorEl = document.getElementById("error");
    const carsEl = document.getElementById("cars");
    errorEl.textContent = "";

    if (!url.includes("autotrader.co.uk/car-details/")) {
        errorEl.textContent = "Please paste a valid AutoTrader car link";
        return;
    }

    try {
        // Load the page in the browser
        const res = await fetch(url);
        const html = await res.text();

        // Parse HTML as DOM
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        // AutoTrader stores JSON in __NEXT_DATA__
        const nextDataEl = doc.querySelector("#__NEXT_DATA__");
        if (!nextDataEl) {
            errorEl.textContent = "Car data not found. Make sure the page is fully loaded.";
            return;
        }

        const data = JSON.parse(nextDataEl.textContent);

        const car = data.props.pageProps.listing;

        const score = scoreCar(car.year, car.mileage);

        // Display the car
        carsEl.innerHTML += `
            <hr>
            <img src="${car.media.images[0].url}" width="100%">
            <b>${car.make} ${car.model}</b><br>
            Year: ${car.year}<br>
            Mileage: ${car.mileage}<br>
            Price: £${car.price}<br>
            ⭐ Score: ${score}/10
        `;

    } catch (e) {
        errorEl.textContent = "Failed to fetch car data. Open the listing in Safari and try again.";
        console.error(e);
    }
}
</script>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run()
