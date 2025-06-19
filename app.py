from flask import Flask, jsonify, render_template, request
from config import db
from basicAnalysis import run_basic_analysis
from overloadAnalysis import run_overload_analysis

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/algorithms/run-basic-analysis', methods=['POST'])
def run_basic_algorithm():
    try:
        data = request.get_json()
        horse_id = data.get("id") if data else None

        print(f"[Basic Analysis] Received horseId: {horse_id}")

        results = run_basic_analysis(horse_id)
        return jsonify({"message": "Training summary analysis executed successfully", "details": results}), 200
    except Exception as e:
        error_message = f"Error running training summary algorithm: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/api/algorithms/run-overload-analysis', methods=['POST'])
def run_overload():
    try:
        data = request.get_json()
        print(f"[Overload] Received data: {data}")
        horse_id = data.get("id") if data else None

        print(f"[Overload] Received horseId: {horse_id}")

        results = run_overload_analysis(horse_id)
        return jsonify({"message": "Overload analysis executed successfully", "details": results}), 200
    except Exception as e:
        error_message = f"Error running overload analysis algorithm: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
