from cred import OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, ASSISTANT_API,TWILIO_FROM_NUMBER,TWILIO_TO_NUMBER
import json
from flask import Flask, request, render_template
from openai import OpenAI
import time
from generic_chat import chat_with_gpt
from generic_news import fetch_news
import sys
from pathlib import Path
import datetime
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import logging

senddate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
app = Flask(__name__)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openaiclient = OpenAI(api_key=OPENAI_API_KEY)

# Start tracking previous interactions
conversation_history = []
assistant_id = ASSISTANT_API

# Establish a correspondence between the assistant's function names and your Python functions

functions = {
    'get_news': fetch_news,

}

# Read in the personality context from the file 'instructions.txt' 

with open('instructions.txt', 'r') as file:
    instructions = file.read().strip()

@app.route("/aristotle", methods=["POST", "GET"])
def wa_reply():
    twilio_response = MessagingResponse()
    reply = twilio_response.message()

    answer = chat_with_bot()
    
    numbers = [TWILIO_TO_NUMBER, TWILIO_TO_NUMBER2,TWILIO_TO_NUMBER3]  
    # add all the numbers to which you want to send a message in this list

    for number in numbers:
        message = client.messages.create(
        body=answer,
        from_='whatsapp:+'+TWILIO_FROM_NUMBER,
        to='whatsapp:+'+number,
    )

    
    message = client.messages.create(
        body=answer,
        from_='whatsapp:+'+TWILIO_FROM_NUMBER,
        to='whatsapp:+'+TWILIO_TO_NUMBER
        
        
    )

    print(message.sid)
    logging.basicConfig(level=logging.DEBUG, filename="/home/vish/Projects/logs/openailog.txt", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    logger = logging.getLogger()
    logger.debug((answer))
    return message.sid


def chat_with_bot():
   # Obtain the request's user message
    question = request.form.get('Body', '').lower()
    print("user query ", question)

    thread = openaiclient.beta.threads.create()
    try:
       # Insert user message into the thread
        message = openaiclient.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        # Run the assistant
        run = openaiclient.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions=instructions
        )

        # Show assistant response
        run = openaiclient.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        # Pause until it is not longer queued
        count = 0
        while (run.status == "queued" or run.status == "in_progress" and count < 5):
            time.sleep(1)
            run = openaiclient.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            count = count + 1

        if run.status == "requires_action":

            # Obtain the tool outputs by running the necessary functions
            aristotle_output = run_functions(run.required_action)
            aristotle_output = run_functions(run.required_action)

            # Submit the outputs to the Assistant
            run = openaiclient.beta.threads.runs.submit_aristotle_output(
                thread_id=thread.id,
                run_id=run.id,
                aristotle_output=aristotle_output
            )

        # Wait until it is not queued
        count = 0
        while (run.status == "queued" or run.status == "in_progress" or run.status == "requires_action" and count < 5):
            time.sleep(2)
            run = openaiclient.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            count = count + 1

        # After run is completed, fetch thread messages
        messages = openaiclient.beta.threads.messages.list(
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


# Run the interaction
if __name__ == "__main__":
    app.run(port=8001, debug=True)
