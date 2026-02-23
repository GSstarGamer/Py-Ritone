# Repository Agent Rules

## Chat Context Maintenance (Required)
For every meaningful task in this repository:
1. Append an entry to `chat-context/UPDATES.md`.
2. Include:
   - date
   - short request summary
   - what changed (files/APIs/behavior)
   - validation commands run
   - notable follow-up note/risk (if any)

## When To Also Update `chat-context/README.md`
Update `chat-context/README.md` if the task changes:
1. architecture or protocol surface,
2. public API shape/usage guidance,
3. key operational workflows (start/stop/debug behavior),
4. important project-orientation context future chats should know first.

## Startup Read Order
1. `chat-context/README.md`
2. `chat-context/UPDATES.md`
3. Then proceed to task-specific files.
