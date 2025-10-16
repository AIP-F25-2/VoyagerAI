from flask import Flask, render_template, jsonify
import webbrowser
import threading
from skyscanner_scrapper import scrape_skyscanner

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/flights')
def get_flights():
    print("Fetching flights from scraper...")
    flights = scrape_skyscanner("lhr", "jfk", "2025-11-01", max_results=5)
    return jsonify(flights)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    threading.Timer(1.5, open_browser).start()
    app.run(port=5000, debug=True)
