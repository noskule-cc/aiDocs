# [Platform] Architecture Rules

Enforceable design principles. Read before writing new code (`AGENTS.md` routes here).


## Layer Boundaries

<!-- Define your dependency direction. Example: -->
```
UI → Presentation → Domain ← Data
```

| Rule | Allowed | Forbidden |
|------|---------|-----------|
| Domain imports | Domain, Core | Data, UI, Presentation |
| Data imports | Data, Domain, Core | UI, Presentation |
| Presentation imports | Presentation, Domain, Core | Data, UI |
| UI imports | All layers | — |
| Core imports | Core only | All other layers |


## Design Principles

<!-- List your architectural patterns. Examples: -->
<!-- - Strategy pattern for pluggable implementations -->
<!-- - Slot-based composition for extensible types -->
<!-- - Repository pattern for data access -->


## Reuse Rules

Before implementing new logic, check this table. If what you need exists, use it.

### Calculators

| Need | Use | Location |
|------|-----|----------|
| <!-- e.g. "HR zone calculation" --> | <!-- e.g. "HrZonesCalculator.calculateZone()" --> | <!-- e.g. "domain/util/" --> |

### Formatters

| Need | Use | Location |
|------|-----|----------|
| | | |

### Parsers

| Need | Use | Location |
|------|-----|----------|
| | | |

### Constants

| Need | Use | Location |
|------|-----|----------|
| | | |


## Extension Points

<!-- Document how to add new types without modifying existing code. Example: -->
<!-- | Adding a new... | Mechanism | Steps | -->
<!-- |-----------------|-----------|-------| -->
<!-- | Training type | Add enum + slot config | 1. Add to TrainingType enum 2. Add SlotConfig entry | -->


## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Hard-code values | Use constants class | Single source of truth |
| Duplicate calculations | Use existing calculator | Consistency, maintainability |
| Import across layers | Follow layer boundaries | Dependency direction |
| Create God classes | Split by responsibility | Testability, readability |


## Known Violations

<!-- Track existing violations to fix later, not to replicate. -->
| File | Violation | Status |
|------|-----------|--------|
| | | |


**Last Updated:** YYYY-MM-DD
