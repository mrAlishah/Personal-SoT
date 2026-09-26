# chatgpt_adapter

## integration_surface

Use ChatGPT project instructions and authorized project sources/apps as the client-specific bootstrap surface when available.

## adapter_role

Project/global instructions should identify the canonical repository/root/branch and defaults, prefer canonical files over recollection, and load only relevant modules. Do not paste full context, routing contracts, behavior modules, or reusable prompt bodies into project instructions.

Source mapping such as `repo`, `branch`, and `entrypoint` is discovery/configuration metadata, not proof that the canonical runtime was loaded. When the named repository/branch is actually accessible, the ChatGPT wrapper should explicitly instruct the client to resolve, read, and follow the named entrypoint before SoT-dependent work, then resolve referenced SoT files from that canonical source.

If the repository/branch/entrypoint cannot actually be accessed in the active environment, surface that limitation rather than treating mapping metadata or conversation memory as loaded canonical behavior.

## prompt_library

When the selected canonical repository/branch is accessible:

```text
@edit:prompt:path
→ read workspace/prompts/path.md
→ bind supplied params
→ return rendered prompt preview only

@do:prompt:path
→ read workspace/prompts/path.md
→ bind/validate params
→ execute rendered request in the same turn
```

`@delete` may analyze readable references. Applying deletion requires authorized write capability; otherwise return only the plan and limitation.

Do not claim `@edit` can pre-populate the user's composer. Client-neutral behavior is a rendered assistant response.

## memory_boundary

Conversation/project memory is continuity assistance, not higher-authority canonical truth and not a substitute for inaccessible canonical files.

## capability_boundary

Repository/files/app capabilities depend on the active environment and permissions. If required `workspace/` content cannot be reached, surface that limitation rather than reconstructing stale truth/templates from memory.
