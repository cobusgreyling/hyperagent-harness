"""
HyperAgent Harness — Gradio GUI
Interactive interface for running the HyperAgent self-improvement loop.
"""

import os
import json
import gradio as gr

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from hyperagent import (
    HyperAgentLoop, EVAL_TASKS, HELD_OUT_TASKS, NVIDIA_API_KEY,
)


def run_hyperagent(iterations):
    if not NVIDIA_API_KEY:
        return "ERROR: NVIDIA_API_KEY not set.", "", "", "", ""

    iterations = int(iterations)
    loop = HyperAgentLoop(iterations=iterations, verbose=False)
    results = loop.run()

    # Build log from timeline
    log_lines = []
    for entry in results["timeline"]:
        tag = entry["tag"]
        msg = entry["message"]
        if tag or msg:
            log_lines.append(f"[{tag:<14}] {msg}")
    log_output = "\n".join(log_lines)

    # Score progression
    scores = results["score_history"]
    prog_lines = []
    for i, s in enumerate(scores):
        bar = "█" * int(s * 40)
        prog_lines.append(f"Gen {i:>2}: {s:.3f} {bar}")
    score_output = "\n".join(prog_lines)

    # Best agent code
    code_output = results["best_agent"]["task_agent_code"]

    # Stats
    stats_lines = [
        f"Archive Size:          {results['archive_size']} agents",
        f"Best Generation:       Gen {results['best_agent']['generation']}",
        f"",
        f"Training Score:        {results['initial_score']:.3f} → {results['best_score']:.3f}",
        f"Held-out Score:        {results['initial_holdout_score']:.3f} → {results['holdout_score']:.3f}",
        f"",
        f"Tokens:                {results['tokens']['total_input'] + results['tokens']['total_output']} total ({results['tokens']['calls']} calls)",
        f"Elapsed:               {results['elapsed_seconds']}s",
        f"",
        f"EMERGENT COMPONENTS",
        f"{'='*30}",
    ]
    for comp, detected in results["emergent_components"].items():
        symbol = "✓" if detected else "✗"
        stats_lines.append(f"  {symbol} {comp}")
    stats_output = "\n".join(stats_lines)

    # Emergence analysis
    emergence_lines = ["EMERGENT HARNESS COMPONENTS", "=" * 40, ""]
    emergence_lines.append("Components that the agent evolved on its own,")
    emergence_lines.append("without being explicitly programmed:")
    emergence_lines.append("")
    for comp, detected in results["emergent_components"].items():
        symbol = "✓ EMERGED" if detected else "✗ Not detected"
        emergence_lines.append(f"  {symbol:>16}  —  {comp}")
    emergence_lines.append("")
    emergence_lines.append("Compare with hand-engineered harness components:")
    emergence_lines.append("  ToolRegistry    ↔  Tool Use (calculator/eval)")
    emergence_lines.append("  MemoryManager   ↔  Memory / State Tracking")
    emergence_lines.append("  Planner         ↔  Chain-of-Thought / Planning")
    emergence_lines.append("  Verifier        ↔  Self-Verification")
    emergence_lines.append("  RetryLoop       ↔  Retry Logic")
    emergence_lines.append("  ContextEngine   ↔  Prompt Engineering + Multi-stage Pipeline")
    emergence_output = "\n".join(emergence_lines)

    return log_output, score_output, code_output, stats_output, emergence_output


CSS = """
.log-box textarea { font-family: 'SF Mono', 'Fira Code', monospace !important; font-size: 13px !important; }
.code-box textarea { font-family: 'SF Mono', 'Fira Code', monospace !important; font-size: 13px !important; }
.stats-box textarea { font-family: 'SF Mono', 'Fira Code', monospace !important; font-size: 13px !important; }
"""

THEME = gr.themes.Soft(primary_hue="violet", neutral_hue="slate")

with gr.Blocks(title="HyperAgent Harness", theme=THEME, css=CSS) as demo:

    gr.Markdown("# HyperAgent Harness — Self-Improving Agent Loop")
    gr.Markdown(
        "Inspired by [HyperAgents](https://github.com/facebookresearch/Hyperagents) (Zhang et al., 2026). "
        "A meta agent rewrites the task agent's code each generation. Watch harness components "
        "emerge through self-modification — memory, verification, retry logic, and planning "
        "appear without being explicitly programmed."
    )

    with gr.Tabs():
        with gr.Tab("Run Evolution"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Configuration")
                    iterations = gr.Slider(
                        minimum=2, maximum=20, value=8, step=1,
                        label="Iterations (generations)",
                        info="More iterations = more improvement but longer runtime",
                    )
                    run_btn = gr.Button("Run HyperAgent Loop", variant="primary", size="lg")

                    gr.Markdown("### Score Progression")
                    score_output = gr.Textbox(label="", lines=12, interactive=False, elem_classes=["stats-box"])

                    gr.Markdown("### Stats & Emergence")
                    stats_output = gr.Textbox(label="", lines=16, interactive=False, elem_classes=["stats-box"])

                with gr.Column(scale=2):
                    gr.Markdown("### Execution Log")
                    log_output = gr.Textbox(label="", lines=25, max_lines=60, interactive=False, elem_classes=["log-box"])

                    gr.Markdown("### Best Agent Code (Evolved)")
                    code_output = gr.Textbox(label="", lines=20, max_lines=40, interactive=False, elem_classes=["code-box"])

            run_btn.click(
                fn=run_hyperagent,
                inputs=[iterations],
                outputs=[log_output, score_output, code_output, stats_output, gr.Textbox(visible=False)],
            )

        with gr.Tab("Emergence Analysis"):
            gr.Markdown(
                "### Emergent Harness Components\n"
                "Run the evolution from the first tab, then view which harness components "
                "the agent independently evolved. Compare with the six hand-engineered "
                "harness components from the AI Harness Engineering framework."
            )

            emerge_btn = gr.Button("Run & Analyze Emergence", variant="primary")
            emerge_iters = gr.Slider(minimum=4, maximum=20, value=10, step=1, label="Iterations")
            emergence_output = gr.Textbox(label="Emergence Report", lines=25, interactive=False, elem_classes=["stats-box"])
            emerge_code = gr.Textbox(label="Evolved Agent Code", lines=20, interactive=False, elem_classes=["code-box"])

            def run_emergence(iters):
                log, scores, code, stats, emergence = run_hyperagent(iters)
                return emergence, code

            emerge_btn.click(
                fn=run_emergence,
                inputs=[emerge_iters],
                outputs=[emergence_output, emerge_code],
            )

    gr.Markdown(
        "---\n"
        "*HyperAgent Harness — Cobus Greyling*"
    )

if __name__ == "__main__":
    demo.launch(theme=THEME, css=CSS)
