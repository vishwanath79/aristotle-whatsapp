import json
import time
import logging
import datetime
from pathlib import Path
from flask import Flask, request
from openai import OpenAI
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from cred import (
    OPENAI_API_KEY,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    ASSISTANT_API,
    TWILIO_FROM_NUMBER,
    TWILIO_TO_NUMBER,
    TWILIO_TO_NUMBER2,
    TWILIO_TO_NUMBER3
)
from generic_chat import chat_with_gpt
from generic_news import fetch_news

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    filename="logs/openailog.txt",
    filemode="a+",
    format="%(asctime)-15s %(levelname)-8s %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Global variables
conversation_history = []
WHATSAPP_PREFIX = 'whatsapp:+'

# Load instructions
try:
    with open('instructions.txt', 'r') as file:
        instructions = file.read().strip()
except FileNotFoundError:
    logger.error("Instructions file not found")
    instructions = "Default AI assistant instructions"

# Available functions mapping
functions = {
    'get_news': fetch_news,
}

@app.route("/aristotle", methods=["POST"])
def wa_reply():
    """Handle incoming WhatsApp messages and return AI response"""
    try:
        answer = chat_with_bot()
        numbers = [TWILIO_TO_NUMBER, TWILIO_TO_NUMBER2, TWILIO_TO_NUMBER3]
        
        # Send message to all configured numbers
        for number in numbers:
            message = twilio_client.messages.create(
                body=answer,
                from_=f'{WHATSAPP_PREFIX}{TWILIO_FROM_NUMBER}',
                to=f'{WHATSAPP_PREFIX}{number}'
            )
            logger.info(f"Message sent to {number}: {message.sid}")
        
        return str(message.sid)
    except Exception as e:
        logger.error(f"Error in wa_reply: {str(e)}")
        return "Error processing request", 500

def chat_with_bot():
    """Handle incoming messages and return AI response"""
    try:
        # Obtain the request's user message
        question = request.form.get('Body', '').lower()
        print("user query ", question)

        thread = openai_client.beta.threads.create()
        try:
            # Insert user message into the thread
            message = openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=question
            )

            # Run the assistant
            run = openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_API,
                instructions=instructions
            )

            # Show assistant response
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

            # Pause until it is not longer queued
            count = 0
            while (run.status == "queued" or run.status == "in_progress" and count < 5):
                time.sleep(1)
                run = openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                count = count + 1

            if run.status == "requires_action":

                # Obtain the tool outputs by running the necessary functions
                aristotle_output = run_functions(run.required_action)
                aristotle_output = run_functions(run.required_action)

                # Submit the outputs to the Assistant
                run = openai_client.beta.threads.runs.submit_aristotle_output(
                    thread_id=thread.id,
                    run_id=run.id,
                    aristotle_output=aristotle_output
                )

            # Wait until it is not queued
            count = 0
            while (run.status == "queued" or run.status == "in_progress" or run.status == "requires_action" and count < 5):
                time.sleep(2)
                run = openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                count = count + 1

            # After run is completed, fetch thread messages
            messages = openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # TODO look for method call in data in messages and execute method
            print(f"---------------------------------------------")
            print(f"THREAD MESSAGES: {messages}")

            # With every message, include user's message into the conversation history
            for message in messages:  # Loop through the paginated messages
                system_message = {"role": "system",
                                  "content": message.content[0].text.value}
                # Append to the conversation history
                conversation_history.append(system_message)

            # Get the response from ChatGPT
            answer = chat_with_bot(question, conversation_history, instructions)

            print(f"---------------------------------------------")
            print(f"ARISTOTLE: {answer}")
            return str(answer)
        except Exception as e:
            answer = 'Sorry, I could not process that.'
            print(f"An error occurred: {e}")

        return str(answer)
    except Exception as e:
        logger.error(f"Error in chat_with_bot: {str(e)}")
        return "Error processing request", 500

# To make the necessary function calls and return their outputs as JSON strings
def run_functions(required_actions):
    aristotle_output = []
    for tool_call in required_actions.submit_aristotle_output.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Call the corresponding Python functionews inn
        if func_name in functions:
            function = functions[func_name]

            result = function(**args)

            # Function's output is converted to JSON
            result_str = json.dumps(result)

            # The result is appended into the list of outputs
            aristotle_output.append({
                "tool_call_id": tool_call.id,
                "output": result_str,
            })

    return aristotle_output

if __name__ == "__main__":
    app.run(port=8001, debug=True)
