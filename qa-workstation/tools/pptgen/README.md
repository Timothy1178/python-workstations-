# pptgen — build branded decks on top of a company .pptx template

Used to produce the "WhatsApp Chatbot Registration" deck on the ASW 185
template. Nothing brand-specific is stored here: the template stays on
your machine (drop it into the Doc & PPT Templates page) and the build
reads it from a local folder.

```
tools/pptgen/
  pptlib.py              # tiny OOXML slide builder: text, shapes, pictures, groups,
                         # entrance animations (fade / float / wipe / zoom / fly) and transitions
  build_whatsapp_deck.py # the WhatsApp chatbot registration deck
  build_showcase_deck.py # the 35-slide design catalog / skills showcase (spin, pulse,
                         # motion paths, hyperlinked catalog, rings, funnel, mock-ups…)
  post_charts.py         # python-pptx step that adds native charts + a styled table
  icons.js               # renders react-icons to PNG in brand colours + grey image placeholders (node)
```

Effects available in `pptlib.EFFECTS`: entrance `fade float rise wipe wipedown wheel
split zoom spinin flyleft flyright flyup`; emphasis `spin spinloop spinback pulse grow`
(loop variants repeat until the end of the slide); motion paths `slideright bounce`.

How to rebuild (Python 3 + node):

1. Unzip the template: `python -c "import zipfile; zipfile.ZipFile('template.pptx').extractall('tpl/unpacked')"`
2. `npm i react react-dom react-icons sharp && node icons.js` → `icons/*.png`
3. `python build_whatsapp_deck.py` (or `build_showcase_deck.py`) → `build/`, then zip it
   from inside the folder: `(cd build && zip -Xr ../deck.pptx .)`.
4. Showcase only: `python post_charts.py deck.pptx 15 17` adds the charts and the table.

The build keeps the template's masters, layouts, logos and art; slides
are written as XML with the shapes grouped so each card animates as one
unit. Expect to adjust `TPL`, `BUILD` and the icon folder paths at the
top of the build script.
