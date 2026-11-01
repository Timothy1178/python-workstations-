# pptgen — build branded decks on top of a company .pptx template

Used to produce the "WhatsApp Chatbot Registration" deck on the ASW 185
template. Nothing brand-specific is stored here: the template stays on
your machine (drop it into the Doc & PPT Templates page) and the build
reads it from a local folder.

```
tools/pptgen/
  pptlib.py              # tiny OOXML slide builder: text, shapes, pictures, groups,
                         # entrance animations (fade / float / wipe / zoom / fly) and transitions
  build_whatsapp_deck.py # the deck itself — copy and edit for the next presentation
  icons.js               # renders react-icons to PNG in brand colours (node)
```

How to rebuild (Python 3 + node):

1. Unzip the template: `python -c "import zipfile; zipfile.ZipFile('template.pptx').extractall('tpl/unpacked')"`
2. `npm i react react-dom react-icons sharp && node icons.js` → `icons/*.png`
3. `python build_whatsapp_deck.py` → `build/`, then zip it from inside
   the folder: `(cd build && zip -Xr ../deck.pptx .)`.

The build keeps the template's masters, layouts, logos and art; slides
are written as XML with the shapes grouped so each card animates as one
unit. Expect to adjust `TPL`, `BUILD` and the icon folder paths at the
top of the build script.
