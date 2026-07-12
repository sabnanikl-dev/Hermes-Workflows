---
name: multimodal-ml-workflows
description: "Use for multimodal ML workflows: image generation, segmentation, CLIP retrieval/classification, Whisper transcription, AudioCraft generation, and Hugging Face Hub model/dataset operations."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mlops, multimodal, vision, audio, huggingface, stable-diffusion, whisper]
    related_skills: [llm-inference-and-structured-output]
---

# Multimodal ML Workflows

## Overview
Use this umbrella for non-text-only ML workflows spanning vision, audio, image generation, speech recognition, cross-modal retrieval, and Hugging Face Hub operations.

## When to Use
- Stable Diffusion / diffusers image generation, img2img, inpainting, or custom pipelines.
- Segment Anything, CLIP, or other vision-language/image analysis tasks.
- Whisper transcription/translation/language ID.
- AudioCraft/MusicGen/AudioGen generation.
- Search/download/upload models and datasets on Hugging Face Hub.

## Workflow
1. Identify modality, input/output format, and hardware/API constraints.
2. Choose the smallest reliable model/tool for the task.
3. Prepare inputs and output directories.
4. Run a smoke inference/generation/transcription.
5. Inspect outputs visually/audibly/textually and report paths/URLs.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/` as reference packages with `README.md` entry points, not active skills. Notable absorbed packages include `audiocraft-audio-generation`, `segment-anything-model`, and `huggingface-hub`.

## Verification Checklist
- [ ] Inputs exist and are in supported formats.
- [ ] Model/download/auth requirements checked.
- [ ] Outputs are actually generated and inspected.
- [ ] File paths/URLs and parameters are included in final handoff.
