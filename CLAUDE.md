# skin.contuary — editing notes

Estuary-derived Kodi skin. This file captures non-obvious patterns for
editing the home screen. The iteration loop (kodi-remote / kodi-shot /
kodi-diff / kodi-logtail / kodi-builtin) lives in Claude's auto-memory,
not here.

## Resolution variants

The skin authors XML in a single `xml/` tree. The active logical coord
space is selected by the `<res>` element in `addon.xml`. Companion
addon `script.skin.contuary` rewrites that line to switch resolutions.

- `RunScript(script.skin.contuary)` — open a select dialog (preselects
  the current resolution)
- `RunScript(script.skin.contuary,<name>)` — apply the named option
  directly (e.g. `1920x1080`, `2256x1269`)
- `RunScript(script.skin.contuary,_sync)` — silently sync
  `Skin.String(resolution)` to whatever is currently in `addon.xml`

A Kodi restart is required after a `<res>` change because Kodi only
parses `addon.xml` at skin load. The script prompts for the restart
via a yes/no dialog. `ReloadSkin()` is *not* sufficient.

User-facing entry point: Settings → Skin settings → Resolution
(button id=708 in `SkinSettings.xml`). The button's `label2` shows
`$INFO[Skin.String(resolution)]`; SkinSettings has an
`<onload condition="System.HasAddon(script.skin.contuary)">RunScript(script.skin.contuary,_sync)</onload>`
hook so the displayed value stays in sync if `addon.xml` was edited
out of band.

The full set of supported options lives in `OPTIONS` at the top of
`script.skin.contuary/default.py` — add an entry there to expose a new
resolution.

**Dev tree vs installed tree.** There are two copies of `xml/`:

- Dev: `/media/minipie/bluecon/docs/IT/devel/skins/skin.contuary/xml/`
- Installed: `/home/conor/.kodi/addons/skin.contuary/xml/`

`ReloadSkin()` reads the installed tree. Edits made only to dev are
invisible until copied across. Keep the two in sync.

## IconButton vs IconButtonLarge

Two round-icon button includes in `Includes_Buttons.xml`:

- `IconButton` — flat single `<control type="radiobutton">`. Safe to drop
  into any grouplist; grouplist auto-wires up/down/left/right between
  direct focusable children. Used by the playback-controls sidebar
  (`grouplist id="14100"`, ids 14101..14106), the touchscreen row in
  `Includes.xml`, and all other multi-button rows.
- `IconButtonLarge` — `<control type="group">` wrapping an overhanging
  focus-ring image + a radiobutton. Lets the focus ring be larger than
  the button bounds. Because the outer control is a group,
  grouplist auto-wiring **does not work** through it — callers must pass
  explicit `onup`/`ondown`/`onleft`/`onright` params. Currently used
  only by the three PSS buttons on the home screen.

Rule: if you need a bigger focus ring on an existing auto-wired
grouplist, convert just that *caller site* to `IconButtonLarge` and wire
navigation by hand. Do not promote `IconButton` itself to the group form
— it silently breaks every grouplist that uses it.

## Home-screen layout files

- `Home.xml` — window definition, per-category section groups
  (movies=5000, tvshows=6000, music=7000, addons=8000, video=11000,
  livetv=12000, radio=13000, favorites=14000, weather=15000,
  musicvideos=16000, pictures=4000, games=17000, disc=21000). Weather
  info top strip is `<control type="group" id="16678">`.
- `Includes_Home.xml` — reusable widget templates: `MainMenuTitle`,
  `CategoryLabel`, `WidgetListPoster`, `WidgetListEpisodes`,
  `WeatherWidget`, …
- `Includes.xml` — generic includes used from multiple windows,
  e.g. `WeatherIconHome` (only used on the home weather screen).
- `Font.xml` — two fontsets: `Default` (NotoSans) and `Arial`.
  Changes that touch a font must be mirrored in both.
- `Defaults.xml` — element defaults. `<label>` default font is
  `font13`; relevant when a label has no explicit `<font>` tag.

## Position chain on the home widgets area

`<control type="group" id="2000">` has `<left>70</left>`. All
per-section groups (5000, 6000, …) sit inside it and inherit that
offset. So a nominal "x=0" in a WeatherWidget is actually at skin x=70.
Keep this in mind when aligning widgets with off-widget elements.

## Parameterising shared includes

When you need to tweak *only one caller* of a shared include, add a
param with a default that preserves existing behaviour rather than
forking the include. Applied to `CategoryLabel`:

- `posx` (default 55) — left offset of the label
- `font` (default `font13`) — lets the weather caller pick a smaller font

Pattern: add `<param name="X">default</param>` at the top of the
`<include>`, reference as `$PARAM[X]` in the definition, then pass
`<param name="X" value="..."/>` only at the call site that needs a
change. Unrelated callers keep the default and stay untouched.

## Main Menu Title

Each section group on the home screen displays its name (Movies,
Shows, Music, …) above the widget stack. Implemented as the
`MainMenuTitle` include in `Includes_Home.xml` — a `<control type="group">`
of `<height>140</height>` wrapping a `font_mainmenu` label at
`<top>20</top><left>82</left>`. The 140 height reserves enough space
to push the first widget down clear of the title (the grouplist
otherwise pulls the next item up because of `itemgap=-160`).

Each section's grouplist (5001, 6001, 7001, …) calls `MainMenuTitle`
as its first child with a static label, e.g.

```xml
<include content="MainMenuTitle">
    <param name="label" value="$LOCALIZE[342]"/>
</include>
```

Putting the title *inside* the grouplist achieves two things:

1. The title scrolls up with the widgets when the user navigates down
   the stack — they share the grouplist's scroll offset.
2. The title inherits the section group's `Visible_Right_Delayed`
   slide-in/out animation, so it animates together with the widgets
   when cycling main menu sections.

The label is static per section (passed in at the call site) rather
than dynamic via `$INFO[Container(9000).ListItem.Label]` — a dynamic
label would briefly show the *new* section's text while the *old*
section is still sliding off-screen.

Sections without a grouplist (favorites uses a `panel`, disc uses
`ImageWidget`) keep a sibling `MainMenuTitle` instead — stationary
title is acceptable there because those sections don't need
widget-stack scrolling.

The stock Categories widget title is suppressed by passing
`widget_header=""` at the `WidgetListCategories` call site (rather
than `visible=false`, which would hide the card panel too). The
CategoryLabel control still renders — it's just empty.

## Forking shared InfoWall layouts

`WidgetListPoster`, `WidgetListEpisodes`, `WidgetListSquare` reference
layout includes defined in `View_54_InfoWall.xml` that are *also* used
by the full-screen View 54 (movies/tvshows/episodes/music browser).
To change home-widget dimensions without touching View 54, fork the
layout: add `InfoWallMovieLayoutHome`, `InfoWallEpisodeLayoutHome`,
`InfoWallMusicLayoutHome` as new includes in that file and point the
home widget include at the `*Home` variant. All internal dimensions
(bg width/height/left/top, textbox, overlay, progress, rating offsets,
bordersize) must be edited together — they are hard-coded, not derived
from the slot width.

## Left-aligning widget category labels

`CategoryLabel` has a `posx` parameter (default 55). For home widgets,
pass `posx=82` so the label lines up with the first card's left edge
within the widget slot. Also pass `font=font13_w` for the home-widget
text size.

## Font conventions

Home-widget text uses `_w`-suffixed font variants (`font10_w`,
`font12_w`, `font13_w`, `font14_w`, `font25_narrow_w`, `font27_w`,
`font27_narrow_w`, `font20_title_w`, `font30_title_w`). Originally
introduced for per-variant scaling; now they're a single set of fixed
sizes.

The Main Menu Title uses `font_mainmenu`.

If you need another scaled sub-area, prefer a new suffix (e.g. `_xl`)
rather than reusing `_w`.

## List-highlight colour

`list_focus` (in every `colors/<theme>.xml`) is the colordiffuse used
for focused list items across the skin. Currently set to 60 % opaque
(alpha `99`) over each theme's accent hue, e.g. `99607D8B` in
`defaults.xml`. Replaces the older `button_focus` / `button_alt_focus`
references on `lists/focus.png`.

## Skin `<res>` and script-addon WindowXML overrides

`addon.xml` can declare a non-1080p logical coord space, e.g.
`<res width="2256" height="1269" aspect="16:9" default="true" folder="xml"/>`.
Skin XML is then authored in those units, which Kodi maps to the
physical display. Estuary-derived skins tolerate this with top-left
anchoring and relative sizing.

**Trap: forking a script-addon's WindowXMLDialog into the skin.** If
the skin ships a file with the same filename as a script addon's
window XML (e.g. `script-embuary-video.xml` matching
`script.embuary.info`'s movie-info dialog), Kodi prefers the skin's
copy. Two paths with different scaling semantics:

- **Addon's own** `resources/skins/default/1080i/foo.xml` → Kodi treats
  the `1080i` folder as a declared 1920×1080 coord system and scales
  the whole dialog to the skin's `<res>` space. Works at any res.
- **Skin's `xml/foo.xml`** → Kodi treats contents as already in the
  skin's coord space. Literal `<width>1920</width>` renders as 85 % of
  screen at 2256×1269 — dialog pins top-left, content clipped or
  undersized.

Rule: **don't fork script-addon WindowXMLs into the skin** unless
you're prepared to rescale them every time `<res>` changes. For mods
to an addon's dialog (extra menu items, theming), prefer contributing
upstream or letting the originating addon apply its own patch — e.g.
KodiSeerr's Advanced-settings "Inject request button into Embuary
info" action injects a seven-line `<item>` block plus an icon into
`script.embuary.info` directly, so embuary's auto-scaling still
applies.

**Diagnosing which file Kodi loaded.** Tail `kodi.log` while opening
the dialog and look for `Window Init (...)` lines — they print the
full path, revealing skin-override vs addon-original. Example from
the embuary debugging session:

```
Window Init (/.../skin.contuary/xml/script-embuary-video.xml)
Window Init (/.../script.embuary.info/resources/skins/default/1080i/script-embuary-person.xml)
```

The first is a skin override (won't scale), the second is the addon
original (auto-scales).
