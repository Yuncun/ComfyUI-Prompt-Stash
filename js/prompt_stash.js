// Prompt Stash: List and Prompt menus above the text box, Save / Save as… / Delete below it, list housekeeping in
// the right-click menu. The menus are saved with the workflow but not sent with the job (options.serialize = false),
// so switching them never re-runs anything.
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NONE = "—";
const NEW_LIST = "+ New list…";

const ask = async (title, message, defaultValue = "") => {
    const d = app.extensionManager?.dialog;
    return d?.prompt ? d.prompt({ title, message, defaultValue }) : window.prompt(message, defaultValue);
};
const sure = async (title, message) => {
    const d = app.extensionManager?.dialog;
    return d?.confirm ? !!(await d.confirm({ title, message })) : window.confirm(message);
};
const call = async (path, body) => {
    const res = await api.fetchApi(`/prompt_stash/${path}`, body ? { method: "POST", body: JSON.stringify(body) } : undefined);
    const json = await res.json();
    if (!json.success) {
        const toast = app.extensionManager?.toast;
        toast?.add ? toast.add({ severity: "error", summary: "Prompt Stash", detail: json.error, life: 5000 }) : alert(json.error);
    }
    return json;
};

// One copy of the lists ({list: {name: text}}) shared by every Prompt Stash node; the server broadcasts each change.
let lists = null;
const stashNodes = new Set();
const setLists = (l) => { lists = l; stashNodes.forEach((n) => n.stashRefresh()); };
api.addEventListener("prompt-stash-update-all", (e) => setLists(e.detail.lists));
let loading = null;
const loadLists = () => (loading ??= call("lists").then((j) => j.success && setLists(j.lists)).finally(() => (loading = null)));

app.registerExtension({
    name: "Yuncun.PromptStash",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "PromptStash") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            const node = this, text = this.widgets.find((w) => w.name === "text");
            const listW = this.addWidget("combo", "list", "default", (v) => pickList(v), { values: ["default"], serialize: false });
            const promptW = this.addWidget("combo", "prompt", NONE, (v) => pickPrompt(v), { values: [NONE], serialize: false });
            listW.label = "List";
            promptW.label = "Prompt";
            this.widgets.splice(0, this.widgets.length, listW, promptW, ...this.widgets.filter((w) => w !== listW && w !== promptW));
            const names = () => Object.keys(lists?.[listW.value] ?? {});
            const redraw = () => node.setDirtyCanvas(true, true);

            this.stashRefresh = () => {
                if (!lists) return;
                if (!(listW.value in lists)) { listW.value = Object.keys(lists)[0]; promptW.value = NONE; }
                if (promptW.value !== NONE && !names().includes(promptW.value)) promptW.value = NONE;
                listW.options.values = [...Object.keys(lists), NEW_LIST];
                promptW.options.values = [NONE, ...names()];
                redraw();
            };
            let shownList = listW.value;
            const pickList = async (v) => {
                if (v === NEW_LIST) {
                    listW.value = shownList;
                    const name = (await ask("New list", "Name of the new list:"))?.trim();
                    if (!name) return redraw();
                    const j = await call("add_list", { list: name });
                    if (!j.success) return redraw();
                    listW.value = name;
                    setLists(j.lists);
                }
                if (listW.value !== shownList) promptW.value = NONE;
                shownList = listW.value;
                this.stashRefresh();
            };
            const pickPrompt = (v) => {
                const saved = lists?.[listW.value]?.[v];
                if (v !== NONE && saved !== undefined) text.value = saved;
                redraw();
            };
            const save = async (name) => {
                const j = await call("save", { list: listW.value, name, text: text.value });
                if (j.success) { promptW.value = name; setLists(j.lists); }
            };
            const saveAs = async () => {
                const name = (await ask("Save prompt", `Save to "${listW.value}" as:`, promptW.value === NONE ? "" : promptW.value))?.trim();
                if (!name) return;
                if (name !== promptW.value && names().includes(name)
                    && !(await sure("Replace prompt", `"${name}" already exists in "${listW.value}". Replace it?`))) return;
                await save(name);
            };
            const del = async () => {
                if (promptW.value === NONE) return;
                if (!(await sure("Delete prompt", `Delete "${promptW.value}" from "${listW.value}"? The text stays in the box.`))) return;
                const j = await call("delete", { list: listW.value, name: promptW.value });
                if (j.success) { promptW.value = NONE; setLists(j.lists); }
            };
            const row = app.widgets.MULTI_BUTTON(this, "actions", {
                options: {
                    buttons: [
                        { label: "Save", callback: () => (promptW.value === NONE ? saveAs() : save(promptW.value)) },
                        { label: "Save as…", callback: saveAs },
                        { label: "Delete", callback: del },
                    ],
                    height: 28, gap: 10, pad: 16, alternate: false,
                },
            }, app);
            row.serialize = false;
            this.addCustomWidget(row);
            this.stashLists = {
                rename: async () => {
                    const old = listW.value, name = (await ask("Rename list", `New name for "${old}":`, old))?.trim();
                    if (!name || name === old) return;
                    const j = await call("rename_list", { list: old, new: name });
                    if (j.success) { stashNodes.forEach((n) => n !== node && n.widgets[0].value === old && (n.widgets[0].value = name)); listW.value = shownList = name; setLists(j.lists); }
                },
                remove: async () => {
                    const name = listW.value, count = names().length;
                    if (!(await sure("Delete list", `Delete the list "${name}" and its ${count} saved prompt${count === 1 ? "" : "s"}?`))) return;
                    const j = await call("delete_list", { list: name });
                    if (j.success) setLists(j.lists);
                },
            };

            stashNodes.add(this);
            const onRemoved = this.onRemoved;
            this.onRemoved = function () { stashNodes.delete(this); onRemoved?.apply(this, arguments); };
            lists ? this.stashRefresh() : loadLists();
        };

        const getExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (canvas, options) {
            getExtraMenuOptions?.apply(this, arguments);
            const list = this.widgets[0].value;
            options.push(null,
                { content: `Rename list "${list}"…`, callback: () => this.stashLists.rename() },
                { content: `Delete list "${list}"…`, callback: () => this.stashLists.remove() });
        };
    },
});
