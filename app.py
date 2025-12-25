from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
from google import genai
import json # Import the json library for parsing
# NEW: Import CORS for handling Cross-Origin Resource Sharing
from flask_cors import CORS
#Adding new Resources to make it Run
import smtplib
import ssl
from email.mime.text import MIMEText # Used to format the email content

# Load environment variables from .env file (to get your GEMINI_API_KEY)
load_dotenv()

# --- Initialize Flask App and Paths ---
# Serve frontend files from the '../frontend' directory relative to the backend folder
app = Flask(__name__, static_folder='../frontend', static_url_path='') 

# NEW: Enable CORS for all routes (necessary when serving static files and API from different endpoints/local setup)
CORS(app)

# --- Add Security Headers (Best Practice) ---
@app.after_request
def add_security_headers(response):
    # Prevent content sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking (only allow framing from the same origin)
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Force HTTPS for subsequent requests (HSTS - requires HTTPS in production)
    # response.headers['Strict-TransportSecurity'] = 'max-age=31536000; includeSubDomains'
    return response

# --- Initialize Gemini Client ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # If the key is not found, raise an error to stop the server from starting
    raise ValueError("GEMINI_API_KEY not found. Please create a .env file with GEMINI_API_KEY=\"YOUR_KEY\"")

try:
    # Use the official SDK to initialize the client
    client = genai.Client(api_key=GEMINI_API_KEY)
    # Use a fast, capable model for the task
    model = 'gemini-2.5-flash'
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None
    model = None


# app.py (Insert this block after the Gemini client initialization)

# --- Load Email Sending Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
# Convert port to integer, defaulting to 465 if not set
SMTP_PORT = int(os.getenv("SMTP_PORT", 465)) 
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# app.py (Replace send_email_stub)
def send_email_live(to_email, from_email, subject, body):
    """
    Sends an email using Python's smtplib over a secure SSL connection.
    Uses credentials and settings from the environment variables.
    """
    if not all([SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        return {"status": "error", "message": "Email configuration missing in environment variables."}

    # 1. Create the email message object
    msg = MIMEText(body)
    msg['Subject'] = subject
    # It's best practice to use the actual sender for 'From'
    msg['From'] = SENDER_EMAIL 
    msg['To'] = to_email

    try:
        # 2. Create a secure SSL context
        context = ssl.create_default_context()
        
        # 3. Connect to the server and send the email
        # Use SMTP_SSL for port 465 (secure connection from the start)
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            # Log in to the account
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            
            # Send the email. The 'from_addr' is the logged-in user.
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            
        return {"status": "success", "message": "Email sent successfully."}

    except smtplib.SMTPAuthenticationError:
        print("Error: Failed to log in. Check SENDER_EMAIL/SENDER_PASSWORD (e.g., if using Gmail, check App Password).")
        return {"status": "error", "message": "Authentication failed. Check credentials."}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "error", "message": f"An error occurred while sending: {e}"}


# --- ROUTES ---

@app.route('/')
def index():
    """Route to serve the main index.html file."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Route to serve static files (style.css, script.js, etc.)."""
    return send_from_directory(app.static_folder, filename)


@app.route('/api/analyze', methods=['POST'])
def analyze_email():
    """
    API endpoint to take a draft email and use the Gemini API to polish it 
    and extract metrics (Tone, Readability).
    """
    if client is None:
        return jsonify({"error": "AI service not available. Check API Key."}), 500

    # IMPROVED: Input validation and security checks
    try:
        data = request.json
        if not data:
             return jsonify({"error": "Missing JSON data in request."}), 400
             
        draft_subject = data.get('subject', '')
        draft_body = data.get('body', '')
        desired_tone = data.get('toneOption', 'Professional') 
        
        # Security check: Limit input length to prevent DOS/abuse of the AI model
        MAX_INPUT_LENGTH = 5000 
        if len(draft_subject) + len(draft_body) > MAX_INPUT_LENGTH:
             return jsonify({"error": f"Input too long. Max length is {MAX_INPUT_LENGTH} characters."}), 413 # 413 Payload Too Large

    except Exception:
        # Catch unexpected errors during request parsing
        return jsonify({"error": "Invalid JSON format or malformed request."}), 400

    # The prompt now includes the desired tone/style for the model to follow
    prompt = f"""
    You are an AI Email Enhancer. Your task is to rewrite a draft email to be professional, clear, and well-structured.

    1. **Polish the Subject and Body:** Rewrite the draft subject and body to significantly improve professionalism, clarity, grammar, and tone.
    2. **Apply Style:** The polished email MUST adhere to the **{desired_tone}** tone/style.
    3. **Analyze:** Determine the **Tone** (e.g., Professional, Formal, Friendly, Urgent, Casual) and **Readability** (e.g., High, Medium, Low) of the *polished* version.
    4. **Output Format:** Return a JSON object ONLY with the following keys: "polishedSubject", "polishedBody", "tone", and "readability". Do not include any other text, markdown formatting (like ```json), or explanation outside of the JSON block.

    DRAFT EMAIL:
    Subject: {draft_subject}
    Body:
    {draft_body}

    JSON Output:
    """

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        polished_json_string = response.text
        
        # --- START OF FIX: Robust JSON Extraction ---
        # 1. Clean the string by removing markdown fence (```json) if present
        if polished_json_string.startswith('```') and polished_json_string.endswith('```'):
            # This handles both ```json\n{...}\n``` and ```{...}```
            start_index = polished_json_string.find('{')
            end_index = polished_json_string.rfind('}') + 1
            if start_index != -1 and end_index != 0:
                 polished_json_string = polished_json_string[start_index:end_index]
        # 2. Trim whitespace before final parsing
        polished_json_string = polished_json_string.strip()
        # --- END OF FIX ---

        # Parse the JSON string
        polished_data = json.loads(polished_json_string)

        # Return the AI-generated JSON directly to the frontend
        return jsonify(polished_data), 200

    except json.JSONDecodeError:
        # If parsing fails, print the raw output to help debug the AI's format
        print(f"Error: AI returned invalid JSON. Raw output received:\n{polished_json_string[:500]}")
        return jsonify({"error": "AI response format error."}), 500
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": "Failed to process email with AI."}), 500



@app.route('/api/send', methods=['POST'])
def send_email():
    """
    API endpoint to send the email using the polished data.
    """
    try:
        data = request.json
        # NOTE: The 'from' field from the frontend is ignored for security/deliverability
        # and we use the configured SENDER_EMAIL.
        # from_email = data.get('from') 
        to_email = data.get('to')
        subject = data.get('subject')
        body = data.get('body')
    except Exception:
        return jsonify({"error": "Invalid JSON format."}), 400

    # *** CALL THE NEW LIVE FUNCTION ***
    send_result = send_email_live(to_email, SENDER_EMAIL, subject, body)

    if send_result['status'] == 'success':
        return jsonify({"message": "Email sent successfully"}), 200
    else:
        # Pass the specific error message back to the user
        return jsonify({"error": send_result.get('message', 'Failed to send email.')}), 500


if __name__ == '__main__':
    # SECURITY FIX: Running in debug=True is dangerous in production. Changed to run without debug.
    # The default port 5000 is kept.
    app.run(port=5000)