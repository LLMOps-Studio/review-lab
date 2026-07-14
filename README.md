# 🧪 Review Lab: Multi-Agent AI Code Reviewer

![Status: Completed](https://img.shields.io/badge/Status-Completed-success)
![Stack: LangGraph | FastAPI | Langfuse](https://img.shields.io/badge/Stack-LangGraph%20%7C%20FastAPI%20%7C%20Langfuse-blue)

## 📌 Problem & Objective
Traditional code review is bottlenecked by human bandwidth, while single-prompt AI reviewers often hallucinate or miss subtle architectural flaws. **Review Lab** solves this by implementing a **Multi-Agent Supervisor Pattern** (powered by LangGraph). Instead of one generic AI, the code is analyzed by specialized agents (Security, Style, Performance) grounded with actual static analysis tools (`bandit`, `pylint`, `ast`), orchestrated by a Lead Supervisor.

*Note: This architecture is a direct code-review adaptation of the Supervisor Pattern used in complex financial reasoning engines like Agentic Investing.*

## 🏗 Architecture
1. **GitHub Webhook:** Triggers on PR creation.
2. **FastAPI Background Worker:** Asynchronously processes the diff to prevent GitHub timeouts.
3. **LangGraph Orchestrator:** - **Supervisor Node:** Routes logic based on file type/state.
   - **Security Agent:** Uses `bandit` tool to find hardcoded secrets/injections.
   - **Style Agent:** Uses `pylint` tool to enforce PEP 8.
   - **Performance Agent:** Uses `ast` to detect O(N^2) complexity bottlenecks.
   - **Summarizer:** Compiles findings into a professional markdown comment.
4. **Langfuse:** Traces token usage and latency per sub-agent.

## 📊 Concrete Metrics (Smoke Test Baseline)
| Metric | Value | Target |
|---|---|---|
| End-to-End Review Latency | ~18.4s (Phi-3) | < 30s |
| Tool Grounding Accuracy | 100% | 100% (No Hallucinations) |
| CI/CD Pipeline Mock | 100% PASS | PASS |

## 🔌 Extension Points (Modular Design)
This lab is built to be modular. Based on specific company needs, the following components can be swapped in under 1 hour:

| Client Requirement | Target Component | Modification |
|---|---|---|
| Cloud LLM (OpenAI/Anthropic) | `llmops-common` | Switch `OLLAMA_DEFAULT_MODEL` to OpenAI via `BaseLLMClient` |
| Alternative Orchestration | `src/review_lab/agents/graph.py` | Swap LangGraph for CrewAI or AutoGen |
| Enterprise Observability | `.env` | Swap local Langfuse keys for Datadog or Arize AI |

## 🚀 Setup Instructions

```bash
cd ../../LLMOpsPlatform/llmops-platform && docker compose up -d ollama

cd ../../ReviewLab/review-lab
python -m venv .venv && source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -e .
uvicorn review_lab.api:app --reload --port 8005
```

Or via the full stack (`docker compose up --build` from `LLMOpsPlatform/llmops-platform`), and interact through the **Review Lab** tab in the [Studio UI](../../LLMOpsUI), or as a `code_review` node in a Studio DAG.