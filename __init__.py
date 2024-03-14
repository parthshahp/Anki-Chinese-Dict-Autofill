from aqt import mw
from aqt.utils import showInfo
# from aqt.qt import *
# import aqt.editor
from anki.hooks import addHook
from .load_dict import load_dict

assert mw is not None
config = mw.addonManager.getConfig(__name__)

assert config is not None
def_field = config["definition_field"]
word_field = config["word_field"]

def onRegenerate(browser):
    selected = browser.selectedNotes()

    if selected:
        # fields = anki.find.fieldNames(mw.col, selected)
        for nid in selected:
            note = browser.col.get_note(nid)
            if not note[def_field]:
                note[def_field] = cc_dict[note[word_field]]["english"]
            browser.col.update_note(note)
    else:
        showInfo("No notes selected")

def setupMenu(browser):
    a = QAction("Generate Chinese Readings", browser)
    a.triggered.connect(lambda: onRegenerate(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)

cc_dict = load_dict()
addHook("browser.setupMenus", setupMenu)
