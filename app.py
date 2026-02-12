from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!doctype html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Car Compare</title>

<h2>🚗 Car Compare</h2>

<input id="url" placeholder="Paste AutoTrader link" style="width:95%;padding:10px;font-size:16px">
<button onclick="addCar()" style="padding:10px;margin-top:10px">Add Car</button>

<p id="error" style="color:red;"></p>
<div id="cars"></div>

<script>
async function addCar() {
  const url = document.getElementById("url").value.trim();
  document.getElementById("error").textContent = "";

  if (!url.includes("autotrader.co.uk/car-details/")) {
    document.getElementById("error").textContent = "Please paste a valid AutoTrader car link.";
    return;
  }

  try {
    // Fetch the page directly in the browser
    const res = await fetch(url);
    const html = await res.text();

    // Extract the __NEXT_DATA__ JSON embedded by AutoTrader
    const start = html.indexOf('__NEXT_DATA__');
    if (start === -1) throw "Vehicle data not found";

    const jsonStart = html.indexOf('{', start);
    const jsonEnd = html.indexOf('</script>', jsonStart);
    const data = JSON.parse(html.slice(jsonStart, jsonEnd));

    const car = data.props.pageProps.listing;

    // Calculate score
    const age = new Date().getFullYear() - car.year;
    const score = Math.max(0, (10 - age * 0.6 - car.mileage / 30000)).toFixed(1);

    // Render car details
    document.getElementById("cars").innerHTML += `
      <hr>
      <img src="${car.media.images[0].url}" width="100%">
      <b>${car.make} ${car.model}</b><br>
      Year: ${car.year}<br>
      Mileage: ${car.mileage.toLocaleString()}<br>
      Price: £${car.price.toLocaleString()}<br>
      ⭐ Score: ${score}/10
    `;

    // Clear input
    document.getElementById("url").value = "";

  } catch(e) {
    console.error(e);
    document.getElementById("error").textContent = 
      "Failed to fetch car data. Open the listing in Safari and try again.";
  }
}
</script>
"""

@app.route("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(debug=True)
