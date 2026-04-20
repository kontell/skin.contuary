# skin.contuary — editing notes

Estuary-derived Kodi skin. This file captures non-obvious patterns for
editing the home screen. The iteration loop (kodi-remote / kodi-shot /
kodi-diff / kodi-logtail / kodi-builtin) lives in Claude's auto-memory,
not here.

## Card-size variants

The skin ships three layout templates targeting 16:9 displays:

- `xml_large/` — 6 cards across (reference layout; scaling factor 1.0)
- `xml_medium/` — 7 cards across (factor ~0.857)
- `xml_small/` — 8 cards across (factor ~0.75)

`addon.xml` `<res>` points at `xml/` — the **live render target**. It
is a copy of whichever template is currently selected and is
gitignored; populate it by running the variant switcher at least once
after install. The companion script addon `script.skin.contuary`
swaps templates at runtime:

- `RunScript(script.skin.contuary,<variant>)` — apply a named variant
- `RunScript(script.skin.contuary)` — cycle small → medium → large → small

The script rmtree's `xml/`, copytree's `xml_<variant>/` into `xml/`,
sets `Skin.String(card_size,<variant>)`, then `ReloadSkin()`. No Kodi
restart needed.

User-facing switches:
- Settings → Skin settings → Card size (button id=708 in `SkinSettings.xml`)
- F6 keyboard shortcut (developer-local, kept in `userdata/keymaps/keymap.xml`
  — Kodi does not auto-load skin-shipped keymaps)

**When editing layout**: modify the templates under `xml_<variant>/`,
then let the script repopulate `xml/`. Direct edits to `xml/` are
wiped on the next variant switch. The weather widget is intentionally
identical across all three variants — don't scale it.

## Home-screen layout files

Paths below are relative to each template (`xml_large/`, `xml_medium/`,
`xml_small/`); `xml/` mirrors whichever template is active.

- `Home.xml` — window definition, per-category widget groups
  (movies=5000, tvshows=7000, weather=15000, …). Weather info top strip
  is `<control type="group" id="16678">`. Main Menu Title label is
  `id="2099"`, positioned at `<left>82</left>` inside group 2000 so it
  aligns with the first card of the widget row below.
- `Includes_Home.xml` — reusable widget templates: `CategoryLabel`,
  `WidgetListPoster`, `WidgetListEpisodes`, `WeatherWidget`, …
- `Includes.xml` — generic includes used from multiple windows,
  e.g. `WeatherIconHome` (only used on the home weather screen).
- `Font.xml` — two fontsets: `Default` (NotoSans) and `Arial`.
  Changes that touch a font must be mirrored in both.
- `Defaults.xml` — element defaults. `<label>` default font is
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

Home-widget text (all per-category widgets) uses `_w`-suffixed font
variants (`font10_w`, `font12_w`, `font13_w`, `font14_w`,
`font25_narrow_w`, `font27_w`, `font27_narrow_w`, `font20_title_w`,
`font30_title_w`). In `xml_large/Font.xml` these are ~0.945× the
non-suffixed originals; `xml_medium/` and `xml_small/` scale those
`_w` sizes by the same factor as the cards (0.857 and 0.75
respectively) so text shrinks in lockstep with slot width. The
non-suffixed fonts are identical across variants.

The Main Menu Title uses `font_mainmenu` (also scaled per variant:
45 / 39 / 34 for large / medium / small).

If another sub-area of the skin needs its own scaled fonts, follow the
same pattern with a different suffix (e.g. `_small`) rather than
reusing `_w`.

## Scaling other home widgets to 6 cards across

The widget panel inside group 2000 spans 1850 skin px. To fit 6 slots
evenly with ≈25 px right margin matching the weather row, each slot is
scaled by 0.945 from the original card width. Widgets covered:

- `WidgetListPoster` (movies, tvshows posters)
- `WidgetListEpisodes` (recently added episodes)
- `WidgetListSquare` (music albums)
- `WidgetListCategories` (inline — categories/genre rows, addons)
- `WidgetListPVR` (live TV channel tiles)

For each, update the outer slot `width`, `itemlayout`/`focusedlayout`
`height`, inner `<group>` `<left>` (to centre the card in its slot),
focus `<effect type="zoom">` `center="x,y"`, and any hard-coded
dimensions inside inline layouts.

## Forking shared InfoWall layouts

`WidgetListPoster`, `WidgetListEpisodes`, `WidgetListSquare` reference
layout includes defined in `View_54_InfoWall.xml` that are *also* used
by the full-screen View 54 (movies/tvshows/episodes/music browser).
To scale the home variants without touching View 54, fork the layout:
add `InfoWallMovieLayoutHome`, `InfoWallEpisodeLayoutHome`,
`InfoWallMusicLayoutHome` as new includes in that file and point the
home widget include at the `*Home` variant. All internal dimensions
(bg width/height/left/top, textbox, overlay, progress, rating offsets,
bordersize) must be scaled together — they are hard-coded, not
derived from the slot width.

## Left-aligning widget category labels

`CategoryLabel` has a `posx` parameter (default 55). For home widgets,
pass `posx=82` so the label lines up with the first card's left edge
within the widget slot. Also pass `font=font13_w` for the scaled
variant.

## Main Menu Title and hidden Categories label

The home screen shows the current main-menu section name (Movies,
TV shows, …) as a heading above the Categories row. Implemented as a
single label `id="2099"` inside group 2000, sourcing its text from
`$INFO[Container(9000).ListItem.Label]`. Positioned at `<left>82</left>`
to align with the first card.

The stock Categories widget title is suppressed by passing
`widget_header=""` at the `WidgetListCategories` call site (rather
than `visible=false`, which would hide the card panel too). The
CategoryLabel control still renders — it's just empty.
