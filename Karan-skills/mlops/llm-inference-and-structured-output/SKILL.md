---
name: llm-inference-and-structured-output
description: "Use for LLM inference, quantization, serving, and constrained/structured generation: llama.cpp, GGUF, vLLM, Guidance, Outlines, and refusal/behavior model surgery."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mlops, inference, quantization, serving, structured-output, llama-cpp, vllm]
    related_skills: [llm-training-workflows]
---

# LLM Inference and Structured Output

## Overview
Use this umbrella when deploying or controlling LLM inference: local GGUF/llama.cpp, high-throughput vLLM serving, quantization, JSON/regex/grammar-constrained output, or model behavior surgery experiments.

## When to Use
- Convert or run GGUF models with llama.cpp.
- Serve models with vLLM/OpenAI-compatible APIs.
- Enforce JSON/regex/Pydantic/XML/code schemas with Guidance or Outlines.
- Explore model behavior modification/abliteration workflows.

## Subworkflows

### Local inference and quantization
Match model size, context, quantization, and hardware. Verify load, prompt, throughput, and output quality before declaring a deployment ready.

### Serving
Check API compatibility, batching, context length, GPU memory, and health endpoints. Run a smoke request against the served endpoint.

### Structured generation
Prefer schema-first design. Test adversarial/edge prompts and parse failures, not just happy paths.

### Model surgery
Treat behavior modification experiments as research: preserve baselines, configs, and evaluation results.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/` as reference packages with `README.md` entry points, not active skills. Use `serving-llms-vllm` there for vLLM deployment details, alongside llama.cpp and model-surgery references.

## Verification Checklist
- [ ] Model files/checkpoints exist and match expected format.
- [ ] Endpoint or local binary responds to a real test prompt.
- [ ] Structured outputs parse under the declared schema.
- [ ] Performance and memory claims are measured, not guessed.
