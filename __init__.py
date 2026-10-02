"""Prompt Stash (simple): one node that keeps prompts in named lists. Fork of phazei/ComfyUI-Prompt-Stash (Apache-2.0)."""
import json
import os

from aiohttp import web
from server import PromptServer

from .data_utils import init_data_file
from .prompt_stash_node import PromptStash

DATA_FILE = init_data_file(os.path.dirname(os.path.realpath(__file__)))


def _load():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {"version": "1.0"}
    if not data.get("lists"):
        data["lists"] = {"default": {}}
    return data


def _save(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)
    PromptServer.instance.send_sync("prompt-stash-update-all", {"lists": data["lists"]})


def _ok(data):
    return web.json_response({"success": True, "lists": data["lists"]})


def _fail(error):
    return web.json_response({"success": False, "error": error}, status=400)


async def _body(request):
    body = await request.json()
    return {k: v.strip() if isinstance(v, str) and k != "text" else v for k, v in body.items()}


routes = PromptServer.instance.routes


@routes.get("/prompt_stash/lists")
async def get_lists(request):
    return _ok(_load())


@routes.post("/prompt_stash/save")
async def save_prompt(request):
    b, data = await _body(request), _load()
    if b.get("list") not in data["lists"]:
        return _fail(f'No list named "{b.get("list")}".')
    if not b.get("name"):
        return _fail("A saved prompt needs a name.")
    data["lists"][b["list"]][b["name"]] = str(b.get("text", ""))
    _save(data)
    return _ok(data)


@routes.post("/prompt_stash/delete")
async def delete_prompt(request):
    b, data = await _body(request), _load()
    if b.get("name") not in data["lists"].get(b.get("list"), {}):
        return _fail(f'No prompt "{b.get("name")}" in "{b.get("list")}".')
    del data["lists"][b["list"]][b["name"]]
    _save(data)
    return _ok(data)


@routes.post("/prompt_stash/add_list")
async def add_list(request):
    b, data = await _body(request), _load()
    if not b.get("list"):
        return _fail("A list needs a name.")
    if b["list"] in data["lists"]:
        return _fail(f'A list named "{b["list"]}" already exists.')
    data["lists"][b["list"]] = {}
    _save(data)
    return _ok(data)


@routes.post("/prompt_stash/rename_list")
async def rename_list(request):
    b, data = await _body(request), _load()
    old, new = b.get("list"), b.get("new")
    if old not in data["lists"]:
        return _fail(f'No list named "{old}".')
    if not new or new in data["lists"]:
        return _fail(f'Pick a new name that isn\'t taken ("{new}").')
    data["lists"] = {new if k == old else k: v for k, v in data["lists"].items()}
    _save(data)
    return _ok(data)


@routes.post("/prompt_stash/delete_list")
async def delete_list(request):
    b, data = await _body(request), _load()
    if b.get("list") not in data["lists"]:
        return _fail(f'No list named "{b.get("list")}".')
    if len(data["lists"]) == 1:
        return _fail("Can't delete the only list.")
    del data["lists"][b["list"]]
    _save(data)
    return _ok(data)


NODE_CLASS_MAPPINGS = {"PromptStash": PromptStash}
NODE_DISPLAY_NAME_MAPPINGS = {"PromptStash": "Prompt Stash"}
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
