from dotenv import load_dotenv
import chainlit as cl
from prompts import PLANNING_PROMPT
import base64
from agents.base_agent import Agent
from agents.implementation_agent import ImplementationAgent

load_dotenv()

# Note: If switching to LangSmith, uncomment the following, and replace @observe with @traceable
# from langsmith.wrappers import wrap_openai
# from langsmith import traceable
# client = wrap_openai(openai.AsyncClient())

from langfuse.decorators import observe
from langfuse.openai import AsyncOpenAI
 
client = AsyncOpenAI()

planning_agent = Agent(name="Planning Agent", client=client, prompt=PLANNING_PROMPT)
implementation_agent = ImplementationAgent("Implementation", client, PLANNING_PROMPT)

gen_kwargs = {
    "model": "gpt-4o",
    "temperature": 0.2
}

SYSTEM_PROMPT = """\
You are a pirate.
"""

@observe
@cl.on_chat_start
def on_chat_start():    
    message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    cl.user_session.set("message_history", message_history)

@observe
async def generate_response(client, message_history, gen_kwargs):
    response_message = cl.Message(content="")
    await response_message.send()

    stream = await client.chat.completions.create(
        messages=message_history, 
        stream=True, 
        tools=[{
            "type": "function",
            "function": {
                "name": "implement_milestone",
                "description": "Implement the next milestone in the plan",
                "parameters": {"type": "object", "properties": {}}
            }
        }],
        **gen_kwargs
    )

    function_call = None
    response_content = ""

    async for part in stream:
        delta = part.choices[0].delta
        if delta.tool_calls:
            function_call = delta.tool_calls[0]
        if delta.content:
            response_content += delta.content
            await response_message.stream_token(delta.content)
    
    if function_call and function_call.function.name == "implement_milestone":
        implementation_response = await implementation_agent.execute(message_history)
        await response_message.stream_token("\n\nImplementation Agent Response:\n" + implementation_response)
        response_content += "\n\nImplementation Agent Response:\n" + implementation_response

    await response_message.update()

    return response_content

@cl.on_message
@observe
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])

    # Processing images exclusively
    images = [file for file in message.elements if "image" in file.mime] if message.elements else []

    if images:
        # Read the first image and encode it to base64
        with open(images[0].path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        message_history.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message.content
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })
    else:
        message_history.append({"role": "user", "content": message.content})
    
    response_content = await implementation_agent.execute(message_history)

    message_history.append({"role": "assistant", "content": response_content})
    cl.user_session.set("message_history", message_history)

    return response_content




if __name__ == "__main__":
    cl.main()
