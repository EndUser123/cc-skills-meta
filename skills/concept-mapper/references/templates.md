# Concept Mapper - Templates & Advanced Techniques

Ready-to-use Mermaid templates and advanced techniques for complex maps.

## Templates

### GRINDE Study Map Template

For learning/study maps using the GRINDE framework (Group, Related, Interconnected, Nested, Deep, Elaborated).

```mermaid
mindmap
    root((Topic))
      Group1[Related Concepts]
        Interconnected
        Nested_Details
        Deep_Understanding
        Elaborated_Examples
```

### Three-Tier Architecture Template

For system architecture diagrams showing presentation, application, and data layers.

```mermaid
graph TB
    subgraph Presentation
        UI1
        UI2
    end
    subgraph Application
        Service1
        Service2
    end
    subgraph Data
        DB1
        DB2
    end
    Presentation -->|API| Application
    Application -->|SQL| Data
```

### Argument Analysis Template

For converting text/articles into argument structure maps.

```mermaid
graph LR
    Claim[Main Claim]
    Premise1[Premise]
    Premise2[Premise]
    Evidence1[Supporting Evidence]
    Evidence2[Counter-Evidence]
    Conclusion[Conclusion]

    Premise1 --> Claim
    Premise2 --> Claim
    Evidence1 --> Premise1
    Evidence2 -.->|Weakens| Claim
    Claim --> Conclusion
```

## Advanced Techniques

### For Complex Systems
- Use nested subgraphs for layers
- Add legends or keys
- Use different arrow styles for different relationship types
- Color-code by subsystem or concern

### For Learning/Studying
- Add memory hooks (mnemonics, analogies)
- Include "don't confuse with" branches
- Add practice questions or self-tests
- Link to related topics

### For Text Analysis
- Distinguish between claims and evidence
- Show argument structure (premise -> conclusion)
- Highlight controversial points
- Include citations or references
