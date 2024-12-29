"""
Chat module for Aristotle WhatsApp bot.
Handles interactions with OpenAI's GPT model.
"""

from typing import List, Dict, Any
import logging
from openai import OpenAI
from cred import OPENAI_API_KEY

logger = logging.getLogger(__name__)

def chat_with_gpt(
    question: str, 
    conversation_history: List[Dict[str, str]], 
    personality: str
) -> str:
    """
    Interact with ChatGPT to get responses.

    Args:
        question (str): The user's question
        conversation_history (list): List of previous messages
        personality (str): The AI's personality instructions

    Returns:
        str: The AI's response

    Raises:
        Exception: If there's an error communicating with OpenAI
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Manage conversation history token limit
        while sum(len(msg['content'].split()) for msg in conversation_history) > 4096:
            conversation_history.pop(0)

        # Add user's question to conversation
        conversation_history.append({
            "role": "user",
            "content": question
        })

        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": personality},
                *conversation_history,
            ]
        )

        answer = response.choices[0].message.content
        logger.debug(f"ChatGPT response: {answer}")

        # Update conversation history
        conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        return answer

    except Exception as e:
        logger.error(f"Error in chat_with_gpt: {str(e)}")
        return "I apologize, but I'm having trouble processing your request."



