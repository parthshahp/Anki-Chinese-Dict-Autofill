# Anki-Chinese-Dict-Autofill

A very simple add-on that will allow you to automatically fill in your Chinese Anki card definitions. Just make sure to set which field your word is in and which field you would like the English definition to go in the config file.

## Installation

To install go [here](https://ankiweb.net/shared/info/1181718073).

## Config

To configure settings, go to Tools -> Add-ons -> Select this add-on and click Config. It should look like this:
```
{
    "definition_field": "Definition",
    "word_field": "Target",
    "expression_field": "Expression",
    "pinyin": "Pinyin",
    "tone_coloring": "1",
    "error_tag": "AutofillError",
    "auto_fill_on_add": false,
    "auto_fill_note_types": []
}
```
To generate the definitions, go to card explorer and select the cards that need the definitions filled in. Once selected, go to 'Edit', then 'Generate Chinese Readings' in the top bar.

## Automatic filling with ASBplayer / AnkiConnect

Enable automatic filling in the add-on config and specify the exact Anki note type names to process:

```json
"auto_fill_on_add": true,
"auto_fill_note_types": ["Chinese Mining"]
```

Replace `Chinese Mining` with your actual note type. These are settings to merge into the full config above. Automatic filling is disabled by default, including for existing installations without these settings. Config changes apply on the next operation; restart Anki after installing updated add-on code.

Configure ASBplayer to export the selected **word** to `Target` (or your configured `word_field`), and the subtitle sentence to `Expression`. Leave `Definition` and `Pinyin` blank to have them filled. Existing values, audio, images, and other fields are preserved. Whitespace-only or empty HTML fields such as `<br>` count as blank. Definition and reading are filled independently; the Pinyin field is optional.

The add-on uses `anki.hooks.note_will_be_added` to modify the note before Anki saves it. It also processes matching notes created in Anki's Add window, but does not run for imports or updates to existing notes. Notes without the configured word and definition fields are skipped.

Empty or unknown words are saved without a definition and tagged with `error_tag` (by default `AutofillError`). Dictionary failures are logged and tagged without blocking export or opening a dialog. Set `error_tag` to an empty string to disable tagging. Tags are not automatically removed on a later successful fill.

Lookups use local CC-CEDICT, not an external API, and do not use sentence context to choose a meaning or pronunciation. The current index supports simplified-character lookup only. The dictionary is loaded lazily and reused in memory; the first lookup may take longer while loading/rebuilding the disk cache.

Automatic filling never rewrites the source word or colors the sentence. The browser command still trims surrounding word whitespace and can color plain-text expressions when `tone_coloring` is `"1"`; expressions containing HTML are left unchanged to avoid corrupting markup or nesting tone spans.

### Verification

Run the automated tests without installing Anki:

```sh
python3 -m unittest discover -s tests -v
```

For an end-to-end check, restart Anki with this add-on and AnkiConnect enabled, enable the settings above, and export a known word such as `你好` from ASBplayer. Confirm the saved note has a definition and pinyin, with the sentence/audio/images unchanged. Also verify an existing definition is preserved, an unknown word receives `AutofillError`, and disabling autofill leaves new notes unchanged.

![image](https://github.com/parthshahp/Anki-Chinese-Dict-Autofill/assets/48393781/ffe53912-abf5-48e3-9ba4-164df07a5f63)


The first time you run the generator it will parse CEDICT and write a cache (`cedict_cache.json`) alongside the dictionary file so future runs load instantly. Delete the cache if you replace `cedict_ts.u8` and the add-on will rebuild it automatically.


(The name is a WIP)
