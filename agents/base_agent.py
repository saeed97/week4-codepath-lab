import os
import chainlit as cl

class Agent:
    """
    Base class for all agents.
    """

    tools = [
        {
            "type": "function",
            "function": {
                "name": "updateArtifact",
                "description": "Update an artifact file which is HTML, CSS, or markdown with the given contents.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to update.",
                        },
                        "contents": {
                            "type": "string",
                            "description": "The markdown, HTML, or CSS contents to write to the file.",
                        },
                    },
                    "required": ["filename", "contents"],
                    "additionalProperties": False,
                },

            }
        },
        {
            "type": "function",
            "function": {
                "name": "implement_milestone",
                "description": "Implement the next milestone in the plan",
                "parameters": {"type": "object", "properties": {}}
            }
        
        }

    ]

    def __init__(self, name, client, prompt="", gen_kwargs=None):
        self.name = name
        self.client = client
        self.prompt = prompt
        self.gen_kwargs = gen_kwargs or {
            "model": "gpt-4o",
            "temperature": 0.2
        }

    async def execute(self, message_history):
        """
        Executes the agent's main functionality.

        Note: probably shouldn't couple this with chainlit, but this is just a prototype.
        """
        copied_message_history = message_history.copy()

        # Check if the first message is a system prompt
        if copied_message_history and copied_message_history[0]["role"] == "system":
            # Replace the system prompt with the agent's prompt
            copied_message_history[0] = {"role": "system", "content": self._build_system_prompt()}
        else:
            # Insert the agent's prompt at the beginning
            copied_message_history.insert(0, {"role": "system", "content": self._build_system_prompt()})

        response_message = cl.Message(content="")
        await response_message.send()

        stream = await self.client.chat.completions.create(
            messages=copied_message_history, 
            stream=True, 
            tools=self.tools, 
            tool_choice="auto", 
            **self.gen_kwargs
        )

        function_name = ""
        arguments = ""
        response_content = ""

        async for part in stream:
            delta = part.choices[0].delta
            if delta.tool_calls:
                tool_call = delta.tool_calls[0]
                function_name += tool_call.function.name or ""
                arguments += tool_call.function.arguments or ""
            if delta.content:
                response_content += delta.content
                await response_message.stream_token(delta.content)

        if function_name:
            print(f"DEBUG: function_name: {function_name}")
            print(f"DEBUG: arguments: {arguments}")

        await response_message.update()

        return function_name, arguments, response_content

    def _build_system_prompt(self):
        """
        Builds the system prompt including the agent's prompt and the contents of the artifacts folder.
        """
        artifacts_content = "<ARTIFACTS>\n"
        artifacts_dir = "artifacts"

        if os.path.exists(artifacts_dir) and os.path.isdir(artifacts_dir):
            for filename in os.listdir(artifacts_dir):
                file_path = os.path.join(artifacts_dir, filename)
                if os.path.isfile(file_path):
                    with open(file_path, "r") as file:
                        file_content = file.read()
                        artifacts_content += f"<FILE name='{filename}'>\n{file_content}\n</FILE>\n"
        
        artifacts_content += "</ARTIFACTS>"

        return f"{self.prompt}\n{artifacts_content}"
    



#             prompt = """You are an Implementation Agent. Your task is to implement or update a single milestone from the plan.md file. Follow these steps:

# 1. Read the plan.md file and identify the next uncompleted milestone.
# 2. Implement or update the milestone by modifying index.html and style.css in the artifacts folder. If these files don't exist, create them.
# 3. Mark the completed milestone in plan.md.
# 4. Provide a brief summary of the changes made.

# Focus on one milestone at a time and make small, incremental changes. If given feedback, apply the necessary fixes to the current milestone."""