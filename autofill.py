"""Shared, persistence-free Chinese note autofill logic."""

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Mapping, Optional

from .utils import decode_pinyin, list_to_html_list


class _FieldText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.has_media = False

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "div", "p"}:
            self.parts.append(" ")
        if tag in {"img", "audio", "video", "object", "iframe"}:
            self.has_media = True


def _field_text(value):
    parser = _FieldText()
    parser.feed(value)
    parser.close()
    return "".join(parser.parts).strip(), parser.has_media


def _is_blank(value):
    text, has_media = _field_text(value)
    return not text and not has_media


@dataclass
class AutofillResult:
    changed: bool = False
    error: Optional[str] = None


def autofill_note(note, dictionary: Mapping, config: Mapping, *, manual=False):
    """Mutate fields/tags only; the caller is responsible for saving the note.

    Missing required fields indicate an unrelated note and are skipped. Pinyin
    and expression fields are optional. Automatic fills never rewrite the word
    or expression fields.
    """
    word_field = config["word_field"]
    definition_field = config["definition_field"]
    if word_field not in note or definition_field not in note:
        return AutofillResult()

    result = AutofillResult()
    original_word = note[word_field]
    word, _ = _field_text(original_word)
    if manual and original_word != original_word.strip():
        note[word_field] = original_word.strip()
        result.changed = True

    entry = dictionary.get(word) if word else None
    if not word:
        result.error = f"empty value in '{word_field}'"
    elif entry is None:
        result.error = f"'{word}' not found in dictionary"

    if result.error:
        error_tag = (config.get("error_tag") or "").strip()
        if error_tag and error_tag not in note.tags:
            note.add_tag(error_tag)
            result.changed = True
        return result

    # Prepare values before mutating fields, so malformed entries don't leave
    # a partially filled note when the automatic callback handles the error.
    updates = {}
    if _is_blank(note[definition_field]):
        updates[definition_field] = list_to_html_list(entry["english"])

    reading_field = config.get("pinyin")
    if reading_field and reading_field in note and _is_blank(note[reading_field]):
        updates[reading_field], _ = decode_pinyin(entry["pinyin"])

    expression_field = config.get("expression_field")
    if (manual and config.get("tone_coloring") == "1"
            and expression_field and expression_field in note):
        expression = note[expression_field]
        # Never traverse HTML markup as Chinese text or nest tone spans on rerun.
        if expression and "<" not in expression:
            colored = []
            for char in expression:
                char_entry = dictionary.get(char)
                tones = decode_pinyin(char_entry["pinyin"])[1] if char_entry else []
                colored.append(f"<span class='tone{tones[0]}'>{char}</span>" if tones else char)
            updates[expression_field] = "".join(colored)

    for field, value in updates.items():
        if note[field] != value:
            note[field] = value
            result.changed = True
    return result
