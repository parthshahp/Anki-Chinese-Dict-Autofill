"""Anki integration for manual and on-add Chinese dictionary autofill."""

import logging
from typing import Dict, Optional

from anki.hooks import note_will_be_added
from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import showInfo

from .autofill import autofill_note
from .load_dict import load_dict


logger = logging.getLogger(__name__)
cc_dict: Optional[Dict[str, Dict[str, object]]] = None


def _get_config():
    # Read on each operation so changes in Tools > Add-ons apply immediately.
    if mw is None:
        return {}
    return mw.addonManager.getConfig(__name__) or {}


def _get_cc_dict() -> Dict[str, Dict[str, object]]:
    global cc_dict
    if cc_dict is None:
        cc_dict = load_dict()
    return cc_dict


def auto_fill_on_add(col, note, deck_id):
    """Enrich an unsaved note without blocking note creation on failure."""
    config = _get_config()
    if config.get("auto_fill_on_add", False) is not True:
        return
    allowed_types = config.get("auto_fill_note_types", [])
    if not isinstance(allowed_types, list):
        return
    if note.note_type()["name"] not in allowed_types:
        return
    if not all(config.get(key) in note for key in ("word_field", "definition_field")):
        return

    try:
        result = autofill_note(note, _get_cc_dict(), config)
        if result.error:
            logger.warning("Chinese autofill: %s", result.error)
    except Exception:
        # Exceptions escaping this hook would cause AnkiConnect exports to fail.
        logger.exception("Chinese autofill failed; saving note without autofill")
        error_tag = (config.get("error_tag") or "").strip()
        if error_tag:
            note.add_tag(error_tag)


def onRegenerate(browser):
    selected = browser.selectedNotes()
    if not selected:
        showInfo("No notes selected")
        return

    try:
        dictionary = _get_cc_dict()
    except (OSError, ValueError) as err:
        showInfo(f"Failed to load dictionary: {err}")
        return

    config = _get_config()
    errors = []
    for nid in selected:
        note = browser.col.get_note(nid)
        result = autofill_note(note, dictionary, config, manual=True)
        if result.changed:
            browser.col.update_note(note)
        if result.error:
            errors.append(f"Note {nid}: {result.error}")

    if errors:
        formatted_errors = "\n".join(errors)
        showInfo(f"Some notes could not be updated:\n{formatted_errors}")


def setupMenu(browser):
    action = QAction("Generate Chinese Readings", browser)
    action.triggered.connect(lambda: onRegenerate(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(action)


note_will_be_added.append(auto_fill_on_add)
gui_hooks.browser_menus_did_init.append(setupMenu)
