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
        model="minimax/minimax-m2.1",          # $0.27/$1.10 - Best Value: Ultra-cheap, great for high-volume CI/CD
        # model="z-ai/glm-4.7",                # $0.40/$1.50 - Balanced: Good general performance, low cost fallback
        # model="moonshotai/kimi-k2.5",        # $0.50/$2.80 - Visual: Best for tasks involving screenshots or UI
        # model="openai/gpt-5.2-codex",        # $1.75/$14.00 - Specialized: Optimized for complex refactoring/agents
        # model="google/gemini-3-pro-preview", # $2.00/$12.00 - Frontier: Massive context window for repo-wide analysis
        # model="anthropic/claude-3.5-sonnet", # $3.00/$15.00 - Gold Standard: Highest accuracy for interactive/difficult tasks

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

# Remove markdown code block markers (```json ... ``` or just ``` ... ```)
import re
# Strip opening/closing code block markers with optional language identifier
text = re.sub(r'^```[a-zA-Z0-9]*\s*', '', text)
text = re.sub(r'\s*```$', '', text)

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

# Log to stderr so it shows in workflow but doesn't pollute solution.json
import sys as _sys
print(f"✓ Wrote {out_path}", file=_sys.stderr)
print(json.dumps(parsed)[:1000], file=_sys.stderr)
