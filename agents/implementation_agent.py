import os
import json
import chainlit as cl
from .base_agent import Agent

class ImplementationAgent(Agent):
    def __init__(self, name, client, prompt):
        super().__init__(name, client, prompt)

    async def execute(self, message_history):
        function_name, arguments, response_content = await super().execute(message_history)

        if function_name:
            if function_name == "implement_milestone":
                self._ensure_file_exists('index.html', '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Jive</title><link rel="stylesheet" href="style.css"></head><body></body></html>')
                self._ensure_file_exists('style.css', '/* Styles for Jive website */')
                self._update_plan_md()
                response_content += "\nMilestone implemented."

            elif function_name == "updateArtifact":
                arguments_dict = json.loads(arguments)
                filename = arguments_dict.get("filename")
                contents = arguments_dict.get("contents")

                if filename and contents:
                    self._ensure_file_exists(filename, contents)
                    response_content += f"\nArtifact '{filename}' was updated."

        return response_content

    def _ensure_file_exists(self, filename, initial_content):
        artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
        os.makedirs(artifacts_dir, exist_ok=True)
        file_path = os.path.join(artifacts_dir, filename)
        
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(initial_content)

    def _update_plan_md(self):
        plan_path = os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'plan.md')
        if os.path.exists(plan_path):
            with open(plan_path, 'r') as f:
                content = f.read()
            
            # Find the first uncompleted milestone and mark it as completed
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('- [ ]'):
                    lines[i] = line.replace('- [ ]', '- [x]', 1)
                    break
            
            updated_content = '\n'.join(lines)
            
            with open(plan_path, 'w') as f:
                f.write(updated_content)

    async def update_artifact(self, filename, contents):
        self._ensure_file_exists(filename, contents)
