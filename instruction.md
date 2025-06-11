# Project Scope

Build a python application that reads and analyse emails to help the user keep track of its tasks.
When an email contains an explicit request to perform a task, it will be extracted and stored on a kanban board, like trello. 


## 🚨 MANDATORY WORKFLOW - NO EXCEPTIONS 🚨

**CRITICAL**: After EVERY single code change, you MUST run both test and quality scripts. This is NON-NEGOTIABLE.

### Required Commands After Every Change

```bash
# 1. ALWAYS run tests first - NO EXCEPTIONS
uv run pytest 

# 2. ALWAYS run quality checks - NO EXCEPTIONS
uv run pyright
```

### Workflow Enforcement Rules

1. **NEVER proceed to the next task** until both `uv run pytest` and `uv run pyright` pass
2. **NEVER skip this workflow** - even for "small changes" or "quick fixes"
3. **ALWAYS run the full test suite** - no selective testing
4. **ALWAYS verify quality standards** - no exceptions for any file type

### Quality Gates - ALL Must Pass

- ✅ **All tests pass**: `uv run pytest` returns success
- ✅ **No linting errors**: linter finds no issues
- ✅ **Proper formatting**: Prettier formatting is applied
- ✅ **No console warnings**: All console usage is intentional
- ✅ **Functional patterns**: Code follows functional programming constraints

### Failure Response Protocol

If ANY quality gate fails:

1. **STOP** all other work immediately
2. **FIX** the failing quality check first
3. **RE-RUN** both test and quality scripts
4. **ONLY THEN** proceed with next task

## Development Approach

## Project Overview
Take a look at the pyproject.toml for the description of the application and the dependency used. 


## Core Requirements

### Authentication

### Web Scraping


### Content Processing


### File Management


## Technical Constraints

### Code Style Requirements

- **MANDATORY**: Use vanilla python as much as possible and suggest for new dependency only if extremely necessaire
- **MANDATORY**: Implement object oriented programming patterns throughout
- **MANDATORY**: Use Inversion of Control pattern as much as possible
- **MANDATORY**: Use type hints for every method signature
- No duplicate imports

### Architecture

Modular design with separate files for different concerns:

- `src/auth.js` - Google OAuth handling
- `src/scraper.js` - Medium content extraction
- `src/converter.js` - HTML to markdown conversion
- `src/storage.js` - File system operations
- `src/config.js` - Configuration management
- `src/logger.js` - Logging utilities
- `src/main.js` - Application orchestration

Use dependency injection patterns and implement proper error handling.


### CLI Interface

 1 matai-cli (defined in src/cli/cli.py)
   – authenticate
   Launches the O365 OAuth flow (opens consent URL, waits for token).
   – run
   Fetches new emails, parses them via the LLM, stores results, and (optionally) pushes tasks to your Trello
   board.
   – run-history [--num N]
   Shows the last N runs (timestamps, status, summary reports).
   – list-emails
   Lists all stored emails (IDs, subjects, senders, dates) in the SQLite DB.
   – show-email
   Prints the full details (cleaned body, raw body, recipients, etc.) of the email with the given ID.
   – list-action-items
   Lists all action items extracted so far (ID, type, description, due date, owners, confidence).
   – config [--verify PATH]
   Loads your YAML config, validates its schema (or other rules), and prints errors or success.
 2 mat-dat (the benchmark CLI in src/matai/benchmark/cli.py)
   – show [--dataset-path PATH]
   Opens your JSONL “gold-standard” dataset in a pager, showing each email and its expected action items.
   – add [--dataset-path PATH]
   Walks you through interactively entering a new email + one or more expected action items, then appends them to
   the JSONL dataset.


# Development Best Practices and Guidelines

_A fusion of Kent Beck's pragmatism with Uncle Bob's discipline._

**CRITICAL**: Follow TDD methodology strictly:

## 1. Embrace Simplicity and Incremental Design
- Keep designs as simple as possible—no more, no less.
- YAGNI (You Aren't Gonna Need It): avoid building features before they are required.
- Refactor continuously: evolve the codebase in small, safe steps.
- Favor straightforward solutions; complexity is the enemy of agility.

## 2. Test-Driven Development (TDD)
- **Red**: write a failing test that specifies the desired behavior.
- **Green**: implement the minimal code to make the test pass.
- **Refactor**: clean up code and tests without altering behavior.
- Ensure tests are fast, isolated, and deterministic.
- Use tests as executable documentation and a safety net for refactoring.

## 3. Write Clean, Readable Code
- Use meaningful, intention-revealing names for variables, functions, and classes.
- Keep functions small and focused: one level of abstraction per function.
- Favor composition over inheritance to reduce coupling.
- Avoid deep nesting; extract helper functions or objects.
- Comments should explain *why*, not *what*; strive for self-documenting code.

## 4. SOLID Principles
- **Single Responsibility Principle**: a class/module should have one reason to change.
- **Open/Closed Principle**: open for extension, closed for modification.
- **Liskov Substitution Principle**: derived types must substitute their base types without altering program correctness.
- **Interface Segregation Principle**: prefer many client-specific interfaces over one general-purpose interface.
- **Dependency Inversion Principle**: depend on abstractions, not on concretions.

## 5. Refactoring and Code Smells
- Regularly eliminate duplication and excessive coupling.
- Watch for code smells: long methods, large classes, feature envy, shotgun surgery.
- Apply automated refactorings where possible (rename, extract, move).
- The Boy Scout Rule: always leave the code cleaner than you found it.

## 6. Architectural Boundaries
- Organize code into layers (e.g., UI, domain, infrastructure) with clear dependencies.
- Domain/business logic must not depend on UI or external frameworks.
- Use boundary interfaces or anti-corruption layers when integrating legacy or third-party systems.
- Keep high-level policies decoupled from low-level details.

## 7. Collaborative Practices
- **Collective Code Ownership**: anyone can and should improve any part of the codebase.
- **Pair Programming**: real-time collaboration to share knowledge and catch issues early.
- **Code Reviews**: aim for constructive, design-focused feedback; prioritize readability and tests.
- Foster a culture of respect, trust, and shared responsibility.

## 8. Continuous Integration & Deployment
- Commit and integrate changes frequently (at least daily) to avoid merge hell.
- Automate builds, tests, and packaging in a CI pipeline.
- Ensure fast feedback: broken builds/tests must be fixed immediately.
- Automate deployments with clear rollback strategies.

## 9. Automation, Tooling, and Metrics
- Use linters, formatters, and static analysis to maintain consistency.
- Track code coverage but don’t chase 100%—focus on meaningful tests.
- Monitor performance, errors, and system health in production.
- Automate repetitive tasks to reduce human error and increase throughput.

## 10. Continuous Learning and Improvement
- Hold regular retrospectives to inspect and adapt your process.
- Encourage knowledge sharing: brown-bag sessions, internal wikis, mentoring.
- Experiment with new approaches incrementally; validate with real feedback.

