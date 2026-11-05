# Issue Tracker

Project management using GitHub Issues and Projects v2.

## Conventions

Types, labels, and project fields are discoverable via the GitHub API. These rules aren't:

1. **Use issue types** for classification — not labels
2. **Use labels** for the feature area the issue touches
3. **Label the feature, not the data.** Most issues need one label
4. **Use the sub-issue feature** to link children to epics
5. **Add every issue to the project**
6. **Set sprint status** to Backlog unless otherwise stated
7. **Always estimate** — Fibonacci (1, 2, 3, 5, 8, 13)
8. **Title format** — imperative verb + concise description
9. **Update wiki** when closing issues that add significant functionality
10. **Epic estimate** — sum of its sub-issue estimates
11. **Sign as an agent** — if you are an AI agent, put your signature on the **first line** of every issue body, issue or PR comment and PR body you draft: `` — 🤖 <model name> (`<model ID>`) ``, with your actual model name and exact model ID. The posting account no longer tells who wrote it; humans never sign

### Estimate Scale

| Points  | Complexity                                         |
|---------|----------------------------------------------------|
| 1       | Trivial — config change, copy fix                  |
| 2       | Small — single file, data already available        |
| 3       | Medium — new component, aggregation logic          |
| 5       | Large — DB migration, new data capture, multi-file |
| 8       | XL — architectural change, cross-cutting concern   |
| 13      | XXL — epic-scale, should probably be split          |
