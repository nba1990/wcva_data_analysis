<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

```text
<type>(<scope>): <short summary>

<body>

<footer>
```

### Template

```text
<type>(<scope>): <summary in imperative mood>

Example:
feat(auth): add JWT token validation middleware

<body>
Explain the change in more detail.

Why:
- Why the change was necessary

What:
- What was changed
- Key implementation details

How:
- Important design decisions

<footer>
Closes: <issue-id>
Relates-to: <issue-id>
Breaking-change: <description if applicable>
```

### Common Types

```
feat     → new feature
fix      → bug fix
docs     → documentation
style    → formatting / linting
refactor → code change without behavior change
perf     → performance improvement
test     → adding or fixing tests
build    → build system / dependencies
ci       → CI/CD changes
chore    → maintenance tasks
revert   → revert a previous commit
```

### Example Commit

```
feat(api): add pagination support to user endpoint

Why:
Large user datasets caused slow response times.

What:
- Added page and limit query parameters
- Updated database query logic
- Added validation for pagination input

How:
Used offset-based pagination with indexed queries.

Closes: #42
```

# Pull Request (PR) Description Template

This pairs nicely with structured commits.

```markdown
## Summary

Brief explanation of the change.

Example:
Adds caching layer to reduce database load for user queries.

---

## Changes

- <change 1>
- <change 2>
- <change 3>

---

## Motivation

Why this change was necessary.

Explain the problem that existed before.

---

## Implementation Details

Important implementation notes:

- Algorithms
- Architecture changes
- Dependencies added/removed

---

## Screenshots / Examples (if applicable)

Before:

```

<example>
```

After:

```
<example>
```

---

## Testing

How this change was verified.

* [ ] Unit tests added/updated
* [ ] Integration tests
* [ ] Manual testing

Test steps:

1. <step>
2. <step>
3. <step>

---

## Breaking Changes

Describe any breaking changes.

Migration steps if required.

---

## Related Issues

Closes: #<issue>
Relates to: #<issue>

---

## Checklist

* [ ] Code compiles
* [ ] Tests pass
* [ ] Documentation updated
* [ ] No breaking changes (or documented)

````

```text
# <type>(<scope>): <summary>
#
# Summary should be 50 characters or less
# Use imperative mood (e.g., "add feature" not "added feature")

<type>(<scope>): <summary>

# ------------------------
# Why is this change needed?
#
# -

# ------------------------
# What does this change do?
#
# -

# ------------------------
# Additional notes
#
# -

# ------------------------
# Issue references
#
# Closes:
# Relates to:
````
