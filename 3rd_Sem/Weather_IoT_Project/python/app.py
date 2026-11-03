
from flask import Flask, request, jsonify, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "weather.db"


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- RECEIVE SENSOR DATA ----------------

@app.route("/api/readings", methods=["POST"])
def receive_data():

    data = request.get_json(silent=True)

    if not data or "temperature" not in data or "humidity" not in data:
        return jsonify({
            "status": "error",
            "message": "Temperature or humidity missing"
        }), 400

    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Invalid sensor values"
        }), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        INSERT INTO readings (temperature, humidity, timestamp)
        VALUES (?, ?, ?)
    """, (temperature, humidity, timestamp))

    conn.commit()
    conn.close()

    print("New Reading:", temperature, "°C |", humidity, "%")

    return jsonify({
        "status": "success",
        "message": "Weather data saved successfully"
    }), 200


# ---------------- GET SENSOR DATA ----------------

@app.route("/api/readings", methods=["GET"])
def get_readings():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT * FROM readings
        ORDER BY id DESC
        LIMIT 50
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# ---------------- DASHBOARD ----------------

@app.route("/")
def dashboard():

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Smart Weather Monitoring System</title>

    <meta name="viewport" content="width=device-width, initial-scale=1">

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 25px;
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            color: #1e293b;
        }

        h1 {
            text-align: center;
            margin-bottom: 8px;
        }

        .subtitle {
            text-align: center;
            color: #64748b;
            margin-bottom: 30px;
        }

        .container {
            max-width: 1000px;
            margin: auto;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 3px 12px #00000010;
            text-align: center;
        }

        .card h3 {
            color: #64748b;
        }

        .value {
            font-size: 38px;
            font-weight: bold;
        }

        .charts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 25px;
        }

        .chart-box {
            background: white;
            padding: 20px;
            border-radius: 12px;
            min-width: 0;
        }

        .status {
            text-align: center;
            margin-top: 20px;
            color: #64748b;
        }

        @media (max-width: 650px) {
            .cards, .charts {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <h1>Smart Weather Monitoring System</h1>

    <p class="subtitle">
        Real-Time Temperature and Humidity Monitoring
    </p>

    <div class="cards">

        <div class="card">
            <h3>Temperature</h3>
            <div class="value" id="temperature">-- °C</div>
        </div>

        <div class="card">
            <h3>Humidity</h3>
            <div class="value" id="humidity">-- %</div>
        </div>

    </div>

    <div class="charts">

        <div class="chart-box">
            <h3>Temperature History</h3>
            <canvas id="temperatureChart"></canvas>
        </div>

        <div class="chart-box">
            <h3>Humidity History</h3>
            <canvas id="humidityChart"></canvas>
        </div>

    </div>

    <p class="status" id="status">
        Waiting for sensor data...
    </p>

</div>

<script>

    const tempContext =
        document.getElementById("temperatureChart");

    const humidityContext =
        document.getElementById("humidityChart");

    const temperatureChart = new Chart(tempContext, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Temperature (°C)",
                data: [],
                borderWidth: 2,
                tension: 0.3
            }]
        },
        options: {
            responsive: true
        }
    });

    const humidityChart = new Chart(humidityContext, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Humidity (%)",
                data: [],
                borderWidth: 2,
                tension: 0.3
            }]
        },
        options: {
            responsive: true
        }
    });


    async function updateDashboard() {

        try {

            const response = await fetch("/api/readings");

            if (!response.ok) {
                throw new Error("Server error");
            }

            const readings = await response.json();

            if (readings.length === 0) {
                document.getElementById("status").innerText =
                    "Waiting for sensor data...";
                return;
            }

            const latest = readings[0];

            document.getElementById("temperature").innerText =
                latest.temperature + " °C";

            document.getElementById("humidity").innerText =
                latest.humidity + " %";

            const ordered = readings.slice().reverse();

            const labels = ordered.map(item => item.timestamp);
            const temperatures = ordered.map(item => item.temperature);
            const humidities = ordered.map(item => item.humidity);

            temperatureChart.data.labels = labels;
            temperatureChart.data.datasets[0].data = temperatures;
            temperatureChart.update();

            humidityChart.data.labels = labels;
            humidityChart.data.datasets[0].data = humidities;
            humidityChart.update();

            document.getElementById("status").innerText =
                "Last updated: " + latest.timestamp;

        } catch (error) {

            document.getElementById("status").innerText =
                "Unable to connect to Flask server";

            console.log(error);
        }
    }

    updateDashboard();

    setInterval(updateDashboard, 5000);

</script>

</body>
</html>
""")


# ---------------- START SERVER ----------------

if __name__ == "__main__":

    init_db()

    print("Smart Weather Monitoring System")
    print("Flask Server Started!")
    print("Dashboard: http://127.0.0.1:5000")

    app.run(host="0.0.0.0", port=5000, debug=False)
