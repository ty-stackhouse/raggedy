import os
import sys
import json
import traceback
from openai import OpenAI

# Setup OpenRouter/OpenAI client
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("Error: OPENROUTER_API_KEY not set")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Load the system prompt
try:
    with open(".github/prompts/coder_agent.txt", "r") as f:
        system_prompt = f.read()
except Exception as e:
    print(f"Error reading system prompt: {e}")
    sys.exit(1)

# Load the Task
task_payload = os.environ.get("TASK_PAYLOAD")
if not task_payload:
    print("Error: No TASK_PAYLOAD provided")
    sys.exit(1)

# Call the model
try:
    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_payload},
        ],
        temperature=0,
        max_tokens=4096,
        extra_body={
            "transforms": ["middle-out"],
            "route": "fallback",
        },
    )
except Exception:
    print("Model call failed:")
    traceback.print_exc()
    sys.exit(2)

# Extract content
try:
    content = response.choices[0].message.content
except Exception:
    # Try alternate attribute access if library shaped differently
    try:
        content = response.choices[0]['message']['content']
    except Exception:
        print("Unexpected response structure:")
        print(response)
        sys.exit(3)

# Normalize text to JSON blob
text = content.strip()
# If the assistant returned extra text, try to find the first '{'
first_brace = text.find('{')
if first_brace != -1:
    json_text = text[first_brace:]
else:
    json_text = text

# Validate JSON
try:
    parsed = json.loads(json_text)
except Exception:
    print("Failed to parse model output as JSON. Raw output below:")
    print(text)
    sys.exit(4)

# Write solution.json
out_path = "solution.json"
with open(out_path, "w") as f:
    json.dump(parsed, f, indent=2)

print(f"Wrote {out_path}")
print(json.dumps(parsed)[:1000])
