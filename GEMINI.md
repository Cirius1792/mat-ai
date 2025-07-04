# Gemini Project Guide: MAT.AI

This guide provides essential information for working on the MAT.AI project.

## 🚨 MANDATORY WORKFLOW - NO EXCEPTIONS 🚨

**CRITICAL**: After EVERY single code change, you MUST run both test and quality scripts. This is NON-NEGOTIABLE.

### Required Commands After Every Change

1.  **Run tests**:
    ```bash
    uv run pytest
    ```
2.  **Run quality checks (linter)**:
    ```bash
    uv run pyright
    ```

**Failure Protocol**: If any command fails, STOP, FIX the issue, and RE-RUN both commands until they pass before proceeding.

## Project Overview

MAT.AI is an AI-powered mail activity tracker. It reads and analyzes emails to extract tasks and action items, integrating with Trello to help users manage their deadlines.

- **Core Functionality**: Parse emails, identify tasks, and store them.
- **Integrations**: Outlook (O365), Trello, SQLite.
- **Primary Interface**: A command-line interface (CLI).

## Key Technical Constraints & Best Practices

- **Language**: Use vanilla Python where possible.
- **Paradigm**: Object-Oriented Programming (OOP), Inversion of Control (IoC).
- **Typing**: Mandatory type hints for all method signatures.
- **Methodology**: Strict Test-Driven Development (TDD).
- **Code Style**: Follow SOLID principles, write clean, readable code.

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

