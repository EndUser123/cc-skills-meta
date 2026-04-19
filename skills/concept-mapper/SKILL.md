---
name: concept-mapper
description: Unified concept mapping for learning, system architecture, and text analysis. Creates Mermaid diagrams for mind maps, concept maps, system diagrams, and knowledge structures. Use for studying, documentation, architecture visualization, or converting articles/text into visual maps.
version: 1.0.0
status: stable
compatibility: Requires Mermaid renderer (GitHub, Obsidian, VS Code, or online viewers)
metadata:
  category: visualization
  output-format: mermaid
  supports: mindmap concept-map flowchart architecture
---

# Concept Mapper

Unified skill for creating concept maps and mind maps across three primary use cases:

1. **Learning & Study**: Create memory-effective mind maps for studying and note-taking
2. **System Architecture**: Map component relationships, dependencies, and system structure
3. **Text Analysis**: Convert articles, docs, or text into visual concept maps

## When to Use This Skill

Activate this skill when the user:
- Asks to create a "mind map," "concept map," or "knowledge map"
- Wants to visualize relationships between concepts, components, or ideas
- Needs to study or organize complex information
- Wants to understand system architecture or component relationships
- Asks to convert an article, document, or text into a diagram
- Mentions "map out," "visualize," or "diagram" concepts or systems

## Core Principles

### 1. Structure by Purpose
Different goals require different map structures:

**For Learning/Study:**
- Use hierarchical mind maps (center → branches → leaves)
- Apply GRINDE principles: Group, Related, Interconnected, Nested, Deep, Elaborated
- Focus on relationships and memory encoding
- Use color coding and visual grouping
- Include examples and counter-examples

**For System Architecture:**
- Use layered architecture diagrams or component maps
- Show dependencies (arrows), data flow, and interaction patterns
- Group related components (subsystems, layers, modules)
- Label relationships (HTTP, events, streams, etc.)
- Include external boundaries and interfaces

**For Text/Article Analysis:**
- Extract key concepts first (nouns, entities, themes)
- Map relationships (causes, effects, examples, categories)
- Preserve the author's structure but make it visual
- Highlight evidence, claims, and supporting points
- Show hierarchy (main argument → supporting points → evidence)

### 2. Mermaid Syntax Best Practices

See `references/syntax-guide.md` for diagram type conventions (mind map, concept map, architecture).

### 3. Universal Workflow

**Step 1: Identify Purpose**
Ask: "What is the main goal? Study, document architecture, or analyze text?"
- Study → Use mind map structure with memory techniques
- Architecture → Use component diagram with layers and dependencies
- Text analysis → Extract concepts and relationships first

**Step 2: Gather Content**
- For study: List topics, subtopics, examples
- For architecture: List components, their relationships, interfaces
- For text: Read and extract key concepts, claims, evidence

**Step 3: Structure the Map**
- Start with central concept or top-level component
- Add primary branches or adjacent components
- Fill in secondary levels (sub-concepts, sub-components)
- Add cross-links and relationships

**Step 4: Apply Best Practices**
- Use consistent spacing and indentation
- Label relationships clearly
- Group related items visually
- Add icons sparingly for emphasis
- Keep branches balanced (3-7 items per level)

**Step 5: Output and Verify**
- Generate Mermaid code
- Preview in supported renderer
- Check for clarity and completeness
- Adjust if needed

## Examples & Templates

See `references/examples.md` for complete Mermaid examples (learning mind maps, system architecture, text analysis).
See `references/templates.md` for ready-to-use templates (GRINDE study map, three-tier architecture, argument analysis) and advanced techniques.

## Output Guidelines

1. **Always provide Mermaid code** - it's portable and widely supported
2. **Include a brief explanation** of the map structure and how to read it
3. **Suggest a viewer** if needed (GitHub, Mermaid Live Editor, Obsidian, VS Code)
4. **Offer to iterate** - "Want me to adjust the structure, add more detail, or focus on a specific area?"
5. **For complex maps**: Offer to break into multiple linked diagrams

## Integration with Other Skills

This skill works well with:
- **mermaid-diagrams**: For advanced Mermaid syntax and diagram types
- **mapping-visualization-scaffolds**: For complex system architecture
- **grinde-mapper**: For advanced study techniques and memory optimization

When those skills are available, this skill provides a unified entry point, then delegates to specialized skills for advanced use cases.
