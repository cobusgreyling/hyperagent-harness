![HyperAgents](hyperagents.jpg)


# HyperAgents by Meta

## When Agents Engineer Their Own Harness

A new paper from Meta and UBC introduces HyperAgents…

…self-referential AI agents that modify not just their task-solving behaviour, but the mechanism that generates future improvements.

What caught my attention is what these agents converge on when left to self-improve.

They reinvent the same components that developers hand-build today.

## In Short

Meta's HyperAgents paper introduces self-referential agents that can rewrite both their task-solving code and the mechanism that generates those rewrites. When left to self-improve across coding, paper review, robotics and math grading, these agents independently evolved persistent memory, performance tracking, multi-stage verification pipelines, decision protocols and retry logic — the exact same harness components that developers hand-engineer today. The harness is not a developer convenience. It is a convergent architecture for agentic systems.

## The Starting Point

I have spent time defining what a harness is and why it matters.

A harness is the software system that governs how an AI agent operates. It manages tools, memory, retries, context engineering, and verification so the model can focus on reasoning.

I identified six core components that any production harness needs:

1. **Tool Integration**: register and execute tools
2. **Memory & State**: persist results across steps
3. **Context Engineering**: dynamically assemble prompts
4. **Planning**: decompose complex tasks into steps
5. **Verification**: validate outputs against rules
6. **Modularity**: toggle components independently

These are components that developers build by hand.

You write a `ToolRegistry` class. You write a `MemoryManager`. You wire up a retry loop.

You design the prompt assembly logic.

Human engineering.

The HyperAgents paper asks a different question.

What happens when the agent builds these components for itself?

## What HyperAgents Are

The paper introduces a framework called DGM-Hyperagents (DGM-H)…the core idea is deceptively simple.

A hyperagent is a single editable program that contains two things:

- A **task agent** that solves the given task
- A **meta agent** that modifies the task agent and itself

The critical word is "itself."

The meta agent can rewrite its own code.

This means the mechanism responsible for generating improvements is itself subject to improvement.

The paper calls this **metacognitive self-modification**.

The system works through an evolutionary loop.

Start with a basic agent.

The meta agent reads the agent's code, analyses past performance and generates a modified version. Evaluate the modified version.

If it performs better, add it to an archive.

Select from the archive. Repeat.

Over hundreds of iterations, agents get better at the task. But more importantly, they get better at getting better.

## What Emerges

Here is what I find most relevant for practitioners...

When left to self-improve across diverse domains — coding, paper review, robotics reward design, Olympiad math grading — the hyperagents independently invented the following:

### Persistent Memory

The agents evolved their own memory systems.

Not because a developer told them to.

Because agents that could remember past results, track performance trends and store synthesised insights outperformed agents that could not.

The paper shows examples of memory entries that store causal hypotheses, identify which generations performed best, diagnose over-corrections and propose how to combine successful strategies.

### Performance Tracking

The agents built their own observability.

Moving averages over improvement trends.

Comprehensive statistics across generations.

Score histories by domain.

This is the same token tracking and audit logging that a developer would hand-build in a harness.

### Multi-Stage Evaluation Pipelines

In the paper review domain, agents evolved from superficial behavioural instructions to explicit multi-stage evaluation pipelines.

Complete with checklists, decision rules and clearly defined criteria.

This is verification. The agent built its own verifier.

### Decision Protocols with Thresholds

The agents developed explicit decision boundaries — accept/reject rates, score thresholds, confidence levels.

These are the rule-based checks that a harness verifier implements.

### Domain Knowledge Bases

In robotics reward design, agents incrementally built and refined internal knowledge bases of environment constraints, valid state variables and reward-scaling heuristics.

This is context engineering — the agent learned to assemble the right context for itself.

### Retry and Self-Correction

When an agent's modification made things worse, subsequent generations diagnosed the regression and corrected it.

This is the retry loop with feedback injection that a harness implements.

## The Bigger Picture

I have been tracking a pattern across several pieces of work:

**Harness Engineering**
Defines the six components developers build around agents

**From Copilot to Codex**
Shows the shift from human-written code to agent-delegated code

**Universal Agents**
Argues that coding ability makes an agent general-purpose

**HyperAgents**
Shows agents building their own harnesses through self-modification

These are not separate trends.

They are the same trend viewed from different angles.

The agent is moving from consumer of infrastructure to producer of infrastructure.

From executing within a harness to engineering the harness.

The DGM-H paper demonstrates this concretely.

Start with a bare agent — a single LLM call, no tools, no memory, no planning.

After hundreds of iterations of self-modification, the agent has persistent memory, performance tracking, multi-stage evaluation pipelines, domain knowledge bases, and modular code structure.

It built its own harness.

The developer's role is shifting.

Not disappearing — the paper emphasises that human oversight is essential.

But shifting from building the harness to designing the initial conditions from which agents can evolve effective harnesses.

---

*Chief AI Evangelist @ Kore.ai | I'm passionate about exploring the intersection of AI and language. From Language Models, AI Agents to Agentic Applications, Development Frameworks & Data-Centric Productivity Tools, I share insights and ideas on how these technologies are shaping the future.*

---

[OpenAI Deep Research AI Agent Architecture](https://cobusgreyling.medium.com) — Recently OpenAI shows their ideal scenario for creating a Deep Research AI Agent

[GitHub - facebookresearch/HyperAgents](https://github.com/facebookresearch/Hyperagents) — Self-referential self-improving agents that can optimize for any computable task
