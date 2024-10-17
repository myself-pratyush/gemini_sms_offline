from flask_ngrok import run_with_ngrok
import google.generativeai as genai
# from google.colab import userdata
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from flask import Flask, request, render_template_string
from pyngrok import ngrok, conf
import os

load_dotenv()
app = Flask(__name__)

# Authenticate Ngrok and Twilio
# conf.get_default().auth_token = userdata.get('auth_token')
# twilio_account_sid = userdata.get('TWILIO_ACCOUNT_SID')
# twilio_auth_token = userdata.get('TWILIO_AUTH_TOKEN')
# genai.configure(api_key=userdata.get('API_KEY'))

conf.get_default().auth_token = os.environ["ngrok_AUTH_TOKEN"]
twilio_account_sid = os.environ["TWILIO_ACCOUNT_SID"]
twilio_auth_token = os.environ["TWILIO_AUTH_TOKEN"]
genai.configure(api_key=os.environ["API_KEY"])

# Initialize the Twilio Client
client = Client(twilio_account_sid, twilio_auth_token)

# Global variables to store the latest message and sender number
last_message = None
last_sender_number = None

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Reply to incoming SMS messages."""
    global last_message, last_sender_number

    user_msg = request.form.get("Body")
    sender_number = request.form.get("From")  # Get the sender's phone number

    # Generate a response using Google Generative AI
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        user_msg + ' Answer in one word.',
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=10,
            temperature=0.0,
        )
    )

    # Store the message and sender's number for display in the homepage
    last_message = response.text
    last_sender_number = sender_number

    # Use Twilio to send the response message back to the sender
    client.messages.create(
        body=last_message,  # The AI-generated reply
        messaging_service_sid='MGf4e3c8c0316fd0450b323f3bfba6d790',  # Replace with your Twilio number
        to=last_sender_number  # Send it back to the original sender
    )

    return "Message sent!"  # Confirmation message for the /sms route


@app.route("/", methods=['GET'])
def homepage():
    """Display the latest message sent and the sender's number."""
    if last_message and last_sender_number:
        return render_template_string("""
            <h1>Latest SMS Response</h1>
            <p><strong>Sender:</strong> {{ sender_number }}</p>
            <p><strong>Message:</strong> {{ message }}</p>
        """, sender_number=last_sender_number, message=last_message)
    else:
        return "<h1>Welcome to the SMS App</h1><p>No messages sent yet.</p>"


# Reserve a subdomain on ngrok
public_url = ngrok.connect(5000)
print(f"Public URL: {public_url}")

if __name__ == "__main__":
    app.run()
