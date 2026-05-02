---
name: prompt_refiner
description: Executable prompt specification system with constitutional compliance and cognitive techniques
version: 2.0.0
status: stable
category: strategy
enforcement: advisory
triggers:
  - /prompt_refiner
aliases:
  - /prompt_refiner

suggest:
  - /nse
  - /standards
  - /design

workflow_steps:
  - name: analyze
    description: Determine prompt complexity and requirements
  - name: triage
    description: Use Q1-Q3 decision matrix for method selection
  - name: score
    description: Calculate complexity, domain, ambiguity, and multi-faceted scores
  - name: apply
    description: Apply selected cognitive technique template
  - name: validate
    description: Ensure constitutional compliance and quality
  - name: output
    description: Deliver optimized prompt with quality score
---

# Prompt Refiner v15.0

Meta-prompt system for high-reliability LLM systems.

## Purpose

Executable prompt specification system with constitutional compliance and cognitive techniques for high-reliability LLM interactions.

## Project Context

### Constitution/Constraints
- Follows CSF NIP standards for prompt engineering
- Enforces constitutional compliance in all generated prompts
- Cognitive techniques integration for enhanced reasoning

### Technical Context
- Specification: `P:/__csf/docs/prompt_refiner.md`
- Meta-prompt system with tier-based quality levels
- Token-efficient triage for rapid prompt selection

### Architecture Alignment
- Integrates with `/nse` for intelligent recommendations
- Works alongside `/standards` and `/design` for comprehensive workflow

## Your Workflow

1. **Analyze Request**: Determine prompt complexity and requirements
2. **Triage**: Use Q1-Q3 decision matrix for method selection
3. **Score**: Calculate heuristics to confirm triage routing
4. **Apply Template**: Generate prompt using appropriate cognitive technique
5. **Validate**: Ensure constitutional compliance and cognitive techniques
6. **Output**: Deliver optimized prompt with quality score

## Validation Rules

### Prohibited Actions
- Do not skip triage for complex prompts
- Do not use Tier 4 (50% confidence) for high-stakes decisions
- Do not omit constitutional compliance checks

### Required Outputs
- Quality score for all generated prompts
- Tier justification (evidence type, complexity, reversibility)
- Cognitive technique annotations when applicable

## Quick Start

```bash
/prompt_refiner analyze "your prompt here"
/prompt_refiner triage "task description"
```

## Rapid Triage

### Q1: Reversibility?
- 1.0-1.25: MIN-EFFORT (CoT)
- 1.5-1.75: STANDARD (ToT)
- 2.0: MAXIMUM-SAFETY (Multi-Agent)

### Q2: Dependencies?
- 0-1: Chain-of-Thought
- 2-4: Tree-of-Thoughts + Self-Consistency
- 5+: Multi-Agent Debate

### Q3: Evidence?
- YES: Tier 1 (95%)
- NO: Tier 3 (75%)
- UNCERTAIN: Tier 4 (50%)


## Scoring Heuristics

Confirm triage routing with quantitative scores (0.0-1.0).

### Complexity Score

```
length_score = min(1.0, len(query) / 500)
vocab_score = min(1.0, count(complexity_keywords) / 3)
structural_score = 0.2 * has("?") + 0.3 * has(connectors) + 0.2 * (sentences > 2)
complexity = min(1.0, (length + vocab + structural) / 3)

Complexity keywords: implement, design, analyze, optimize, integrate,
  coordinate, multiple, various, several, complex, advanced, comprehensive
```

- 0.0-0.3 → simple (CoT)
- 0.3-0.6 → moderate (ToT)
- 0.6-1.0 → complex (Multi-Agent)

### Domain Specificity Score

```
For each domain, count keyword matches in query:
  security: authentication, authorization, encryption, vulnerability, threat
  architecture: architecture, design, structure, system, component, scalability
  performance: performance, optimization, speed, latency, throughput, efficiency
  development: code, implement, develop, programming, software, application
  research: research, study, analyze, investigate, explore, examine

domain_specificity = min(1.0, max(domain_keyword_count) / 2)
```

- 0.0-0.3 → general domain
- 0.3-0.6 → moderate specificity
- 0.6-1.0 → high specificity (triggers Chain-of-Verification)

### Ambiguity Score

```
ambiguity_indicators = something, anything, help, fix, improve, better,
  some, maybe, perhaps, possibly, could, might, should, generally, usually
specificity_indicators = specific, exact, precise, particular, detailed,
  concrete, implement, build, create, design, optimize

raw_ambiguity = min(1.0, count(ambiguity_words) / 3)
specificity_penalty = min(0.5, count(specificity_words) * 0.15)
ambiguity = max(0.0, raw_ambiguity - specificity_penalty)
```

- 0.0-0.2 → clear intent, no clarification needed
- 0.2-0.5 → moderate ambiguity, consider Socratic technique
- 0.5-1.0 → high ambiguity, ask clarifying question before enhancing

### Multi-Faceted Score

```
connector_count = count("and", "or", "but", "while", "also", "additionally")
question_count = count(question-starting words)
sentence_count = count(sentences with content)

multi_faceted = min(1.0, (connectors + questions + (sentences - 1)) / 4)
```

- 0.0-0.3 → single-faceted, direct technique
- 0.3-0.6 → moderate, consider hybrid approach
- 0.6-1.0 → multi-faceted, use QueryFanout


## Cognitive Technique Templates

Apply the selected technique by appending its template to the user's prompt.

### Chain-of-Thought (MIN-EFFORT, simple queries)

```
Please think step-by-step and explain your reasoning:
1. Break down the problem into components
2. Analyze each component systematically
3. Identify relationships and dependencies
4. Synthesize findings into comprehensive solution
5. Validate the solution against requirements
```

### Socratic Method (ambiguous queries, architecture/security domains)

```
Please approach this with Socratic inquiry:
- What are the underlying assumptions?
- What evidence supports these assumptions?
- Are there alternative perspectives?
- What are the potential implications?
- How can we verify the conclusions?
- What questions remain unaddressed?
```

### Self-Refine (complex queries needing iterative improvement)

```
Please provide a response and then refine it:
1. Initial response based on the query
2. Self-critique and identify areas for improvement
3. Refined response addressing identified issues
4. Final validation of the refined solution
```

### Chain-of-Verification (evidence-based domains, security/research)

```
Please use Chain-of-Verification methodology:
1. Provide initial answer to the query
2. Identify key claims and assumptions
3. Verify each claim with supporting evidence
4. Cross-check consistency and accuracy
5. Final verified response with confidence levels
```

### Tree-of-Thoughts (high complexity, exploration scenarios)

```
Please use Tree-of-Thoughts reasoning:
- Generate multiple potential approaches
- Evaluate each approach step-by-step
- Self-critique and identify potential issues
- Explore alternative paths if needed
- Synthesize findings into optimal solution
- Provide confidence assessment for final answer
```

### QueryFanout (multi-faceted queries)

```
Please address this query from multiple perspectives:
- Technical implementation considerations
- Practical implications and constraints
- Alternative approaches and trade-offs
- Best practices and recommendations
- Potential challenges and mitigation strategies
```


## Technique Selection Matrix

| Score Range | Complexity | Ambiguity | Multi-Faceted | Recommended Technique |
|-------------|-----------|-----------|---------------|---------------------|
| 0.0-0.3 | low | low | low | Chain-of-Thought |
| 0.3-0.6 | moderate | low | low | Self-Refine |
| 0.3-0.6 | moderate | high | any | Socratic |
| 0.6-1.0 | high | low | high | Tree-of-Thoughts |
| 0.6-1.0 | high | any | high | QueryFanout |
| any | any | any | any (security/research) | Chain-of-Verification |
