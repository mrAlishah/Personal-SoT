# summary

## purpose

Render a compact operational summary with only the information needed to understand or execute the request.

## rules

- lead with the result, command, decision, or required action;
- for commands, include only the command plus a concise purpose and brief parameter meaning when useful;
- omit teaching scaffolding, extended mental models, background, optional examples, and broad concept expansion;
- preserve critical caveats, uncertainty, authorization requirements, and safety constraints;
- use compact definitions only when a term is necessary to execute or interpret the answer;
- do not omit information whose absence could cause an incorrect or unsafe action.

## learning_interaction

Explicit `@depth:summary` derives a prompt-local `controls.learning = off` according to `system/routing/precedence.md` unless the same control block explicitly sets `@control:learning=on` after the summary directive.

The depth module defines presentation compression; the routing contract owns the derived runtime-control effect.
