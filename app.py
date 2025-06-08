from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Flask 앱 설정
app = Flask(__name__)
CORS(app)

# 로그 데이터 저장 리스트
logs = []

# Flask 라우트: 로그 및 기타 API
@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs)

@app.route("/api/logs", methods=["POST"])
def add_log():
    log_entry = request.get_json()
    if not log_entry or not isinstance(log_entry, dict):
        return jsonify({'status': 'error', 'message': 'Invalid log entry'}), 400
    logs.append(log_entry)
    return jsonify({'status': 'success'})

@app.route("/api/clear-logs", methods=["POST"])
def clear_logs():
    global logs
    logs = []
    return jsonify({'status': 'success'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)