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
    "error_tag": "AutofillError"
}
```
To generate the definitions, go to card explorer and select the cards that need the definitions filled in. Once selected, go to 'Edit', then 'Generate Chinese Definitions' in the top bar.

![image](https://github.com/parthshahp/Anki-Chinese-Dict-Autofill/assets/48393781/ffe53912-abf5-48e3-9ba4-164df07a5f63)


The first time you run the generator it will parse CEDICT and write a cache (`cedict_cache.json`) alongside the dictionary file so future runs load instantly. Delete the cache if you replace `cedict_ts.u8` and the add-on will rebuild it automatically.


(The name is a WIP)
