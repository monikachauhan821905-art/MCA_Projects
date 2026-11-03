
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>

// WiFi Credentials
const char* ssid = "DELL";
const char* password = "123456789";

// Flask Server IP
const char* serverURL =
"http://192.168.31.175:5000/api/readings";

// DHT11 Configuration
#define DHTPIN D5
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {

  Serial.begin(115200);
  delay(2000);

  dht.begin();

  Serial.println();
  Serial.println("================================");
  Serial.println(" SMART WEATHER MONITORING SYSTEM");
  Serial.println("================================");

  // Connect WiFi
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi Connected!");

    Serial.print("NodeMCU IP: ");
    Serial.println(WiFi.localIP());
  }
  else {
    Serial.println();
    Serial.println("WiFi Connection Failed!");
  }

  Serial.println("System Ready!");
}

void loop() {

  // Read DHT11 Sensor
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Check Sensor
  if (isnan(temperature) || isnan(humidity)) {

    Serial.println();
    Serial.println("ERROR: DHT11 Reading Failed!");
    Serial.println("Check DATA, VCC and GND wiring.");

    delay(5000);
    return;
  }

  // Display Sensor Values
  Serial.println();
  Serial.println("========== WEATHER DATA ==========");

  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" C");

  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println(" %");

  // Send Data to Flask
  if (WiFi.status() == WL_CONNECTED) {

    WiFiClient client;
    HTTPClient http;

    http.begin(client, serverURL);

    http.addHeader(
      "Content-Type",
      "application/json"
    );

    String jsonData = "{";
    jsonData += "\"temperature\":";
    jsonData += String(temperature, 1);
    jsonData += ",";
    jsonData += "\"humidity\":";
    jsonData += String(humidity, 1);
    jsonData += "}";

    Serial.println("Sending data to Flask...");

    int responseCode = http.POST(jsonData);

    Serial.print("HTTP Response: ");
    Serial.println(responseCode);

    if (responseCode == 200) {

      Serial.println("Data saved successfully!");

      String response = http.getString();
      Serial.println(response);

    }
    else {

      Serial.println("Flask Server Connection Failed!");
      Serial.println(http.errorToString(responseCode));

    }

    http.end();

  }
  else {

    Serial.println("WiFi Disconnected!");
    WiFi.reconnect();

  }

  Serial.println("==================================");

  delay(5000);
}
