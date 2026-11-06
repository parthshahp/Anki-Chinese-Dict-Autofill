"""Run with python3 -m unittest discover -s tests -v (no Anki required)."""

import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "chinese_autofill_test"


def load_addon():
    hooks = types.ModuleType("anki.hooks")
    hooks.note_will_be_added = []
    anki = types.ModuleType("anki")
    anki.hooks = hooks
    aqt = types.ModuleType("aqt")
    aqt.gui_hooks = types.SimpleNamespace(browser_menus_did_init=[])
    aqt.mw = types.SimpleNamespace(addonManager=Mock())
    qt = types.ModuleType("aqt.qt")
    qt.QAction = Mock()
    utils = types.ModuleType("aqt.utils")
    utils.showInfo = Mock()
    modules = {"anki": anki, "anki.hooks": hooks, "aqt": aqt,
               "aqt.qt": qt, "aqt.utils": utils}
    spec = importlib.util.spec_from_file_location(
        PACKAGE, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    addon = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = addon
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(addon)
    return addon, hooks, aqt


addon, hooks, aqt = load_addon()
autofill_note = addon.autofill_note
DICTIONARY = {"你好": {"english": ["hello", "hi"], "pinyin": "ni3 hao3"},
              "你": {"english": ["you"], "pinyin": "ni3"}}


class Note(dict):
    def __init__(self, name="Chinese Mining", **fields):
        super().__init__(Target="你好", Definition="", Pinyin="", Expression="你好")
        self.update(fields)
        self.name = name
        self.tags = []

    def note_type(self):
        return {"name": self.name}

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)


class AutofillTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config.json").read_text())
        self.config.update(auto_fill_on_add=True, auto_fill_note_types=["Chinese Mining"])
        aqt.mw.addonManager.getConfig.return_value = self.config
        addon.cc_dict = DICTIONARY
        addon.showInfo.reset_mock()

    def test_hook_registered(self):
        self.assertIn(addon.auto_fill_on_add, hooks.note_will_be_added)

    def test_fill_and_preserve_source_fields(self):
        note = Note(Target=" <b>你好</b>&nbsp; ")
        addon.auto_fill_on_add(None, note, 1)
        self.assertEqual(note["Definition"], "<ul><li>hello</li><li>hi</li></ul>")
        self.assertEqual(note["Pinyin"], "nǐhǎo")
        self.assertEqual(note["Target"], " <b>你好</b>&nbsp; ")
        self.assertEqual(note["Expression"], "你好")

    def test_fields_preserved_independently(self):
        for field in ("Definition", "Pinyin"):
            with self.subTest(field=field):
                note = Note(**{field: "existing"})
                autofill_note(note, DICTIONARY, self.config)
                self.assertEqual(note[field], "existing")
                other = "Pinyin" if field == "Definition" else "Definition"
                self.assertTrue(note[other])

    def test_html_blank_and_media(self):
        note = Note(Definition="<div><br>&nbsp;</div>", Pinyin="  ")
        autofill_note(note, DICTIONARY, self.config)
        self.assertIn("hello", note["Definition"])
        self.assertEqual(note["Pinyin"], "nǐhǎo")
        for value in ('<img src="x.png">', '[sound:x.mp3]', '<audio src="x.mp3"></audio>'):
            note = Note(Definition=value)
            autofill_note(note, DICTIONARY, self.config)
            self.assertEqual(note["Definition"], value)

    def test_errors_tagged_without_dialogs(self):
        for word in ("", "<br>", "not-in-dictionary"):
            with self.subTest(word=word), self.assertLogs(addon.logger, level="WARNING"):
                note = Note(Target=word)
                addon.auto_fill_on_add(None, note, 1)
                self.assertEqual(note.tags, ["AutofillError"])
                self.assertEqual(note["Definition"], "")
        addon.showInfo.assert_not_called()

    def test_skipped_notes_do_not_load_dictionary(self):
        cases = [({}, Note(name="Other")),
                 ({"auto_fill_on_add": False}, Note()),
                 ({"auto_fill_note_types": []}, Note()),
                 ({"auto_fill_note_types": "Chinese Mining"}, Note())]
        missing = Note()
        del missing["Definition"]
        cases.append(({}, missing))
        for overrides, note in cases:
            with self.subTest(overrides=overrides):
                aqt.mw.addonManager.getConfig.return_value = {**self.config, **overrides}
                before = dict(note)
                with patch.object(addon, "_get_cc_dict") as loader:
                    addon.auto_fill_on_add(None, note, 1)
                    loader.assert_not_called()
                self.assertEqual(note, before)
                self.assertEqual(note.tags, [])

    def test_legacy_configuration_is_disabled(self):
        del self.config["auto_fill_on_add"]
        del self.config["auto_fill_note_types"]
        note = Note()
        addon.auto_fill_on_add(None, note, 1)
        self.assertEqual(note["Definition"], "")

    def test_optional_fields(self):
        note = Note()
        del note["Pinyin"]
        del note["Expression"]
        autofill_note(note, DICTIONARY, self.config, manual=True)
        self.assertIn("hello", note["Definition"])

    def test_dictionary_failure_does_not_escape_hook(self):
        note = Note()
        with patch.object(addon, "_get_cc_dict", side_effect=OSError("missing")):
            with self.assertLogs(addon.logger, level="ERROR"):
                addon.auto_fill_on_add(None, note, 1)
        self.assertEqual(note["Definition"], "")
        self.assertEqual(note.tags, ["AutofillError"])
        addon.showInfo.assert_not_called()

    def test_hook_never_persists_note_itself(self):
        collection = Mock()
        addon.auto_fill_on_add(collection, Note(), 1)
        self.assertEqual(collection.mock_calls, [])

    def test_dictionary_is_loaded_once_and_reused(self):
        addon.cc_dict = None
        with patch.object(addon, "load_dict", return_value=DICTIONARY) as loader:
            addon.auto_fill_on_add(None, Note(), 1)
            addon.auto_fill_on_add(None, Note(), 1)
            loader.assert_called_once_with()

    def test_manual_command_saves_changes(self):
        note = Note(Target=" 你好 ")
        browser = Mock()
        browser.selectedNotes.return_value = [123]
        browser.col.get_note.return_value = note
        addon.onRegenerate(browser)
        browser.col.update_note.assert_called_once_with(note)
        self.assertEqual(note["Target"], "你好")
        self.assertIn("tone3", note["Expression"])

    def test_repeated_processing_preserves_colored_html(self):
        note = Note()
        autofill_note(note, DICTIONARY, self.config, manual=True)
        expression = note["Expression"]
        result = autofill_note(note, DICTIONARY, self.config, manual=True)
        self.assertEqual(note["Expression"], expression)
        self.assertFalse(result.changed)

    def test_empty_selection(self):
        browser = Mock()
        browser.selectedNotes.return_value = []
        addon.onRegenerate(browser)
        addon.showInfo.assert_called_once_with("No notes selected")


if __name__ == "__main__":
    unittest.main()
