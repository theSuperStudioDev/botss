import aiohttp
from aiohttp import web
from urllib.parse import urlparse
import aiofiles
import json
import os

API_KEY = os.getenv("PROXY_API_KEY", "YourSecureApiKey")
LOG_FILE = "webhook_logs.json"  # Using JSON for structured logging

# Ensure the log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as file:
        json.dump([], file)

def is_valid_webhook_url(url):
    """Validate Discord webhook URL."""
    parsed_url = urlparse(url)
    return (parsed_url.scheme == "https" and
            parsed_url.netloc == "discord.com" and
            "/api/webhooks/" in parsed_url.path)

async def log_request(ip, data, webhook_url):
    """Log request details."""
    entry = {"ip": ip, "data": data, "webhook_url": webhook_url}
    async with aiofiles.open(LOG_FILE, mode="r+") as log_file:
        logs = json.loads(await log_file.read())
        logs.append(entry)
        await log_file.seek(0)
        await log_file.write(json.dumps(logs, indent=2))

async def handle_proxy(request):
    """Handle proxy requests."""
    api_key = request.headers.get("Authorization")
    if api_key != API_KEY:
        return web.Response(status=403, text="Forbidden: Invalid API key.")
    
    webhook_url = request.query.get('webhook_url')
    if not webhook_url or not is_valid_webhook_url(webhook_url):
        return web.Response(status=400, text="Invalid or missing webhook URL.")
    
    try:
        data = await request.json()
        await log_request(request.remote, data, webhook_url)
        headers = {'Content-Type': 'application/json'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data, headers=headers) as response:
                response_body = await response.text()
                return web.Response(text=response_body, status=response.status)
    except Exception as e:
        return web.Response(status=500, text=f"Error: {str(e)}")

async def handle_dashboard(request):
    """Serve a simple traffic dashboard."""
    async with aiofiles.open(LOG_FILE, mode="r") as log_file:
        logs = json.loads(await log_file.read())
        html_logs = "<table border='1'><tr><th>IP</th><th>Webhook URL</th><th>Data</th></tr>"
        for log in logs:
            html_logs += f"<tr><td>{log['ip']}</td><td>{log['webhook_url']}</td><td>{json.dumps(log['data'])}</td></tr>"
        html_logs += "</table>"
        return web.Response(text=f"<h1>Webhook Proxy Traffic</h1>{html_logs}", content_type="text/html")

app = web.Application()
app.router.add_post('/proxystuff', handle_proxy)
app.router.add_get('/', handle_dashboard)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)
