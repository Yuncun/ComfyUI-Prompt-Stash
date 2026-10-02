class PromptStash:
    """A prompt box with saved prompts. The List and Prompt menus and the Save buttons live in the browser
    (js/prompt_stash.js) and use the routes in __init__.py; only the text reaches the job, so picking another
    list or saved prompt never re-runs anything."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"text": ("STRING", {"multiline": True, "default": "", "placeholder": "prompt"})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "utils"
    DESCRIPTION = "Type a prompt, or pick a saved one from a list. Save / Save as… / Delete store it in user/prompt_stash/."

    def run(self, text):
        return (text,)
