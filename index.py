from aiohttp import web, ClientSession
import asyncio
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the web server
app = web.Application()

# Rate limit settings
RATE_LIMIT_WINDOW = 60  # Time window in seconds
MAX_REQUESTS_PER_WINDOW = 10  # Maximum allowed requests per IP per window

# In-memory store to track requests per IP
rate_limit_store = {}

# Endpoint to handle incoming requests
async def handle_request(request):
    try:
        # Get the user's IP address
        user_ip = request.remote
        current_time = time.time()

        # Initialize rate limit data for new IPs
        if user_ip not in rate_limit_store:
            rate_limit_store[user_ip] = {'count': 0, 'start_time': current_time}

        # Get the current rate limit data
        user_data = rate_limit_store[user_ip]

        # Check if the rate limit window has expired
        if current_time - user_data['start_time'] > RATE_LIMIT_WINDOW:
            user_data['count'] = 0  # Reset the counter
            user_data['start_time'] = current_time  # Reset the window start time

        # Increment the request count
        user_data['count'] += 1

        # Check if the user has exceeded the rate limit
        if user_data['count'] > MAX_REQUESTS_PER_WINDOW:
            logging.warning(f"Rate limit exceeded for IP: {user_ip}")
            return web.Response(text="Rate limit exceeded. Please try again later.", status=429)

        # Extract webhook URL from the request path
        webhook_url = request.match_info.get('webhook_url', '')
        webhook_url = f"https://discord.com/{webhook_url}"
        logging.info(f"Received webhook URL: {webhook_url}")

        # Parse the request payload
        try:
            data = await request.json()
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON: {e}")
            return web.Response(text="Invalid JSON", status=400)

        # Basic validation of the payload
        if not isinstance(data, dict) or not data:
            logging.error("Empty or invalid payload received.")
            return web.Response(text="Invalid or empty payload", status=400)

        # Headers can be extended to include custom headers if needed
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Your Proxy Server/1.0'  # Custom User-Agent
        }

        # Log the request for debugging
        logging.info(f"Request payload: {json.dumps(data, indent=2)}")
        logging.info(f"Request headers: {headers}")

        # Payload transformation (example: adding a timestamp or extra field)
        data['processed_at'] = 'Proxy Server'  # Example transformation

        # Function to send the request to Discord with rate limiting
        async def send_to_webhook(url, payload):
            async with ClientSession() as session:
                while True:
                    async with session.post(url, json=payload, headers=headers) as response:
                        response_text = await response.text()
                        if response.status == 204:
                            logging.info(f"Message sent successfully to {url}.")
                            payload.clear()  # Drop the payload after a successful send
                            return web.Response(text=f"Request sent to {url}, status: {response.status}", status=response.status)
                        elif response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 1))
                            logging.warning(f"Rate limited by Discord. Retrying after {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                        else:
                            logging.error(f"Failed to send request: {response.status} - {response_text}")
                            return web.Response(text=f"Error sending request: {response_text}", status=response.status)

        # Support for multiple webhook URLs in the payload
        if isinstance(data.get("webhook_urls"), list):
            tasks = [send_to_webhook(f"https://discord.com/{url}", data) for url in data["webhook_urls"]]
            await asyncio.gather(*tasks)
            return web.Response(text="Requests processed for multiple webhooks.", status=204)
        else:
            return await send_to_webhook(webhook_url, data)

    except Exception as e:
        # Handle and log exceptions
        logging.error(f"Error handling request: {e}")
        return web.Response(text=f"Error handling request: {e}", status=500)

# Add a route for the webhook URL
app.router.add_post('/{webhook_url:.+}', handle_request)

# Run the app
web.run_app(app, host='0.0.0.0', port=7153)
