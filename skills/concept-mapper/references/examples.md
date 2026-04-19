# Concept Mapper - Examples

Complete Mermaid examples for each use case.

## Example 1: Learning Mind Map (Study)

**User Request:** "Create a mind map for learning about microservices"

```mermaid
mindmap
    root((Microservices))
      Definition
        Small, independent services
        Each owns its data
        Communicates via APIs
      Advantages
        Scalability
        Independent deployment
        Technology diversity
      Challenges
        Network complexity
        Data consistency
        Service discovery
      Patterns
        API Gateway
        Service Mesh
        Event-driven
      Best_Practices
        Domain-driven design
        Containerization
        Observability
```

## Example 2: System Architecture Map

**User Request:** "Map out a web application architecture"

```mermaid
graph TB
    subgraph Client[Client Layer]
        Web[Web App]
        Mobile[Mobile App]
    end

    subgraph Gateway[API Gateway]
        Auth[Authentication]
        Rate[Rate Limiting]
        Route[Routing]
    end

    subgraph Services[Service Layer]
        User[User Service]
        Order[Order Service]
        Payment[Payment Service]
    end

    subgraph Data[Data Layer]
        UserDB[(User DB)]
        OrderDB[(Order DB)]
        Cache[(Redis Cache)]
    end

    Web -->|HTTPS| Gateway
    Mobile -->|HTTPS| Gateway
    Gateway -->|REST| User
    Gateway -->|REST| Order
    Gateway -->|REST| Payment
    User -->|SQL| UserDB
    Order -->|SQL| OrderDB
    User -.->|Cache| Cache
    Order -.->|Events| Payment
```

## Example 3: Text to Concept Map

**User Request:** "Convert this article about climate change into a concept map"

**First: Extract Key Concepts**
- Climate Change (central)
- Greenhouse Effect (mechanism)
- Fossil Fuels (cause)
- Renewable Energy (solution)
- Impacts (consequences)
- Mitigation (actions)

```mermaid
graph LR
    CC(Climate Change)
    GH[Greenhouse Effect]
    FF[Fossil Fuels]
    RE[Renewable Energy]
    IMP[Impacts]
    MIT[Mitigation]

    FF -->|Causes| GH
    GH -->|Leads to| CC
    CC -->|Results in| IMP
    RE -->|Reduces| CC
    MIT -->|Strategies for| CC

    IMP --> Temperature
    IMP --> Weather
    IMP --> Sea_Level

    MIT --> Policy
    MIT --> Technology
    MIT --> Adaptation
```
