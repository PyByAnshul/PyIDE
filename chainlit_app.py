import chainlit as cl
import traceback
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
# Set your Gemini API key
genai.configure(api_key=os.getenv('GOOGLE_API'))

@cl.on_chat_start
async def main():
    await cl.Message(content="Hello World! Ask me anything.").send()

@cl.on_message
async def handle_message(message: cl.Message):
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")  # Or "gemini-pro"
        response = model.generate_content(message.content)

        # Access the response text
        if response and response.text:
            await cl.Message(content=response.text).send()
        else:
            await cl.Message(content="Error: Gemini returned no response.").send()

    except Exception as e:
        traceback.print_exc()
        await cl.Message(content=f"An error occurred: {str(e)}").send()
