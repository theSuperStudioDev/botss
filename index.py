from flask import Flask, request, jsonify
import requests
import json
import datetime
from flask_cors import CORS
import aiofiles

app = Flask(__name__)
CORS(app)  # Enable CORS if required
LOG_FILE = "webhook_logs.json"  # Path to your log file

@app.route("/proxystuff", methods=["POST"])
async def proxy_webhook():
    try:
        data = request.json
        webhook_url = data.pop("webhook_url", None)
        if not webhook_url:
            return jsonify({"error": "webhook_url is required"}), 400

        # Forward the request to the actual webhook
        response = requests.post(webhook_url, json=data)
        log_entry = {
            "ip": request.remote_addr,
            "webhook_url": webhook_url,
            "data": data,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        # Log the request
        await log_request(log_entry)
        
        return jsonify({"status": response.status_code, "response": response.json()}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

async def log_request(entry):
    async with aiofiles.open(LOG_FILE, mode="r+") as log_file:
        try:
            logs = json.loads(await log_file.read())
        except json.JSONDecodeError:
            logs = []
        logs.append(entry)
        await log_file.seek(0)
        await log_file.write(json.dumps(logs, indent=2))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
