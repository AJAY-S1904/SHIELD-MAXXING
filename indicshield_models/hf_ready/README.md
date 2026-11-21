---
language:
- en
- hi
- bn
- ta
- te
- mr
- gu
- kn
- ml
- pa
- ur
tags:
- ai-safety
- guardrails
- jailbreak-detection
- indicbert
- qwen2.5
- onnx
license: apache-2.0
pipeline_tag: text-classification
---

# 🛡️ IndicShield-JEV
**Multilingual Jailbreak Detection · IndicBERTv2 × Qwen2.5-0.5B × JEV Architecture**

## Overview
IndicShield-JEV bridges the safety gap where LLMs collapse when confronted with multilingual jailbreak attempts in Indian languages, Romanized transliterated Indic scripts (Hinglish/Tanglish), and code-mixed prompts.

## Architecture: JEV (Judge-Evidence-Verdict)
- **IndicBERTv2 Backbone** (768d): Captures 12+ Indic languages, script phonetics, and native tokens.
- **Qwen2.5-0.5B Backbone** (896d): Captures deep conversational semantics, intent, and cross-lingual transfer.
- **Judge Module**: 8-head bidirectional cross-attention bridge aligning both representation spaces.
- **Evidence Module**: 32 learned threat archetype prototype tokens for threat scoring.
- **Verdict Module**: Calibrated classification head outputting safety verdicts and probabilities.

## Deployment
Includes PyTorch checkpoints and an ultra-fast ONNX runtime model (`indicshield_jev_fusion.onnx`) ready for CPU, edge, and browser inference.
