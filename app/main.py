import argparse
import os
import sys
import json
import subprocess

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

def read_tool_call(tool_call):
        arguments = json.loads(tool_call.function.arguments)
        file_path = arguments["file_path"]
        with open(file_path) as f:
            file_contents = f.read()
            return file_contents

def write_tool_call(tool_call):
    arguments = json.loads(tool_call.function.arguments)
    file_path = arguments["file_path"]
    content = arguments["content"]
    with open(file_path, "w") as f:
        f.write(content)
        return f"Successfully wrote to {file_path}"

def bash_tool_call(tool_call):
    arguments = json.loads(tool_call.function.arguments)
    command = arguments["command"]
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    message = [{"role": "user", "content": args.p}]
    tools = [
            {
                "type": "function",
                "function": {
                    "name": "Read",
                    "description": "Read and return the contents of a file",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                        "type": "string",
                        "description": "The path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Write",
                    "description": "Write content to a file",
                    "parameters": {
                    "type": "object",
                    "required": ["file_path", "content"],
                    "properties": {
                        "file_path": {
                        "type": "string",
                        "description": "The path of the file to write to"
                        },
                        "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                        }
                    }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Bash",
                    "description": "Execute a shell command",
                    "parameters": {
                    "type": "object",
                    "required": ["command"],
                    "properties": {
                        "command": {
                        "type": "string",
                        "description": "The command to execute"
                        }
                    }
                    }
                }
            },]
    while True:
        
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=message,
            tools=tools,
        )

        assistant_message = chat.choices[0].message
        message.append(assistant_message)

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        if not chat.choices[0].message.tool_calls: 
            break
        for tool_call in chat.choices[0].message.tool_calls:
            if tool_call.function.name == "Read":
                Read_Val = read_tool_call(tool_call)
                message.append({"role": "tool","tool_call_id": tool_call.id, "content": Read_Val})
            
            elif tool_call.function.name == "Write":
                Write_Val = write_tool_call(tool_call)
                message.append({"role": "tool","tool_call_id": tool_call.id, "content": Write_Val})
            
            elif tool_call.function.name == "Bash":
                bash_out = bash_tool_call(tool_call)
                message.append({"role": "tool","tool_call_id": tool_call.id, "content": bash_out.stdout})
            else :
                return None



    # TODO: Uncomment the following line to pass the first stage
    if chat.choices[0].message.content:
        print(chat.choices[0].message.content)


        
    

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    

if __name__ == "__main__":
    main()
