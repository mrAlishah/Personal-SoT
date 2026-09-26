# v1_1_prompt_flow

## edit_trace

Input:

```text
@ctx:personal/projects/job_search
@edit:prompt:job_search/analyze_job
@param:role=[Senior Go Backend Engineer]
@param:company=[Example GmbH]
@param:job_description=[[
Go backend role using PostgreSQL and Kafka.
]]
```

Expected:

```text
parse edit action
→ resolve exact job_search/analyze_job
→ prompt_status = active
→ bind role/company/job_description
→ resolve prompt defaults
→ preserve explicit ctx in rendered preview
→ render complete prompt
→ STOP
```

No job analysis occurs in this turn.

## do_trace

Input:

```text
@ctx:personal/projects/job_search
@do:prompt:job_search/analyze_job
@param:role=[Senior Go Backend Engineer]
@param:company=[Example GmbH]
@param:job_description=[[
Go backend role using PostgreSQL and Kafka.
]]
```

Expected:

```text
parse do action
→ resolve exact template
→ validate active status + params
→ resolve explicit context independently
→ resolve prompt-local profile/presentation defaults
→ load only relevant authorized job-search/personal atoms
→ apply hard policies/access/authority
→ execute rendered request
```

Prompt template remains a task recipe, not factual authority.

## body_input_trace

```text
@do:prompt:language/translate_professional
@param:target_language=[german]

من هنوز آن را شروع نکرده‌ام.
```

Expected:

```text
target_language = german
input = invocation body
```

Then execute translated request with vocab suffix from prompt defaults.

## delimiter_trace

```text
@edit:prompt:research/compare_tools
@param:items=[[
[
  "A",
  "B"
]
]]
```

Expected: the standalone `]` closing the inner array is parameter content; only standalone `]]` closes multiline binding.

## deletion_trace

First:

```text
@delete:prompt:coding/review_pr
```

Expected:

```text
resolve current prompt
→ identify owned_assets
→ search inbound exact references
→ list shared coding/md/concept references as preserved
→ return deletion plan
→ no write
```

Then after review:

```text
@confirm:delete:prompt:coding/review_pr
```

Expected:

```text
re-fetch prompt/version + inbound refs
→ if unchanged and write-authorized:
   delete prompt + owned assets
   repair inbound refs
   validate
   commit coherently
→ else abort/re-plan
```

## token_trace

Retrieve only:

```text
selected prompt
+
referenced effective profile/presentation modules
+
minimum authoritative context required by final task
```

Do not retrieve all `workspace/prompts/`, all examples, unrelated projects, or unrelated sensitive atoms.
