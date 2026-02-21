"""
Quick Start Example – OpenAI API

This file provides a minimal, end-to-end example for interacting with
the OpenAI API using Python. It is intended for first-time users who
want to verify their setup and start sending prompts to an AI model
as quickly as possible.

The examples in this file demonstrate:
- Sending a simple question to the AI
- Performing text classification
- Generating structured or creative content
- Extracting structured information from 2_unstructured text
- Running the program in an interactive prompt mode

"""

import os
from openai import OpenAI


# Initialize OpenAI client
client = OpenAI()
messages = []

def ask_ai(model: str = "gpt-4o") -> str:
    global messages
    """
    Simple function to ask AI a question.
    
    Args:
        prompt: Your question or instruction
        model: Which AI model to use (default: gpt-4o)
        
    Returns:
        AI's response as text
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            n=1
        )
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content

        
    except Exception as e:
        return f"Error: {str(e)}\n\nMake sure OPENAI_API_KEY is set in your .env file"


# ----------------------------------------------------------------
# QUICK START EXAMPLES - Try these!
# ----------------------------------------------------------------

if __name__ == "__main__":
    

    while True:
        user_input = input("\nYour prompt: ")

        if user_input.strip():
            print("\nAI Response:")
            print("-" * 70)
            messages.append({"role": "user", "content": user_input})
            response = ask_ai()
            print(response)
            print(messages)
