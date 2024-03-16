from aqt import mw
from aqt.utils import showInfo
from aqt.qt import QAction
# import aqt.editor
from anki.hooks import addHook
from .load_dict import load_dict

assert mw is not None
config = mw.addonManager.getConfig(__name__)

assert config is not None
def_field = config["definition_field"]
word_field = config["word_field"]
reading_field = config["pinyin"]

def onRegenerate(browser):
    selected = browser.selectedNotes()

    if selected:
        # fields = anki.find.fieldNames(mw.col, selected)
        for nid in selected:
            note = browser.col.get_note(nid)
            if not note[def_field]:
                html = list_to_html_list(cc_dict[note[word_field]]["english"])
                note[def_field] = html
            if not note[reading_field]:
                note[reading_field] = cc_dict[note[word_field]]["pinyin"]
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

def list_to_html_list(lst, ordered=False):
    list_type = "ol" if ordered else "ul"
    html_list = f"<{list_type}>"
    
    for item in lst:
        html_list += f"<li>{item}</li>"
    
    html_list += f"</{list_type}>"
    
    return html_list
