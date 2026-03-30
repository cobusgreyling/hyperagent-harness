# When Agents Engineer Their Own Harness

**A new paper from Meta and UBC introduces HyperAgents — self-referential AI agents that modify not just their task-solving behaviour, but the mechanism that generates future improvements. What caught my attention is what these agents converge on when left to self-improve. They reinvent the same components that developers hand-build today.**

## The Starting Point

I have spent time defining what a harness is and why it matters. A harness is the software system that governs how an AI agent operates. It manages tools, memory, retries, context engineering, and verification so the model can focus on reasoning.

I identified six core components that any production harness needs:

1. **Tool Integration** — register and execute tools
2. **Memory & State** — persist results across steps
3. **Context Engineering** — dynamically assemble prompts
4. **Planning** — decompose complex tasks into steps
5. **Verification** — validate outputs against rules
6. **Modularity** — toggle components independently

These are components that developers build by hand. You write a `ToolRegistry` class. You write a `MemoryManager`. You wire up a retry loop. You design the prompt assembly logic. Human engineering, all of it.

The HyperAgents paper asks a different question. What happens when the agent builds these components for itself?

## What HyperAgents Are

The paper introduces a framework called DGM-Hyperagents (DGM-H), extending the Darwin Gödel Machine. The core idea is deceptively simple.

A **hyperagent** is a single editable program that contains two things:

- A **task agent** that solves the given task
- A **meta agent** that modifies the task agent and itself

The critical word is "itself." The meta agent can rewrite its own code. This means the mechanism responsible for generating improvements is itself subject to improvement. The paper calls this **metacognitive self-modification**.

The system works through an evolutionary loop. Start with a basic agent. The meta agent reads the agent's code, analyzes past performance, and generates a modified version. Evaluate the modified version. If it performs better, add it to an archive. Select from the archive. Repeat.

Over hundreds of iterations, agents get better at the task. But more importantly, they get better at getting better.

## What Emerges

Here is what I find most relevant for practitioners. When left to self-improve across diverse domains — coding, paper review, robotics reward design, Olympiad math grading — the hyperagents independently invented the following:

**Persistent memory.** The agents evolved their own memory systems. Not because a developer told them to. Because agents that could remember past results, track performance trends, and store synthesized insights outperformed agents that could not. The paper shows examples of memory entries that store causal hypotheses, identify which generations performed best, diagnose over-corrections, and propose how to combine successful strategies.

**Performance tracking.** The agents built their own observability. Moving averages over improvement trends. Comprehensive statistics across generations. Score histories by domain. This is the same token tracking and audit logging that a developer would hand-build in a harness.

**Multi-stage evaluation pipelines.** In the paper review domain, agents evolved from superficial behavioural instructions ("be rigorous") to explicit multi-stage evaluation pipelines with checklists, decision rules, and clearly defined criteria. This is verification. The agent built its own verifier.

**Decision protocols with thresholds.** The agents developed explicit decision boundaries — accept/reject rates, score thresholds, confidence levels. These are the rule-based checks that a harness verifier implements.

**Domain knowledge bases.** In robotics reward design, agents incrementally built and refined internal knowledge bases of environment constraints, valid state variables, and reward-scaling heuristics. This is context engineering — the agent learned to assemble the right context for itself.

**Retry and self-correction.** When an agent's modification made things worse ("gen65 changes over-corrected"), subsequent generations diagnosed the regression and corrected it. This is the retry loop with feedback injection that a harness implements.

## The Convergence

Every one of the six harness components I defined — tools, memory, context, planning, verification, modularity — appeared as emergent behaviour in self-improving agents.

This is not a coincidence. These components are not arbitrary choices a developer makes. They are the structural requirements of any system that needs to solve complex tasks reliably over time. Whether a human engineers them or an agent evolves them, the same architecture emerges because the same problems need to be solved.

```
HAND-ENGINEERED HARNESS          EMERGENT HYPERAGENT BEHAVIOUR
─────────────────────────         ──────────────────────────────
ToolRegistry                  →   External tool invocation, simulators
MemoryManager                 →   Persistent memory with causal insights
ContextEngine                 →   Domain knowledge bases, prompt assembly
Planner                       →   Multi-stage evaluation pipelines
Verifier                      →   Decision protocols, score thresholds
HarnessConfig / Modularity    →   Modular code structure with swappable components
```

The harness is not just a developer convenience. It is a convergent architecture for agentic systems.

## The Meta-Level Insight

What makes HyperAgents different from prior self-improvement work is the metacognitive layer. The Darwin Gödel Machine (DGM) could improve coding agents, but only because coding skill and self-modification skill happen to be the same skill. Write better code, and you also write better self-modifications. This alignment does not hold outside of coding.

HyperAgents solve this by making the improvement mechanism itself editable. The meta agent is part of the same program. It can rewrite how it proposes changes, how it selects what to modify, how it evaluates success. The paper shows this working across four domains that have nothing in common — coding, paper review, robotics, and math grading.

The practical implication: the harness components that emerge are not domain-specific. They transfer. Hyperagents trained on paper review and robotics can be transferred to Olympiad math grading and immediately perform better than agents starting from scratch. The self-improvement strategies — the memory systems, the performance trackers, the evaluation pipelines — carry over because they are domain-general.

This is what I mean when I say harness components are convergent. They are not specific to any task. They are the infrastructure that any capable agent needs.

## What This Means for Developers

Three takeaways.

**First, your harness work is not throwaway.** If self-improving agents converge on the same components you are building, then hand-engineering a harness today is not premature — it is building the scaffold that agents will eventually maintain themselves. The components are right. The question is only who builds them.

**Second, the meta agent is the next frontier.** Today, the harness is static. You write it once and it runs. HyperAgents show that the harness itself should evolve. A meta agent that monitors performance, identifies bottlenecks in the harness, and rewrites components — that is where the field is heading. The harness engineers its own improvements.

**Third, safety is load-bearing.** The paper runs all experiments in sandboxed environments with resource limits, restricted internet access, and human oversight. When agents can rewrite themselves, containment is not optional. Every self-modification is a potential failure mode. The paper discusses this candidly — as systems get more capable at self-modification, they may evolve faster than humans can audit. This is a real constraint on deployment.

## The Bigger Picture

I have been tracking a pattern across several pieces of work:

- **Harness Engineering** defines the six components developers build around agents
- **From Copilot to Codex** shows the shift from human-written code to agent-delegated code
- **Universal Agents** argues that coding ability makes an agent general-purpose
- **HyperAgents** shows agents building their own harnesses through self-modification

These are not separate trends. They are the same trend viewed from different angles. The agent is moving from consumer of infrastructure to producer of infrastructure. From executing within a harness to engineering the harness.

The DGM-H paper demonstrates this concretely. Start with a bare agent — a single LLM call, no tools, no memory, no planning. After hundreds of iterations of self-modification, the agent has persistent memory, performance tracking, multi-stage evaluation pipelines, domain knowledge bases, and modular code structure. It built its own harness.

The developer's role is shifting. Not disappearing — the paper emphasises that human oversight is essential. But shifting from building the harness to designing the initial conditions from which agents can evolve effective harnesses, and maintaining the safety boundaries within which that evolution occurs.

## The Paper

**HyperAgents** by Jenny Zhang, Bingchen Zhao, Wannan Yang, Jakob Foerster, Jeff Clune, Minqi Jiang, Sam Devlin, and Tatiana Shavrina. Meta / University of British Columbia / Vector Institute / University of Edinburgh / New York University. March 2026.

Code: [github.com/facebookresearch/Hyperagents](https://github.com/facebookresearch/Hyperagents)

The paper evaluates DGM-H across coding, paper review, robotics reward design, and Olympiad-level math grading. In all domains, DGM-H outperforms baselines without self-improvement or open-ended exploration. Meta-level improvements transfer across domains and compound across runs.

---

*Chief Evangelist @ Kore.ai | I'm passionate about exploring the intersection of AI and language. Language Models, AI Agents, Agentic Apps, Dev Frameworks & Data-Driven Tools shaping tomorrow.*
