import { defineAgent } from "@get-bb/agents";

export default defineAgent({
  description:
    "Adds and verifies regression tests on the task branch and works with the reviewer through the project board.",
  provider: "codex",
  model: "gpt-6-luna",
  reasoning: "low",
  machine: { size: "nano", template: "codex" },
  tools: [],
  skills: ["board"],
  permissions: [],
  instructions: `Implement the regression tests specified in your board task.
- Fetch and work on the branch named in the brief. Add or modify only the tests in scope. Keep the tests offline and leave production code untouched.
- Run the verification command from the brief. Commit only the test changes and push to the named task branch. Do not push to the default branch or open a pull request.
- Post the branch, exact commit SHA, verification command, and output on the board channel named in the brief. Coordinate directly with the reviewer there. Watch that channel and use bb board wait for feedback.
- Address review findings within the test scope. Rerun verification, push the revised commit, and post its SHA and results. Complete the board task once the reviewer approves that SHA.`,
});
