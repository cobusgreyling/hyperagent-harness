# HyperAgent Harness

A simplified implementation of the HyperAgent self-improvement loop, demonstrating how AI agents evolve their own harness components through metacognitive self-modification. Powered by **NVIDIA Nemotron Super 49B**.

Based on [HyperAgents](https://github.com/facebookresearch/Hyperagents) (Zhang et al., 2026) — self-referential agents that improve both their task-solving behaviour and their self-improvement mechanism.

---

## The Idea

A **harness** is the software system developers build around an AI agent — tools, memory, planning, verification, retry logic, context engineering. Today, developers hand-engineer these components.

HyperAgents show that agents can **build these components for themselves**. Starting from a bare LLM call with no tools, no memory, and no planning, a self-improving agent evolves its own harness through iterative code modification.

This repo demonstrates that process. A meta agent reads the task agent's code and past results, then rewrites the code to improve performance. Over multiple generations, harness components emerge without being explicitly programmed.

---

## What's Inside

| File | Description |
|------|-------------|
| `hyperagent.py` | Core HyperAgent loop — task agent, meta agent, archive, evaluation, emergence detection |
| `app.py` | Gradio GUI with evolution runner and emergence analysis |
| `blog.md` | Full blog post: "When Agents Engineer Their Own Harness" |

---

## How It Works

```
1. Start with a bare task agent (single LLM call, no harness)
2. Evaluate on 12 math/reasoning tasks → score
3. Meta agent reads code + results → rewrites task agent code
4. Every 3 generations: metacognitive self-modification (meta agent improves its own strategy)
5. Add to archive of stepping stones
6. Repeat for N iterations
7. Evaluate best agent on held-out tasks
8. Detect which harness components emerged
```

### The Evolutionary Loop

```
Archive of HyperAgents
    │
    ├── Select parent (weighted by score)
    │
    ├── Meta Agent reads:
    │   ├── Current task agent code
    │   ├── Past evaluation results (pass/fail per task)
    │   ├── History of recent generations
    │   └── Persistent memory from prior generations
    │
    ├── Meta Agent rewrites task agent code
    │
    ├── (Every 3 gens) Metacognitive self-modification:
    │   └── Meta agent improves its own improvement strategy
    │
    ├── Evaluate child on training tasks
    │
    └── Add to archive → repeat
```

---

## Emergent Harness Components

The system detects which of these harness components appear in the evolved agent's code:

| Hand-Engineered Component | Emergent Equivalent |
|--------------------------|-------------------|
| `ToolRegistry` | Tool use (calculator, eval) |
| `MemoryManager` | State tracking, result storage |
| `Planner` | Chain-of-thought, multi-step reasoning |
| `Verifier` | Self-verification, answer checking |
| Retry Loop | Retry logic, multiple attempts |
| `ContextEngine` | Prompt engineering, multi-stage pipelines |

---

## Quick Start

```bash
export NVIDIA_API_KEY="your-key"
pip install -r requirements.txt

# CLI
python3 hyperagent.py                # 8 iterations (default)
python3 hyperagent.py --quick        # 4 iterations
python3 hyperagent.py --full         # 15 iterations
python3 hyperagent.py 12             # Custom iteration count

# GUI
python3 app.py

# Docker
docker build -t hyperagent-harness .
docker run -e NVIDIA_API_KEY=$NVIDIA_API_KEY -p 7860:7860 hyperagent-harness
```

---

## CLI Output

```
============================================================
  HYPERAGENT HARNESS — Self-Improving Agent Loop
  Model: Nemotron Super 49B
  Iterations: 8
============================================================

[HYPERAGENT    ] Starting HyperAgent self-improvement loop
[CONFIG        ] Iterations: 8 | Tasks: 12 | Held-out: 6

[GENERATION 0  ] Evaluating initial agent (bare LLM call, no harness)
[SCORE         ] Gen 0: 0.750 (9/12 tasks)

[GENERATION 1  ] ==================================================
[SELECT        ] Selected parent: Gen 0 (score=0.750)
[META          ] Meta agent rewriting task agent code...
[SCORE         ] Gen 1: 0.833 (10/12 tasks)
[IMPROVED      ] Newly solved: math_03, reason_02
[BEST          ] New best: Gen 1 (0.833)

...

[GENERATION 8  ] ==================================================
[SCORE         ] Gen 8: 0.917 (11/12 tasks)

[HELD-OUT      ] Best agent (Gen 6): 0.833 (5/6 tasks)
[HELD-OUT      ] Initial agent (Gen 0): 0.667 (4/6 tasks)
[IMPROVE       ] Held-out improvement: 0.667 → 0.833

[EMERGENCE     ] Detecting emergent harness components in best agent...
[EMERGENCE     ]   ✓ Tool Use (calculator/eval)
[EMERGENCE     ]   ✓ Memory / State Tracking
[EMERGENCE     ]   ✓ Chain-of-Thought / Planning
[EMERGENCE     ]   ✓ Self-Verification
[EMERGENCE     ]   ✓ Retry Logic
[EMERGENCE     ]   ✓ Prompt Engineering
[EMERGENCE     ]   ✓ Multi-stage Pipeline
[EMERGENCE     ]   ✓ Error Handling
```

---

## GUI

Two tabs:

1. **Run Evolution** — configure iterations, run the loop, view execution log, score progression, best agent code, and stats
2. **Emergence Analysis** — run and analyze which harness components the agent evolved on its own, compared with hand-engineered components

---

## The Paper

**HyperAgents** by Jenny Zhang, Bingchen Zhao, Wannan Yang, Jakob Foerster, Jeff Clune, Minqi Jiang, Sam Devlin, and Tatiana Shavrina. Meta / UBC / Vector Institute / Edinburgh / NYU. March 2026.

Key findings:
- Hyperagents outperform baselines across coding, paper review, robotics, and math grading
- Meta-level improvements (memory, tracking, pipelines) transfer across domains
- Self-improvements compound across runs
- Both metacognition and open-ended exploration are necessary for sustained progress

---

## Author

Cobus Greyling
