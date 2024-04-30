# import aqt.editor
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


def onRegenerate(browser):
    selected = browser.selectedNotes()

    if selected:
        # fields = anki.find.fieldNames(mw.col, selected)
        errors = []
        for nid in selected:
            note = browser.col.get_note(nid)

            if not note[def_field]:
                try:
                    definition = cc_dict[note[word_field]]["english"]
                    note[def_field] = list_to_html_list(definition)
                except:
                    errors.append(note[word_field])

            if not note[reading_field]:
                temp = cc_dict[note[word_field]]["pinyin"]
                note[reading_field], _ = decode_pinyin(temp)

            if tone_coloring == "1":
                new_expression = []
                for i in range(len(note[expression_field])):
                    if note[expression_field][i] in "，。、“”‘’《》？！：；{}[]()":
                        new_expression.append(note[expression_field][i])
                        continue

                    temp = cc_dict[note[expression_field][i]]["pinyin"]
                    _, tones = decode_pinyin(temp)

                    new_expression.append(
                        f"<span class='tone{tones[0]}'>{note[expression_field][i]}</span>"
                    )

                note[expression_field] = "".join(new_expression)

            browser.col.update_note(note)
        if errors:
            showInfo(f"Words not found: {errors}")
    else:
        showInfo("No notes selected")


def setupMenu(browser):
    a = QAction("Generate Chinese Readings", browser)
    a.triggered.connect(lambda: onRegenerate(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


cc_dict = load_dict()
gui_hooks.browser_menus_did_init.append(setupMenu)
