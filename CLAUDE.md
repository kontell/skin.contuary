# skin.contuary — editing notes

Estuary-derived Kodi skin. This file captures non-obvious patterns for
editing the home screen. The iteration loop (kodi-remote / kodi-shot /
kodi-diff / kodi-logtail / kodi-builtin) lives in Claude's auto-memory,
not here.

## Home-screen layout files

- `xml/Home.xml` — window definition, per-category widget groups
  (movies=5000, tvshows=7000, weather=15000, …). Weather info top strip
  is `<control type="group" id="16678">`.
- `xml/Includes_Home.xml` — reusable widget templates: `CategoryLabel`,
  `WidgetListPoster`, `WidgetListEpisodes`, `WeatherWidget`, …
- `xml/Includes.xml` — generic includes used from multiple windows,
  e.g. `WeatherIconHome` (only used on the home weather screen).
- `xml/Font.xml` — two fontsets: `Default` (NotoSans) and `Arial`.
  Changes that touch a font must be mirrored in both.
- `xml/Defaults.xml` — element defaults. `<label>` default font is
  `font13`; relevant when a label has no explicit `<font>` tag.

## Position chain on the home widgets area

`<control type="group" id="2000">` has `<left>70</left>`. All
per-category groups (5000, 15000, …) sit inside it and inherit that
offset. So a nominal "x=0" in a WeatherWidget is actually at skin x=70.
Keep this in mind when aligning widgets with off-widget elements.

## Parameterising shared includes

When you need to tweak *only one caller* of a shared include, add a
param with a default that preserves existing behaviour rather than
forking the include. Applied so far to `CategoryLabel`:

- `posx` (default 55) — left offset of the label
- `font` (default `font13`) — lets the weather caller pick a smaller font

Pattern: add `<param name="X">default</param>` at the top of the
`<include>`, reference as `$PARAM[X]` in the definition, then pass
`<param name="X" value="..."/>` only at the call site that needs a
change. Unrelated callers keep the default and stay untouched.

## WeatherWidget card scaling

Card dimensions in `WeatherWidget` (Includes_Home.xml) are driven by a
single `width` param but *the other numbers don't auto-scale* — they're
hard-coded inside itemlayout and focusedlayout. When resizing, update
together:

- `<param name="width">` — outer slot width (== bg + shadow)
- `itemlayout` / `focusedlayout` `height`
- inner `<group><left>` — centres the card horizontally in its slot
- bg `<control type="image">` width/height/top and `bordersize`
- icon width/height/left/top
- label widths (so centred text stays inside the card)
- focus `<effect type="zoom">` `center="x,y"` — midpoint of the bg image

Both `itemlayout` and `focusedlayout` contain duplicated structures;
any dimension change must be applied to *both*.

The enclosing group `id="16678"` in Home.xml has its own `<right>` that
defines where the top weather-info block ends — keep it aligned with
the card-row right edge (`right=25` matches the current card width).

## Font conventions

Weather-screen text uses `_w`-suffixed font variants
(`font12_w`, `font13_w`, `font14_w`, `font27_narrow_w`,
`font30_title_w`), scaled ~0.95× of their non-suffixed originals in
both fontsets. Rule of thumb: if you shrink the cards, shrink the
text the same amount; introduce a new `*_w` variant rather than
editing the shared font.

If another sub-area of the skin needs its own scaled fonts, follow the
same pattern with a different suffix (e.g. `_small`) rather than
reusing `_w`.
