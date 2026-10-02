# Prompt Stash (simple)

One ComfyUI node: a prompt box with saved prompts in named lists.

```
Prompt Stash
 List    ◀ characters ▶        last entry: "+ New list…"
 Prompt  ◀ wizard ▶            picking one loads it into the box
 ┌───────────────────────┐
 │ prompt text           │
 └───────────────────────┘
 [ Save ] [ Save as… ] [ Delete ]
```

| control | does |
|---|---|
| List | which list Save and Prompt use; `+ New list…` makes one |
| Prompt | loads a saved prompt into the box |
| Save | overwrites the selected prompt with the box's text (with nothing selected, it is Save as…) |
| Save as… | saves the box under a new name (asks before replacing one) |
| Delete | deletes the selected prompt (asks first); the text stays in the box |
| right-click the node | rename or delete the current list |

Output: `text` (STRING). Only the text goes into the job, so picking another list or prompt never re-runs anything; the menus are saved with the workflow.

Prompts live in `ComfyUI/user/prompt_stash/prompt_stash_data.json`, shared by every workflow; the file format is the original pack's, so existing stashes carry over.

## Fork

Fork of [phazei/ComfyUI-Prompt-Stash](https://github.com/phazei/ComfyUI-Prompt-Stash) (Apache-2.0, see LICENSE), branch `simple`, 2026-10-02.
Changes: one node (`PromptStash`) replaces Saver, Passthrough and Manager; no text input, Use Input toggle, meta output, pause-to-edit or import/export; new routes under `/prompt_stash/`.
Kept from upstream: `data_utils.py` (data-file location and migration, trimmed) and `js/multi_button.js` (the button row).
Workflows using the old `PromptStashSaver` node need it swapped for `Prompt Stash`.
