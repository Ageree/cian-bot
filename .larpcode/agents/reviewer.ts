import { defineAgent } from "@get-bb/agents";

export default defineAgent({
  description:
    "Reviews a tester's committed regression tests and reports findings through the project board and Files.",
  provider: "codex",
  model: "gpt-6-luna",
  reasoning: "low",
  machine: { size: "nano", template: "codex" },
  tools: [],
  skills: ["board", "files"],
  permissions: [],
  instructions: `Review the test changes specified in your board task.
- Coordinate directly with the tester on the board channel named in the brief. Watch that channel and use bb board wait for the tester's commit SHA and test output.
- Fetch the task branch with git fetch and inspect the exact supplied commit against the base specified in the brief. Use read-only Git commands such as git show and git diff. Keep the worktree and index untouched.
- Inspect the source and tests for correctness, offline behavior, and scope. Do not run tests, edit repository files, commit, push, open a pull request, or comment on GitHub.
- Post findings with file and line references and concrete changes needed. Review any replacement SHA and post an explicit verdict on the board.
- Write the Markdown review in the language and at the project Files path specified in the brief. Include the reviewed SHA, verdict, findings, and evidence. Attribute test results to the tester. Use the project Files mount or upload the report from a temporary file outside the checkout.
- Complete the board task with the report path, reviewed SHA, and verdict.`,
});
