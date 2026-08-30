---
name: openrouter-image-analysis
description: Analyze images via OpenRouter using specific vision models (GPT-5.4 Image 2, etc.). Use when the user requests image analysis with a particular model, or when you need higher-quality vision than the built-in vision_analyze tool. Also covers transparent PNG creation from logos.
tags: [openrouter, image, vision, analysis, logo, typography]
triggers:
  - "analyze image with"
  - "use gpt for image"
  - "image analysis"
  - "typography analysis"
  - "logo analysis"
  - "transparent background"
  - "remove background"
---

# OpenRouter Image Analysis

Route image analysis to specific models via OpenRouter API when the built-in `vision_analyze` tool isn't sufficient or the user requests a particular model.

## When to Use

- User requests analysis with a specific model (e.g., "use gpt-5.4-image-2")
- Typography/logo analysis that benefits from stronger vision models
- Need detailed structured analysis (brand audit, font identification, design review)
- Built-in `vision_analyze` gives too-generic results

## Setup

- API key: `~/.hermes/.env` → `OPENROUTER_API_KEY` (read via python-dotenv)
- No additional installs needed (stdlib only: urllib, json, base64)
- Requires `python-dotenv` installed: `pip3 install python-dotenv`

## Step 1: Check Available Models

```bash
ORKEY=$(grep "^OPENROUTER_API_KEY=" ~/.hermes/.env | cut -d= -f2)
curl -s "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $ORKEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('data', []):
    mid = m.get('id', '')
    if 'image' in mid.lower() or 'vision' in mid.lower():
        print(f\"{mid}: {m.get('name', '')}\")
"
```

Common vision models on OpenRouter:
- `openai/gpt-5.4-image-2` — Latest OpenAI vision, best for detailed analysis
- `openai/gpt-5.4-pro` — Strong reasoning + vision
- `openai/gpt-5-image` — Older but capable
- `anthropic/claude-sonnet-4` — Good for structured analysis

## Step 2: Make the API Call

Write a Python script to `/tmp/` and run it. Template:

```python
import os, json, base64, urllib.request
from dotenv import dotenv_values

env = dotenv_values(os.path.expanduser("~/.hermes/.env"))
api_key = env.get("OPENROUTER_API_KEY", "")

with open("/path/to/image.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "openai/gpt-5.4-image-2",  # change model as needed
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": "YOUR PROMPT HERE"}
        ]
    }],
    "max_tokens": 4000
}

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hermes.local",
        "X-Title": "Hermes Agent"
    }
)

with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read().decode())
    print(result["choices"][0]["message"]["content"])
```

## Transparent PNG Creation

For logos on white backgrounds — remove background with Pillow:

```python
from PIL import Image
import numpy as np

img = Image.open('input.jpg').convert('RGBA')
data = np.array(img)
gray = np.mean(data[:,:,:3], axis=2)
data[gray > 240, 3] = 0  # white pixels become transparent
Image.fromarray(data).save('output.png')
```

**Dependencies:** `pip3 install Pillow numpy`
**Pitfall:** System python3 may not have numpy. Install with `pip3 install numpy Pillow`.

## Pitfalls

- **API key location:** Always read from `~/.hermes/.env` via python-dotenv, not from env vars (may not be set in terminal sessions)
- **Model names:** Use full `provider/model` format (e.g., `openai/gpt-5.4-image-2`)
- **Image size:** OpenRouter has image size limits. Resize very large images first.
- **Base64 encoding:** Use `data:image/jpeg;base64,...` format for inline images
- **Timeout:** Set `timeout=120` for vision calls — they're slower than text
- **Don't use execute_code for this:** The base64 encoding of large images in an execute_code script can hit the 50KB stdout cap. Write the script to `/tmp/` and run via `terminal()` instead.
