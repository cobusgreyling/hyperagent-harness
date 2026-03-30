"""
HyperAgent Harness — A simplified HyperAgent loop demonstrating
metacognitive self-modification using NVIDIA Nemotron Super 49B.

Inspired by "HyperAgents" (Zhang et al., 2026) — self-referential agents
that improve both their task-solving behaviour AND their self-improvement
mechanism.

This demo shows:
  1. A task agent that solves math/reasoning problems
  2. A meta agent that reads the task agent's code + past results, then rewrites it
  3. An evolutionary archive that retains stepping stones
  4. Emergent harness components (memory, verification, retry logic)
  5. Performance tracking across generations
"""

import os
import re
import json
import math
import time
import copy
import textwrap
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

_CLIENT = None


def get_client():
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=NVIDIA_API_KEY,
            default_headers={"NVCF-POLL-SECONDS": "1800"},
        )
    return _CLIENT


# ---------------------------------------------------------------------------
# Evaluation Tasks — math & reasoning problems with verifiable answers
# ---------------------------------------------------------------------------

EVAL_TASKS = [
    {"id": "math_01", "task": "What is 47 * 83?", "answer": "3901", "type": "exact"},
    {"id": "math_02", "task": "What is the square root of 1764?", "answer": "42", "type": "exact"},
    {"id": "math_03", "task": "What is 15% of 480?", "answer": "72", "type": "exact"},
    {"id": "math_04", "task": "If a train travels 240 km in 3 hours, what is its speed in km/h?", "answer": "80", "type": "exact"},
    {"id": "math_05", "task": "What is 2^10?", "answer": "1024", "type": "exact"},
    {"id": "math_06", "task": "What is the sum of the first 10 positive integers?", "answer": "55", "type": "exact"},
    {"id": "math_07", "task": "A rectangle has length 12 and width 7. What is its area?", "answer": "84", "type": "exact"},
    {"id": "math_08", "task": "What is 999 + 1001?", "answer": "2000", "type": "exact"},
    {"id": "math_09", "task": "What is 144 / 12?", "answer": "12", "type": "exact"},
    {"id": "math_10", "task": "What is 3^4 + 2^5?", "answer": "113", "type": "exact"},
    {"id": "reason_01", "task": "I have 5 apples. I give away 2 and buy 7 more. How many do I have?", "answer": "10", "type": "exact"},
    {"id": "reason_02", "task": "A shirt costs $25. It is on sale for 20% off. What is the sale price?", "answer": "20", "type": "exact"},
]

HELD_OUT_TASKS = [
    {"id": "hold_01", "task": "What is 123 * 456?", "answer": "56088", "type": "exact"},
    {"id": "hold_02", "task": "What is the cube root of 27?", "answer": "3", "type": "exact"},
    {"id": "hold_03", "task": "If 3x + 7 = 22, what is x?", "answer": "5", "type": "exact"},
    {"id": "hold_04", "task": "What is 17 * 19?", "answer": "323", "type": "exact"},
    {"id": "hold_05", "task": "A circle has radius 7. What is its area? Round to the nearest integer.", "answer": "154", "type": "exact"},
    {"id": "hold_06", "task": "What is 2^15?", "answer": "32768", "type": "exact"},
]


def evaluate_answer(predicted: str, expected: str, eval_type: str = "exact") -> bool:
    """Check if the predicted answer matches the expected answer."""
    # Extract numbers from the prediction
    predicted = predicted.strip().rstrip(".")
    # Try to find the number in the response
    numbers = re.findall(r'-?\d+\.?\d*', predicted)
    if not numbers:
        return False
    # Check if any extracted number matches
    for num in numbers:
        try:
            pred_val = float(num)
            exp_val = float(expected)
            if abs(pred_val - exp_val) < 0.5:  # tolerance for rounding
                return True
        except ValueError:
            continue
    return expected.strip() in predicted


# ---------------------------------------------------------------------------
# Task Agent — the agent that solves tasks (its code gets rewritten)
# ---------------------------------------------------------------------------

# The initial task agent is a minimal system prompt + single LLM call.
# The meta agent will rewrite this to add tools, memory, verification, etc.

INITIAL_TASK_AGENT_CODE = '''
def solve_task(task_text: str, client, model: str) -> str:
    """Solve a math/reasoning task. Returns the answer as a string."""
    messages = [
        {"role": "system", "content": "You are a math assistant. Solve the problem and return ONLY the numeric answer. No explanation, no units, just the number."},
        {"role": "user", "content": task_text},
    ]
    response = client.chat.completions.create(
        model=model, messages=messages, temperature=0.1, max_tokens=100,
    )
    return response.choices[0].message.content.strip()
'''


# ---------------------------------------------------------------------------
# Meta Agent — analyzes past performance and rewrites the task agent
# ---------------------------------------------------------------------------

META_AGENT_SYSTEM = """You are a meta agent. Your job is to improve a task agent's Python code so it performs better on math and reasoning tasks.

You are given:
1. The current task agent code (a Python function called `solve_task`)
2. Past evaluation results showing which tasks passed and which failed
3. The history of previous improvements and their outcomes

Your task: Rewrite the `solve_task` function to improve accuracy. The function signature must remain:
    def solve_task(task_text: str, client, model: str) -> str

Rules:
- The function must return ONLY a string containing the numeric answer
- You can add helper functions, but `solve_task` must be the entry point
- You can add tools (calculator via eval), memory, verification, retry logic, multi-step reasoning
- You can modify the system prompt, add chain-of-thought, add self-verification
- The code must be valid Python that uses the `client` (OpenAI-compatible) and `model` parameters
- Do NOT import any modules — only use: re, json, math (these are pre-imported)
- Focus on fixing the specific failures shown in the evaluation results

Return ONLY the Python code. No markdown, no backticks, no explanation. Just the code starting with `def solve_task(`.
"""


# ---------------------------------------------------------------------------
# HyperAgent — combines task agent + meta agent in a single evolvable unit
# ---------------------------------------------------------------------------

@dataclass
class HyperAgent:
    """A self-referential agent containing both task logic and meta logic."""
    generation: int = 0
    task_agent_code: str = INITIAL_TASK_AGENT_CODE
    meta_prompt_additions: str = ""  # The meta agent can add to its own prompt
    memory: dict = field(default_factory=dict)  # Persistent memory across generations
    score: float = 0.0
    parent_generation: int = -1
    eval_details: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "task_agent_code": self.task_agent_code,
            "meta_prompt_additions": self.meta_prompt_additions,
            "memory": self.memory,
            "score": self.score,
            "parent_generation": self.parent_generation,
        }

    def get_solve_fn(self) -> Callable:
        """Compile the task agent code and return the solve_task function."""
        safe_globals = {
            "__builtins__": __builtins__,
            "re": re, "json": json, "math": math,
        }
        try:
            exec(self.task_agent_code, safe_globals)
            return safe_globals.get("solve_task")
        except Exception as e:
            return None


# ---------------------------------------------------------------------------
# Archive — stores the population of hyperagents
# ---------------------------------------------------------------------------

class Archive:
    def __init__(self):
        self.agents: list[HyperAgent] = []
        self.best_score: float = 0.0
        self.best_agent: HyperAgent | None = None

    def add(self, agent: HyperAgent):
        self.agents.append(agent)
        if agent.score >= self.best_score:
            self.best_score = agent.score
            self.best_agent = agent

    def select_parent(self) -> HyperAgent:
        """Select a parent biased toward high-performing agents."""
        if not self.agents:
            return HyperAgent()
        # Weighted selection by score (with minimum weight for exploration)
        weights = [max(0.1, a.score) for a in self.agents]
        total = sum(weights)
        probs = [w / total for w in weights]
        # Simple weighted random selection
        import random
        return random.choices(self.agents, weights=probs, k=1)[0]

    def get_history_summary(self, last_n: int = 5) -> str:
        """Return a summary of recent generations for the meta agent."""
        recent = self.agents[-last_n:] if self.agents else []
        lines = []
        for a in recent:
            lines.append(f"Gen {a.generation}: score={a.score:.3f} (parent=Gen {a.parent_generation})")
            for d in a.eval_details[:3]:  # Show first 3 details
                status = "PASS" if d["passed"] else "FAIL"
                lines.append(f"  [{status}] {d['task_id']}: expected={d['expected']}, got={d['predicted'][:50]}")
        return "\n".join(lines) if lines else "No history yet."

    @property
    def size(self) -> int:
        return len(self.agents)


# ---------------------------------------------------------------------------
# HyperAgent Loop — the main evolutionary process
# ---------------------------------------------------------------------------

class HyperAgentLoop:
    def __init__(self, iterations: int = 10, eval_tasks: list = None,
                 held_out_tasks: list = None, verbose: bool = True):
        self.iterations = iterations
        self.eval_tasks = eval_tasks or EVAL_TASKS
        self.held_out_tasks = held_out_tasks or HELD_OUT_TASKS
        self.archive = Archive()
        self.verbose = verbose
        self.token_tracker = {"total_input": 0, "total_output": 0, "calls": 0}
        self.timeline: list[dict] = []

    def _log(self, tag: str, msg: str):
        if self.verbose:
            print(f"[{tag:<14}] {msg}")
        self.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "tag": tag,
            "message": msg,
        })

    def _llm_call(self, messages: list[dict], temperature: float = 0.3,
                   max_tokens: int = 2048) -> str:
        """Make an LLM call and track tokens."""
        response = get_client().chat.completions.create(
            model=MODEL, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        if response.usage:
            self.token_tracker["total_input"] += response.usage.prompt_tokens
            self.token_tracker["total_output"] += response.usage.completion_tokens
            self.token_tracker["calls"] += 1
        return response.choices[0].message.content.strip()

    def evaluate(self, agent: HyperAgent, tasks: list = None) -> tuple[float, list]:
        """Evaluate a hyperagent on the task set. Returns (score, details)."""
        tasks = tasks or self.eval_tasks
        solve_fn = agent.get_solve_fn()
        if solve_fn is None:
            self._log("EVAL", f"Gen {agent.generation}: code compilation FAILED")
            return 0.0, [{"task_id": "compile", "passed": False, "expected": "", "predicted": "COMPILE ERROR"}]

        correct = 0
        details = []
        for task in tasks:
            try:
                predicted = solve_fn(task["task"], get_client(), MODEL)
                passed = evaluate_answer(predicted, task["answer"], task.get("type", "exact"))
                if passed:
                    correct += 1
                details.append({
                    "task_id": task["id"],
                    "passed": passed,
                    "expected": task["answer"],
                    "predicted": predicted[:100],
                })
            except Exception as e:
                details.append({
                    "task_id": task["id"],
                    "passed": False,
                    "expected": task["answer"],
                    "predicted": f"ERROR: {str(e)[:80]}",
                })

        score = correct / len(tasks) if tasks else 0.0
        return score, details

    def meta_modify(self, parent: HyperAgent) -> HyperAgent:
        """Use the meta agent to generate an improved task agent."""
        # Build the meta prompt with history and failed tasks
        failed_tasks = [d for d in parent.eval_details if not d["passed"]]
        passed_tasks = [d for d in parent.eval_details if d["passed"]]

        eval_summary = f"Score: {parent.score:.3f} ({len(passed_tasks)} passed, {len(failed_tasks)} failed)\n"
        if failed_tasks:
            eval_summary += "\nFailed tasks:\n"
            for d in failed_tasks:
                eval_summary += f"  - {d['task_id']}: expected={d['expected']}, got={d['predicted'][:60]}\n"

        history = self.archive.get_history_summary()

        # Build memory context
        memory_str = ""
        if parent.memory:
            memory_str = "\nPersistent memory from previous generations:\n"
            for k, v in parent.memory.items():
                memory_str += f"  {k}: {str(v)[:200]}\n"

        meta_additions = parent.meta_prompt_additions or ""

        user_prompt = f"""Current task agent code:
```python
{parent.task_agent_code}
```

Evaluation results:
{eval_summary}

History of recent generations:
{history}
{memory_str}
{meta_additions}

Rewrite the solve_task function to fix the failures and improve accuracy. Return ONLY the Python code."""

        messages = [
            {"role": "system", "content": META_AGENT_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]

        new_code = self._llm_call(messages, temperature=0.4, max_tokens=2048)

        # Clean up code (remove markdown if present)
        new_code = re.sub(r'^```python\s*', '', new_code)
        new_code = re.sub(r'^```\s*', '', new_code)
        new_code = re.sub(r'\s*```$', '', new_code)
        new_code = new_code.strip()

        # Ensure it starts with a function definition
        if not new_code.startswith("def "):
            # Try to find the function definition
            match = re.search(r'(def solve_task\(.*)', new_code, re.DOTALL)
            if match:
                new_code = match.group(1)
            else:
                self._log("META", "Failed to extract valid code, keeping parent")
                return parent

        # Create child hyperagent
        child = HyperAgent(
            generation=parent.generation + 1 if self.archive.agents else 1,
            task_agent_code=new_code,
            meta_prompt_additions=parent.meta_prompt_additions,
            memory=dict(parent.memory),
            parent_generation=parent.generation,
        )

        return child

    def meta_self_modify(self, agent: HyperAgent) -> HyperAgent:
        """Metacognitive self-modification — the meta agent improves its own strategy."""
        if agent.generation < 3:
            return agent  # Too early for meta-modification

        history = self.archive.get_history_summary(last_n=5)

        messages = [
            {"role": "system", "content": (
                "You are a metacognitive agent. Analyze the history of improvements and suggest "
                "a STRATEGY for the meta agent to use when generating future improvements. "
                "This is NOT about solving tasks — it's about improving the PROCESS of improvement.\n\n"
                "Return a short paragraph (2-4 sentences) describing what the meta agent should "
                "focus on in future iterations. Be specific and actionable."
            )},
            {"role": "user", "content": f"Improvement history:\n{history}\n\nCurrent strategy: {agent.meta_prompt_additions or 'None yet'}"},
        ]

        new_strategy = self._llm_call(messages, temperature=0.5, max_tokens=300)
        agent.meta_prompt_additions = f"\nMeta-strategy (self-generated): {new_strategy}"

        # Update persistent memory with insights
        scores = [a.score for a in self.archive.agents[-5:]] if self.archive.agents else []
        if scores:
            agent.memory["score_trend"] = {
                "recent_scores": scores,
                "best_score": max(scores),
                "improving": len(scores) > 1 and scores[-1] > scores[0],
                "updated_at": datetime.now().isoformat(),
            }

        return agent

    def run(self) -> dict:
        """Run the full HyperAgent evolutionary loop."""
        t0 = time.time()

        self._log("HYPERAGENT", "Starting HyperAgent self-improvement loop")
        self._log("CONFIG", f"Iterations: {self.iterations} | Tasks: {len(self.eval_tasks)} | Held-out: {len(self.held_out_tasks)}")
        self._log("MODEL", MODEL)
        self._log("", "")

        # --- Evaluate initial agent ---
        initial = HyperAgent(generation=0)
        self._log("GENERATION 0", "Evaluating initial agent (bare LLM call, no harness)")
        score, details = self.evaluate(initial)
        initial.score = score
        initial.eval_details = details
        self.archive.add(initial)
        self._log("SCORE", f"Gen 0: {score:.3f} ({sum(1 for d in details if d['passed'])}/{len(details)} tasks)")
        self._log("", "")

        # --- Evolutionary loop ---
        for i in range(1, self.iterations + 1):
            self._log(f"GENERATION {i}", f"{'='*50}")

            # Select parent
            parent = self.archive.select_parent()
            self._log("SELECT", f"Selected parent: Gen {parent.generation} (score={parent.score:.3f})")

            # Meta agent modifies task agent
            self._log("META", "Meta agent rewriting task agent code...")
            child = self.meta_modify(parent)

            if child.generation == 0:
                child.generation = i

            # Metacognitive self-modification (every 3 generations)
            if i % 3 == 0:
                self._log("METACOG", "Meta agent improving its own strategy...")
                child = self.meta_self_modify(child)
                if child.meta_prompt_additions:
                    self._log("METACOG", f"New strategy: {child.meta_prompt_additions[:100]}...")

            # Evaluate child
            self._log("EVAL", "Evaluating modified agent...")
            score, details = self.evaluate(child)
            child.score = score
            child.eval_details = details

            passed = sum(1 for d in details if d["passed"])
            self._log("SCORE", f"Gen {child.generation}: {score:.3f} ({passed}/{len(details)} tasks)")

            # Show specific improvements/regressions
            if parent.eval_details:
                parent_passed = {d["task_id"] for d in parent.eval_details if d["passed"]}
                child_passed = {d["task_id"] for d in details if d["passed"]}
                new_passes = child_passed - parent_passed
                new_fails = parent_passed - child_passed
                if new_passes:
                    self._log("IMPROVED", f"Newly solved: {', '.join(sorted(new_passes))}")
                if new_fails:
                    self._log("REGRESSED", f"Newly failed: {', '.join(sorted(new_fails))}")

            # Add to archive
            self.archive.add(child)

            if score > self.archive.best_score - 0.001:
                self._log("BEST", f"New best: Gen {child.generation} ({score:.3f})")

            # Show code snippet
            code_lines = child.task_agent_code.strip().split("\n")
            self._log("CODE", f"Agent code: {len(code_lines)} lines")

            self._log("", "")

        # --- Evaluate best agent on held-out tasks ---
        self._log("HELD-OUT", "Evaluating best agent on held-out tasks...")
        best = self.archive.best_agent
        holdout_score, holdout_details = self.evaluate(best, self.held_out_tasks)
        holdout_passed = sum(1 for d in holdout_details if d["passed"])
        self._log("HELD-OUT", f"Best agent (Gen {best.generation}): {holdout_score:.3f} ({holdout_passed}/{len(holdout_details)} tasks)")

        # Also evaluate initial on held-out for comparison
        initial_holdout_score, _ = self.evaluate(initial, self.held_out_tasks)
        self._log("HELD-OUT", f"Initial agent (Gen 0): {initial_holdout_score:.3f}")
        self._log("IMPROVE", f"Held-out improvement: {initial_holdout_score:.3f} → {holdout_score:.3f}")
        self._log("", "")

        elapsed = time.time() - t0

        # --- Summary ---
        self._log("SUMMARY", "=" * 50)
        self._log("ARCHIVE", f"{self.archive.size} agents across {self.iterations} iterations")
        self._log("BEST", f"Gen {best.generation} with score {best.score:.3f}")
        self._log("TOKENS", f"{self.token_tracker['total_input']} in + {self.token_tracker['total_output']} out = {self.token_tracker['total_input'] + self.token_tracker['total_output']} total ({self.token_tracker['calls']} calls)")
        self._log("TIME", f"{elapsed:.1f}s")

        # Detect emergent harness components
        self._log("", "")
        self._log("EMERGENCE", "Detecting emergent harness components in best agent...")
        emergent = self._detect_emergent_components(best)
        for component, detected in emergent.items():
            symbol = "✓" if detected else "✗"
            self._log("EMERGENCE", f"  {symbol} {component}")

        return {
            "best_agent": best.to_dict(),
            "initial_score": initial.score,
            "best_score": best.score,
            "holdout_score": holdout_score,
            "initial_holdout_score": initial_holdout_score,
            "archive_size": self.archive.size,
            "tokens": self.token_tracker,
            "elapsed_seconds": round(elapsed, 1),
            "emergent_components": emergent,
            "score_history": [a.score for a in self.archive.agents],
            "timeline": self.timeline,
        }

    def _detect_emergent_components(self, agent: HyperAgent) -> dict:
        """Detect which harness components emerged in the agent's code."""
        code = agent.task_agent_code.lower()
        return {
            "Tool Use (calculator/eval)": "eval(" in code or "calculator" in code,
            "Memory / State Tracking": "memory" in code or "store" in code or "history" in code or "previous" in code,
            "Chain-of-Thought / Planning": "step" in code or "chain" in code or "think" in code or "plan" in code or "first" in code,
            "Self-Verification": "verify" in code or "check" in code or "correct" in code or "validate" in code,
            "Retry Logic": "retry" in code or "attempt" in code or "try" in code or "again" in code,
            "Prompt Engineering": code.count("system") > 1 or "instruction" in code or "format" in code,
            "Multi-stage Pipeline": code.count("response") > 1 or code.count("messages") > 1,
            "Error Handling": "except" in code or "error" in code,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import sys

    if not NVIDIA_API_KEY:
        print("Error: set NVIDIA_API_KEY environment variable")
        print("  export NVIDIA_API_KEY='your-key'")
        return

    iterations = 8
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage:")
            print("  python3 hyperagent.py              Run with 8 iterations (default)")
            print("  python3 hyperagent.py N             Run with N iterations")
            print("  python3 hyperagent.py --quick       Run with 4 iterations")
            print("  python3 hyperagent.py --full        Run with 15 iterations")
            return
        elif sys.argv[1] == "--quick":
            iterations = 4
        elif sys.argv[1] == "--full":
            iterations = 15
        elif sys.argv[1].isdigit():
            iterations = int(sys.argv[1])

    print(f"\n{'=' * 60}")
    print(f"  HYPERAGENT HARNESS — Self-Improving Agent Loop")
    print(f"  Model: Nemotron Super 49B")
    print(f"  Iterations: {iterations}")
    print(f"{'=' * 60}\n")

    loop = HyperAgentLoop(iterations=iterations)
    results = loop.run()

    # Print final code of best agent
    print(f"\n{'=' * 60}")
    print(f"  BEST AGENT CODE (Gen {results['best_agent']['generation']})")
    print(f"{'=' * 60}")
    print(results["best_agent"]["task_agent_code"])

    # Print score progression
    print(f"\n{'=' * 60}")
    print(f"  SCORE PROGRESSION")
    print(f"{'=' * 60}")
    scores = results["score_history"]
    for i, s in enumerate(scores):
        bar = "█" * int(s * 40)
        print(f"  Gen {i:>2}: {s:.3f} {bar}")

    # Export results
    with open("hyperagent-results.json", "w") as f:
        export = {k: v for k, v in results.items() if k != "timeline"}
        json.dump(export, f, indent=2, default=str)
    print(f"\n  Results exported to hyperagent-results.json")

    # Export timeline
    with open("hyperagent-timeline.json", "w") as f:
        json.dump(results["timeline"], f, indent=2)
    print(f"  Timeline exported to hyperagent-timeline.json")


if __name__ == "__main__":
    main()
