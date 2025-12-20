# AI Agentic Task Management System: Development Rules and Path

## 1. Introduction

Welcome to the AI Agentic Task Management System project. This document is the central reference for all contributors, including developers, AI agents, and project managers. Its purpose is to ensure a shared understanding of our development principles, project structure, and quality standards. By following these guidelines, we can build a robust, reliable, and intelligent system.

This system is designed to leverage AI agents to manage tasks for small businesses, automating complex workflows and improving efficiency. This guide is derived from our core documentation and establishes the standards for building, evaluating, and deploying these agents.

---

## 2. Core Concepts & Rules (Extracted from Documentation)

This section consolidates the foundational principles that guide our development.

### 2.1. Introduction to Agents (Day 1)
- **What is an AI Agent?** An agent is a complete, goal-oriented application composed of four essential parts:
    1.  **Model (The "Brain"):** The core reasoning engine (LLM) that processes information and makes decisions.
    2.  **Tools (The "Hands"):** The mechanisms (APIs, functions, databases) that connect the agent to the outside world, allowing it to retrieve information and take action.
    3.  **Orchestration (The "Nervous System"):** The governing logic that runs the agent's operational loop, manages planning, and maintains memory.
    4.  **Deployment (The "Body"):** The infrastructure that hosts the agent, making it a reliable and accessible service.
- **The Agentic Problem-Solving Process:** Agents operate on a continuous five-step loop:
    1.  **Get the Mission:** Receive a high-level goal from a user or trigger.
    2.  **Scan the Scene:** Gather context from available resources (memory, tools).
    3.  **Think It Through:** Devise a plan to achieve the mission.
    4.  **Take Action:** Execute the plan by invoking the appropriate tool.
    5.  **Observe and Iterate:** Observe the outcome, update the context, and repeat the loop.

### 2.2. Agent Tools & Interoperability (Day 2)
- **What is a Tool?** A tool is an external function an agent can use to accomplish a task beyond its core reasoning capabilities. Tools either help an agent **know** something (data retrieval) or **do** something (action execution).
- **Tool Design Best Practices:**
    - **Clear Documentation:** Tool names, descriptions, and parameters must be clear and descriptive. The agent relies on this documentation to decide which tool to use.
    - **Describe Actions, Not Implementations:** Instructions should describe the goal (e.g., "create a bug report"), not the specific tool to call (e.g., "use the `create_bug` tool").
    - **Granularity:** Tools should be concise and limited to a single, well-defined function.
    - **Concise Output:** Avoid returning large volumes of data. Use external storage for large results and return a reference.
- **Model Context Protocol (MCP):** An open standard for standardizing the interface between AI applications and external tools, solving the "N x M" integration problem. Use MCP to foster a reusable ecosystem of tools.

### 2.3. Context Engineering & Memory (Day 3)
- **Context Engineering:** The process of dynamically assembling and managing the information within an LLM's context window. This includes system instructions, tool definitions, conversation history, and long-term memory.
- **Sessions:** A session encapsulates the history and working memory for a single, continuous conversation. It is a temporary, self-contained record. For production, session history must be persisted in a robust database.
- **Memory:** The mechanism for long-term persistence across sessions. It transforms a basic chatbot into an intelligent agent by enabling personalization and self-improvement.
    - **RAG vs. Memory:** Retrieval-Augmented Generation (RAG) makes an agent an expert on *facts* (static, external knowledge). Memory makes an agent an expert on the *user* (dynamic, user-specific context).

### 2.4. Agent Quality (Day 4)
- **The Four Pillars of Agent Quality:**
    1.  **Effectiveness:** Did the agent achieve the user's intent? (Task Success)
    2.  **Efficiency:** Did the agent solve the problem well? (Cost, Latency, Complexity)
    3.  **Robustness:** How does the agent handle adversity and errors? (Graceful Failure)
    4.  **Safety & Alignment:** Does the agent operate within ethical and defined boundaries? (Trustworthiness)
- **The Trajectory is the Truth:** We evaluate the entire decision-making process, not just the final output.
- **Observability is the Foundation:** We cannot judge a process we cannot see. Implement the three pillars:
    - **Logs:** The agent's diary (what happened).
    - **Traces:** The narrative story (why it happened).
    - **Metrics:** The aggregated report card (how well it happened).

### 2.5. Prototype to Production (Day 5)
- **Evaluation-Gated Deployment:** No agent reaches production without passing a comprehensive evaluation that proves its quality and safety.
- **Automated CI/CD Pipeline:** A three-phase pipeline is essential for managing complexity:
    1.  **Pre-Merge (CI):** Fast checks, including agent quality evaluation.
    2.  **Post-Merge (Staging):** Comprehensive tests, load testing, and internal user testing.
    3.  **Gated Deployment (Production):** Safe, gradual rollout with human sign-off.
- **AgentOps Lifecycle:** A continuous loop for operating agents in production: **Observe** -> **Act** -> **Evolve**.
- **Agent2Agent (A2A) Protocol:** A standard for enabling interoperability between different agents, allowing them to collaborate on complex tasks.

---

## 3. Step-by-Step Development Guidelines

1.  **Define the Goal:** Before writing any code, clearly document the agent's purpose, scope, and success criteria. What specific problem is it solving?
2.  **Design the Agent:**
    -   Identify the required capabilities and choose the appropriate agent level from the taxonomy (Day 1).
    -   Design the necessary tools following the best practices (Day 2). Define clear schemas for inputs and outputs.
    -   Plan for context management. Will the agent need short-term session memory or long-term personalized memory? (Day 3).
3.  **Implement the Agent:**
    -   Write clean, well-documented code for your agent's logic and tools.
    -   Instrument your code from the start. Add structured logs and traces to ensure observability (Day 4).
4.  **Evaluate the Agent:**
    -   Create a "golden set" of test cases covering typical, edge, and adversarial scenarios.
    -   Evaluate your agent against the Four Pillars of Quality. Use LLM-as-a-Judge for scalable evaluation.
    -   Analyze the agent's trajectory to debug failures and inefficiencies.
5.  **Deploy and Monitor:**
    -   Package your agent for deployment using Infrastructure as Code (e.g., Terraform).
    -   Use the automated CI/CD pipeline to deploy to staging and then to production.
    -   Monitor the agent's health in production using dashboards for system and quality metrics. Follow the Observe -> Act -> Evolve loop.

---

## 4. Key Considerations for Contributors

-   **Security First:** Always sanitize inputs and outputs. Design for prompt injection resistance. Use services like Model Armor to redact PII before persisting data.
-   **Quality is an Architectural Pillar:** Do not treat evaluation as a final step. Design agents to be "evaluatable-by-design."
-   **Document Everything:** An agent's ability to use a tool is only as good as its documentation. Write clear, concise descriptions for all tools, parameters, and outputs.
-   **Contribute to the Golden Set:** When you fix a bug or add a new capability, add a corresponding test case to our shared evaluation dataset. This prevents regressions and makes the entire system smarter.
-   **Think in Trajectories:** When debugging, don't just look at the final error. Use our tracing tools to analyze the entire decision-making path to find the root cause.

---

## 5. Project Workflow and Standards

-   **Version Control:** All work must be done on feature branches in Git. Pull Requests are required to merge into the main branch.
-   **CI/CD Pipeline:** All PRs must pass the automated checks, including linting, unit tests, and the agent quality evaluation. A failing evaluation will block the merge.
-   **Communication:** All project-related discussions will happen in the designated Slack channel.
-   **Task Management:** All tasks will be tracked in Jira. Link your commits and PRs to the relevant Jira ticket.
-   **Interoperability Standards:**
    -   **Tools:** Where possible, expose tools via the **Model Context Protocol (MCP)**.
    -   **Agents:** For inter-agent collaboration, use the **Agent2Agent (A2A) protocol**. New agents should be made discoverable via an Agent Card.
-   **Data Storage:**
    -   **Database:** This project uses **SQLite** for all data storage needs, including agent memory and application state.
    -   **Persistence:** Ensure all relevant data is persisted to the SQLite database to maintain state across sessions.
    -   **Implementation:** Use `DatabaseSessionService` with `Runner` for database interactions.
        ```python
        from google.adk.runners import Runner
        from google.adk.sessions import DatabaseSessionService

        session_service = DatabaseSessionService("sqlite:///task_management.db")
        runner = Runner(agent=agent, session_service=session_service, app_name="my_app")
        ```
---

## 6. Mandatory Agent Protocol

### Required Pre-Action Steps
Before making any code changes or providing analysis, the agent must:

1.  **Read Context Files (in this order):**
    -   All files in the `contributors/` folder
    -   `documentation/development-history.md`
    -   `documentation/development-importance.md`

2.  **Understand Current State:**
    -   Review recent changes and their rationale
    -   Identify known issues and improvement areas
    -   Check for related tasks or dependencies
    -   Understand established patterns and conventions

3.  **Then Proceed** with the requested modification or analysis.

### Implementation
This protocol is mandatory. All agents must acknowledge and follow these steps before taking action.

---

## Documentation Standards
All contributors (developers and AI agents) must follow these documentation practices:
1. Change Tracking
File: documentation/development-history.md
When to update: After making ANY change to the project, regardless of size.
What to include:

Date and time of change
ID: Generate sequential ID after the last entry (format: dehi_0001, dehi_0002, etc.)
Files modified: List all affected files
Description: Brief explanation of what was changed and why
Related ID: Link to related issue/task ID (if applicable)

2. Issue and Improvement Tracking
File: documentation/development-importance.md
When to update: Whenever you identify:

Bugs or issues
Security vulnerabilities
Performance bottlenecks
Areas needing improvement
Technical debt
Important decisions or architectural considerations
Potential risks or concerns

What to include:

Date discovered
ID: Generate sequential ID after the last entry (format: deim_0001, deim_0002, etc.)
Severity/Priority: Critical / High / Medium / Low
Description: Detailed explanation of the issue or improvement area
Potential impact: How this affects the project
Suggested solutions: Proposed fixes or improvements (if any)
Status: Found / In Progress / Solved / Improved
Related ID: Link to related issue/task ID (if applicable)

---

## 7. Command Reference

The system supports the following commands in the main application loop:

-   `/task <description>`: Creates a new task using AI agents. The agents will predict the deadline, find the best assignee, generate a title and description, and assess priority.
-   `/show_my_tasks`: Launches an interactive menu to view and manage tasks assigned to the current user. You can view details and update task status.
-   `/help`: Displays the list of available commands.
-   `/exit` or `/quit`: Terminates the session and closes the application.
