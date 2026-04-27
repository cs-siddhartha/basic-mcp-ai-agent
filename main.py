"""
Agent loop runner for MCP tool execution.
"""

import asyncio
import os
from concurrent.futures import TimeoutError

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent.loop_core import extract_first_line, parse_function_call
from instructions.prompt import system_prompt_template
from instructions.task import task

load_dotenv()

MODEL = "gemini-3.1-flash-lite-preview"
MAX_ITERATIONS = 6
LLM_TIMEOUT = 15

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_tools_desc(tools) -> str:
  lines = []
  for i, tool in enumerate(tools, 1):
    props = (tool.inputSchema or {}).get("properties", {})
    params = ", ".join(props.keys()) or "no params"
    lines.append(f"{i}. {tool.name}({params})")
  return "\n".join(lines)


async def generate_with_timeout(prompt: str, timeout: int = LLM_TIMEOUT):
  """Run the blocking Gemini call in a thread with a timeout."""
  loop = asyncio.get_event_loop()
  return await asyncio.wait_for(
    loop.run_in_executor(
      None,
      lambda: client.models.generate_content(model=MODEL, contents=prompt),
    ),
    timeout=timeout,
  )


async def run_agent_loop():
  server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
  )

  async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
      await session.initialize()
      print("Connected to server.py")

      tools = (await session.list_tools()).tools
      tools_desc = build_tools_desc(tools)
      print(f"Loaded {len(tools)} tools\n")

      system_prompt = system_prompt_template.format(tools_desc=tools_desc)

      history: list[str] = []
      for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- Iteration {iteration} ---")

        context = "\n".join(history) if history else "(no prior steps)"
        prompt = (
          f"{system_prompt}\n"
          f"Task: {task}\n\n"
          f"Previous steps:\n{context}\n\n"
          f"What is your next single action?"
        )

        try:
          response = await generate_with_timeout(prompt)
        except (TimeoutError, asyncio.TimeoutError):
          print("LLM timed out - stopping.")
          break
        except Exception as e:
          print(f"LLM error: {e}")
          break

        text = extract_first_line(response.text)
        print(f"LLM: {text}")

        if text.startswith("FINAL_ANSWER:"):
          print("\n=== Agent done ===")
          print(text)
          break

        if not text.startswith("FUNCTION_CALL:"):
          print("Unexpected response format - stopping.")
          break

        func_name, raw_args = parse_function_call(text)

        tool = next((t for t in tools if t.name == func_name), None)
        if tool is None:
          msg = f"Unknown tool {func_name!r}"
          print(msg)
          history.append(f"Iteration {iteration}: {msg}")
          continue

        arg_names = list(((tool.inputSchema or {}).get("properties", {})).keys())
        arguments = {name: val for name, val in zip(arg_names, raw_args)}

        print(f"-> {func_name}({arguments})")
        try:
          result = await session.call_tool(func_name, arguments=arguments)
          payload = (
            result.content[0].text
            if result.content and hasattr(result.content[0], "text")
            else str(result)
          )
        except Exception as e:
          payload = f"ERROR: {e}"

        print(f"<- {payload}")
        history.append(
          f"Iteration {iteration}: called {func_name}({arguments}) -> {payload}"
        )
      else:
        print("\nReached MAX_ITERATIONS without FINAL_ANSWER.")


def main():
  asyncio.run(run_agent_loop())


if __name__ == "__main__":
  main()
