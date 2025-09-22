# import aqt.editor
from typing import Dict, Optional

from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import showInfo

from .load_dict import load_dict
from .utils import decode_pinyin, list_to_html_list

assert mw is not None
config = mw.addonManager.getConfig(__name__)

assert config is not None
def_field = config["definition_field"]
word_field = config["word_field"]
reading_field = config["pinyin"]
tone_coloring = config["tone_coloring"]
expression_field = config["expression_field"]
error_tag = (config.get("error_tag") or "").strip()


cc_dict: Optional[Dict[str, Dict[str, object]]] = None


def _get_cc_dict() -> Dict[str, Dict[str, object]]:
    global cc_dict
    if cc_dict is None:
        cc_dict = load_dict()
    return cc_dict


def _sanitize_field(raw_value: str) -> str:
    """Strip surrounding whitespace and normalize internal newlines."""

    if not raw_value:
        return ""

    return raw_value.strip()


def onRegenerate(browser):
    selected = browser.selectedNotes()

    if not selected:
        showInfo("No notes selected")
        return

    try:
        dictionary = _get_cc_dict()
    except OSError as err:
        showInfo(f"Failed to load dictionary: {err}")
        return

    errors = []
    for nid in selected:
        note = browser.col.get_note(nid)

        original_word = note[word_field]
        sanitized_word = _sanitize_field(original_word)

        note_changed = False

        if sanitized_word != original_word:
            note[word_field] = sanitized_word
            note_changed = True

        if not sanitized_word:
            errors.append(f"Note {nid}: empty value in '{word_field}'")
            if error_tag:
                note.addTag(error_tag)
                note_changed = True
            if note_changed:
                browser.col.update_note(note)
            continue

        entry = dictionary.get(sanitized_word)

        if entry is None:
            errors.append(f"Note {nid}: '{sanitized_word}' not found in dictionary")
            if error_tag:
                note.addTag(error_tag)
                note_changed = True
            if note_changed:
                browser.col.update_note(note)
            continue

        if not note[def_field]:
            note[def_field] = list_to_html_list(entry["english"])
            note_changed = True

        if not note[reading_field]:
            reading, _ = decode_pinyin(entry["pinyin"])
            note[reading_field] = reading
            note_changed = True

        if tone_coloring == "1" and note[expression_field]:
            new_expression = []
            for char in note[expression_field]:
                if char in "，。、“”‘’《》？！：；{}[]()":
                    new_expression.append(char)
                    continue

                char_entry = dictionary.get(char)
                if not char_entry:
                    new_expression.append(char)
                    continue

                _, tones = decode_pinyin(char_entry["pinyin"])
                if not tones:
                    new_expression.append(char)
                    continue

                new_expression.append(f"<span class='tone{tones[0]}'>{char}</span>")

            colored_expression = "".join(new_expression)
            if colored_expression != note[expression_field]:
                note[expression_field] = colored_expression
                note_changed = True

        if note_changed:
            browser.col.update_note(note)

    if errors:
        formatted_errors = "\n".join(errors)
        showInfo(f"Some notes could not be updated:\n{formatted_errors}")


def setupMenu(browser):
    a = QAction("Generate Chinese Readings", browser)
    a.triggered.connect(lambda: onRegenerate(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


cc_dict = load_dict()
gui_hooks.browser_menus_did_init.append(setupMenu)
