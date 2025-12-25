from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from google import genai
import json
from flask_cors import CORS
import smtplib
import ssl
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app)

# --- Add Security Headers ---
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# --- Initialize Gemini Client ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None
model = None

if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        model = 'gemini-2.5-flash'
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")

# --- Email Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def send_email_live(to_email, from_email, subject, body):
    """Sends an email using Python's smtplib over a secure SSL connection."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        return {"status": "error", "message": "Email configuration missing in environment variables."}

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return {"status": "success", "message": "Email sent successfully."}

    except smtplib.SMTPAuthenticationError:
        print("Error: Failed to log in. Check SENDER_EMAIL/SENDER_PASSWORD.")
        return {"status": "error", "message": "Authentication failed. Check credentials."}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "error", "message": f"An error occurred while sending: {e}"}


# --- API ROUTES ---

@app.route('/api/analyze', methods=['POST'])
def analyze_email():
    """API endpoint to polish an email using Gemini AI."""
    if client is None:
        return jsonify({"error": "AI service not available. Check API Key."}), 500

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON data in request."}), 400

        draft_subject = data.get('subject', '')
        draft_body = data.get('body', '')
        desired_tone = data.get('toneOption', 'Professional')

        MAX_INPUT_LENGTH = 5000
        if len(draft_subject) + len(draft_body) > MAX_INPUT_LENGTH:
            return jsonify({"error": f"Input too long. Max length is {MAX_INPUT_LENGTH} characters."}), 413

    except Exception:
        return jsonify({"error": "Invalid JSON format or malformed request."}), 400

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

        if polished_json_string.startswith('```') and polished_json_string.endswith('```'):
            start_index = polished_json_string.find('{')
            end_index = polished_json_string.rfind('}') + 1
            if start_index != -1 and end_index != 0:
                polished_json_string = polished_json_string[start_index:end_index]

        polished_json_string = polished_json_string.strip()
        polished_data = json.loads(polished_json_string)

        return jsonify(polished_data), 200

    except json.JSONDecodeError:
        print(f"Error: AI returned invalid JSON. Raw output received:\n{polished_json_string[:500]}")
        return jsonify({"error": "AI response format error."}), 500
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": "Failed to process email with AI."}), 500


@app.route('/api/send', methods=['POST'])
def send_email():
    """API endpoint to send the polished email."""
    try:
        data = request.json
        to_email = data.get('to')
        subject = data.get('subject')
        body = data.get('body')
    except Exception:
        return jsonify({"error": "Invalid JSON format."}), 400

    send_result = send_email_live(to_email, SENDER_EMAIL, subject, body)

    if send_result['status'] == 'success':
        return jsonify({"message": "Email sent successfully"}), 200
    else:
        return jsonify({"error": send_result.get('message', 'Failed to send email.')}), 500


# Health check endpoint for Vercel
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "ai_available": client is not None}), 200


# Vercel serverless handler - DO NOT include app.run()
