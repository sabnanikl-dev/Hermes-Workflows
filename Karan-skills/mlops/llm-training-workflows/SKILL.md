---
name: llm-training-workflows
description: "Use for LLM fine-tuning and training workflows: Axolotl, TRL, GRPO/RL, PEFT/LoRA/QLoRA, PyTorch FSDP, Unsloth, experiment tracking, and evaluation harnesses."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mlops, training, fine-tuning, lora, grpo, fsdp, evaluation]
    related_skills: [weights-and-biases, evaluating-llms-harness]
---

# LLM Training Workflows

## Overview
Use this umbrella for model training, fine-tuning, RL alignment, distributed training, evaluation, and experiment tracking. It consolidates framework-specific narrow skills into one lifecycle.

## When to Use
- Configure Axolotl, TRL, PEFT/LoRA/QLoRA, GRPO/RL, FSDP, or Unsloth.
- Plan or debug fine-tuning runs under GPU/memory constraints.
- Evaluate LLMs with harnesses or log experiments with W&B.

## Workflow
1. Define objective, dataset, base model, metric, and safety/quality constraints.
2. Choose training stack: quick LoRA/Unsloth, configurable Axolotl, TRL for SFT/DPO/GRPO, FSDP for distributed scale.
3. Build config and dry-run data/tokenization.
4. Run a small smoke training job before full training.
5. Evaluate and log artifacts/metrics.
6. Package adapters/checkpoints with reproducible config.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/` as reference packages with `README.md` entry points, not active skills. Evaluation-harness details now live under `references/absorbed/evaluating-llms-harness/README.md` with benchmark/API/distributed/custom-task references.

## Verification Checklist
- [ ] Dataset and labels inspected before training.
- [ ] GPU memory assumptions validated with a small run.
- [ ] Metrics/eval suites match the objective.
- [ ] Config, seed, model, data version, and outputs are recorded.
