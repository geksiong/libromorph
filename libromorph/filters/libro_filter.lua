-- libro_filter.lua: Pandoc Lua filter for LibroMorph
-- Supports: Ruby text (furigana), Tate-chu-yoko, Quizzes, Callouts, Dropcaps,
-- Index anchors, ABC music notation, Mermaid diagrams, chord diagrams, rhythm
-- grids, and writing-mode islands.

local is_epub = (FORMAT:match("^epub") ~= nil)
local quiz_counter = 0
local abc_counter = 0
local mermaid_counter = 0
local fretboard_counter = 0
local fretdrom_counter = 0
-- Directories of build-time rendered SVGs (<sha1>-<n>.svg), set by the builder
local abc_svg_dir = os.getenv("LIBROMORPH_ABC_SVG_DIR")
local mermaid_svg_dir = os.getenv("LIBROMORPH_MERMAID_SVG_DIR")
local fretboard_svg_dir = os.getenv("LIBROMORPH_FRETBOARD_SVG_DIR")
local fretdrom_svg_dir = os.getenv("LIBROMORPH_FRETDROM_SVG_DIR")

-- Helper: Convert inlines or blocks to plain text or HTML string
local function stringify(x)
  return pandoc.utils.stringify(x)
end

-- Callout definitions: icon and title
local callout_types = {
  note = { icon = "ℹ️", title = "Note" },
  tip = { icon = "💡", title = "Tip" },
  warning = { icon = "⚠️", title = "Warning" },
  caution = { icon = "🚨", title = "Caution" },
  info = { icon = "📌", title = "Information" },
  theorem = { icon = "📐", title = "Theorem" },
  definition = { icon = "📖", title = "Definition" },
  example = { icon = "🔍", title = "Example" },
  quote = { icon = "💬", title = "Notable Quote" }
}

-- Process Inline elements
function Inlines(inlines)
  -- Pre-pass: merge consecutive Str/Space runs into single Str tokens so that
  -- ruby patterns like {花間|huā jiān} (which Pandoc splits on the space inside
  -- the annotation) are reassembled before the pattern match.  After matching
  -- we re-split any leftover plain text back into Str/Space inlines.
  local merged = {}
  local buf = nil   -- current merged string, or nil
  for _, el in ipairs(inlines) do
    if el.t == 'Str' then
      buf = (buf or "") .. el.text
    elseif el.t == 'Space' then
      if buf ~= nil then
        buf = buf .. " "
      else
        table.insert(merged, el)
      end
    else
      if buf ~= nil then
        -- Trim any trailing space we accumulated that won't be part of a ruby
        table.insert(merged, pandoc.Str(buf))
        buf = nil
      end
      table.insert(merged, el)
    end
  end
  if buf ~= nil then
    table.insert(merged, pandoc.Str(buf))
  end

  -- Helper: re-split a plain string into Str / Space inlines, preserving
  -- leading/trailing spaces accurately.
  local function split_str(s)
    local parts = pandoc.Inlines({})
    -- Walk character by character grouping word vs space runs
    local i = 1
    local word_start = nil
    while i <= #s do
      local c = s:sub(i, i)
      if c == " " then
        if word_start then
          parts:insert(pandoc.Str(s:sub(word_start, i - 1)))
          word_start = nil
        end
        parts:insert(pandoc.Space())
      else
        if not word_start then word_start = i end
      end
      i = i + 1
    end
    if word_start then
      parts:insert(pandoc.Str(s:sub(word_start)))
    end
    return parts
  end

  local new_inlines = pandoc.Inlines({})

  for _, el in ipairs(merged) do
    if el.t == 'Str' then
      local text = el.text

      -- Check for Ruby notation: {漢字|かんじ} — ruby text may contain spaces
      -- (e.g. {花間|huā jiān}, {莊周|Zhuāng Zhōu})
      if text:find("{[^{}|]+|[^{}]+}") then
        local last_pos = 1
        for start_pos, base, ruby, end_pos in text:gmatch("()%{([^|{}]+)|([^{}]+)%}()") do
          if start_pos > last_pos then
            for _, part in ipairs(split_str(text:sub(last_pos, start_pos - 1))) do
              new_inlines:insert(part)
            end
          end
          local raw = string.format("<ruby>%s<rp>(</rp><rt>%s</rt><rp>)</rp></ruby>", base, ruby)
          new_inlines:insert(pandoc.RawInline('html', raw))
          last_pos = end_pos
        end
        if last_pos <= #text then
          for _, part in ipairs(split_str(text:sub(last_pos))) do
            new_inlines:insert(part)
          end
        end

      -- Check for TCY notation: {tcy:42}
      elseif text:find("{tcy:[^}]+}") then
        local last_pos = 1
        for start_pos, val, end_pos in text:gmatch("()%{tcy:%s*([^{}]+)%}()") do
          if start_pos > last_pos then
            new_inlines:insert(pandoc.Str(text:sub(last_pos, start_pos - 1)))
          end
          local raw = string.format('<span class="tcy">%s</span>', val)
          new_inlines:insert(pandoc.RawInline('html', raw))
          last_pos = end_pos
        end
        if last_pos <= #text then
          new_inlines:insert(pandoc.Str(text:sub(last_pos)))
        end

      else
        new_inlines:insert(el)
      end

    elseif el.t == 'Span' then
      -- Explicit Ruby span: [base]{.ruby ruby="かんじ"} or [base]{ruby="かんじ"} or [base]{rt="かんじ"}
      if el.attributes.ruby or el.attributes.rt or el.classes:includes('ruby') then
        local ruby_text = el.attributes.ruby or el.attributes.rt or ""
        local base_text = pandoc.utils.stringify(el.content)
        local raw = string.format("<ruby>%s<rp>(</rp><rt>%s</rt><rp>)</rp></ruby>", base_text, ruby_text)
        new_inlines:insert(pandoc.RawInline('html', raw))

      -- TCY span: [42]{.tcy}
      elseif el.classes:includes('tcy') then
        local val = pandoc.utils.stringify(el.content)
        local raw = string.format('<span class="tcy">%s</span>', val)
        new_inlines:insert(pandoc.RawInline('html', raw))

      -- Dropcap span: [O]{.dropcap}
      elseif el.classes:includes('dropcap') then
        local char = pandoc.utils.stringify(el.content)
        local raw = string.format('<span class="dropcap">%s</span>', char)
        new_inlines:insert(pandoc.RawInline('html', raw))

      -- Index span: [term]{.index id="..."}
      elseif el.classes:includes('index') then
        local id_attr = el.identifier or el.attributes.id or ""
        local entry = el.attributes.entry or el.attributes["index-entry"] or stringify(el.content)
        local raw_open = string.format('<span class="index-term" data-entry="%s"%s>',
          entry:gsub('"', '&quot;'),
          id_attr ~= "" and (' id="' .. id_attr .. '"') or ""
        )
        new_inlines:insert(pandoc.RawInline('html', raw_open))
        for _, sub in ipairs(el.content) do
          new_inlines:insert(sub)
        end
        new_inlines:insert(pandoc.RawInline('html', '</span>'))

      else
        new_inlines:insert(el)
      end

    else
      new_inlines:insert(el)
    end
  end

  return new_inlines
end

-- Helper: Escape text for embedding in HTML content or attribute values
local function html_escape(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

-- Helper: Image blocks for the SVGs pre-rendered from `text` into `svg_dir`
-- (files <sha1(text)>-1.svg, -2.svg, ...); empty if none were rendered
local function rendered_svg_images(svg_dir, text, alt, class)
  local images = {}
  if not svg_dir then return images end
  local digest = pandoc.utils.sha1(text)
  local n = 1
  while true do
    local path = svg_dir .. "/" .. digest .. "-" .. n .. ".svg"
    local f = io.open(path, "r")
    if not f then break end
    f:close()
    table.insert(images, pandoc.Plain({
      pandoc.Image({ pandoc.Str(alt) }, path, "", pandoc.Attr("", { class }))
    }))
    n = n + 1
  end
  return images
end

-- ABC Music Notation
local function abc_block(block)
  abc_counter = abc_counter + 1
  local abc_id = block.identifier ~= "" and block.identifier or ("abc-score-" .. tostring(abc_counter))
  local abc_text = block.text
  local escaped = html_escape(abc_text)

  -- Extract title from the ABC "T:" header field (must start a line)
  local title = ("\n" .. abc_text):match("\nT:%s*([^\n]-)%s*\n")
    or ("\n" .. abc_text):match("\nT:%s*(.-)%s*$")
  local title_attr = (title and title ~= "") and string.format(' data-title="%s"', html_escape(title)) or ""

  if is_epub then
    -- EPUB: Most reading systems don't run scripts, so use the SVGs the
    -- builder pre-rendered for this score (one image per tune/page).
    local alt = title and ("Music score: " .. title) or "Music score"
    local images = rendered_svg_images(abc_svg_dir, abc_text, alt, "abc-svg")
    if #images > 0 then
      return pandoc.Div(images, pandoc.Attr(abc_id, { "abc-score", "abc-score-epub" }))
    end

    -- No rendered SVG available: show the raw notation in a styled block
    -- (titled via data-title).
    local out = string.format(
      '<div class="abc-score abc-score-epub" id="%s"%s>\n' ..
      '<pre class="abc-source"><code>%s</code></pre>\n' ..
      '</div>',
      abc_id, title_attr, escaped
    )
    return pandoc.RawBlock('html', out)
  else
    -- HTML website: Render client-side with abcjs
    -- The ABC source is stored in a <script> tag (type=text/vnd.abc) so it
    -- won't be displayed, and abc.js picks it up for rendering. "</" is
    -- split so the notation can never terminate the script element early.
    local script_text = abc_text:gsub("</", "<\\/")
    local out = string.format(
      '<div class="abc-score" id="%s"%s>\n' ..
      '<div class="abc-render"></div>\n' ..
      '<script type="text/vnd.abc">%s</script>\n' ..
      '<details class="abc-source-toggle">\n' ..
      '  <summary>View ABC Source</summary>\n' ..
      '  <pre class="abc-source"><code>%s</code></pre>\n' ..
      '</details>\n' ..
      '</div>',
      abc_id, title_attr, script_text, escaped
    )
    return pandoc.RawBlock('html', out)
  end
end

-- Mermaid Diagrams
local function mermaid_block(block)
  mermaid_counter = mermaid_counter + 1
  local diagram_id = block.identifier ~= "" and block.identifier or ("mermaid-diagram-" .. tostring(mermaid_counter))
  local text = block.text
  local alt = block.attributes["alt"] or "Diagram"
  local alt_attr = string.format(' aria-label="%s"', html_escape(alt))

  if is_epub then
    -- EPUB: use the SVG the builder pre-rendered for this diagram
    local images = rendered_svg_images(mermaid_svg_dir, text, alt, "mermaid-svg")
    if #images > 0 then
      return pandoc.Div(images, pandoc.Attr(diagram_id, { "mermaid-diagram", "mermaid-diagram-epub" }))
    end

    -- No rendered SVG available: show the diagram source
    return pandoc.RawBlock('html', string.format(
      '<div class="mermaid-diagram mermaid-diagram-epub" id="%s">\n' ..
      '<pre class="mermaid-source"><code>%s</code></pre>\n' ..
      '</div>',
      diagram_id, html_escape(text)
    ))
  end

  -- HTML website: Render client-side with mermaid.js (see js/mermaid-init.js).
  -- Like ABC, the source lives in a non-executed <script> with "</" split.
  return pandoc.RawBlock('html', string.format(
    '<div class="mermaid-diagram" id="%s" role="img"%s>\n' ..
    '<div class="mermaid-render"></div>\n' ..
    '<script type="text/x-mermaid">%s</script>\n' ..
    '</div>',
    diagram_id, alt_attr, (text:gsub("</", "<\\/"))
  ))
end

-- Chord Diagrams (fretted instruments)
--
-- Each non-blank line defines one chord:  NAME FRETS [fingers=...] [base=N] [barre=N]
--   FRETS   one entry per string, lowest string first: x = muted, 0 = open,
--           1-9 = fret; separate with commas for frets >= 10 (x,10,12,12,12,10)
--   fingers same layout as FRETS (0, x or - = none; T = thumb); strings sharing
--           a finger on the same fret are drawn as a barre
--   base    fret number of the top row (default: 1, or the lowest fretted
--           note when the chord doesn't fit in the first four frets)
--   barre   draw a barre on this fret, from the first string fretted there
-- The number of strings is taken from FRETS (6 = guitar, 4 = ukulele, ...).
-- A colon after NAME is optional. Diagrams are drawn as SVG right here, so
-- no external renderer is needed for HTML or EPUB.

local function parse_fret_list(s)
  local list = {}
  if s:find(",") then
    for item in (s .. ","):gmatch("([^,]*),") do table.insert(list, item) end
  else
    for ch in s:gmatch(".") do table.insert(list, ch) end
  end
  return list
end

local function parse_chord_line(line)
  local tokens = {}
  for tok in line:gmatch("%S+") do table.insert(tokens, tok) end
  local name = table.remove(tokens, 1)
  if name:sub(-1) == ":" and #name > 1 then
    name = name:sub(1, -2)
  elseif tokens[1] == ":" then
    table.remove(tokens, 1)
  end
  if #tokens == 0 then
    return nil, string.format("chord '%s' has no frets", name)
  end

  local chord = { name = name, frets = {}, fingers = {} }
  for i, f in ipairs(parse_fret_list(table.remove(tokens, 1))) do
    local lf = f:lower()
    if lf == "x" then
      chord.frets[i] = "x"
    elseif lf:match("^%d+$") then
      chord.frets[i] = tonumber(lf)
    else
      return nil, string.format("chord '%s': invalid fret '%s' (use x, 0 or a fret number)", name, f)
    end
  end
  if #chord.frets < 2 or #chord.frets > 12 then
    return nil, string.format("chord '%s' must have between 2 and 12 strings", name)
  end

  for _, tok in ipairs(tokens) do
    local key, value = tok:match("^(%a+)=(.+)$")
    key = key and key:lower()
    if key == "fingers" then
      local fingers = parse_fret_list(value)
      if #fingers ~= #chord.frets then
        return nil, string.format("chord '%s': fingers has %d entries but there are %d strings",
          name, #fingers, #chord.frets)
      end
      for i, f in ipairs(fingers) do
        if f ~= "0" and f ~= "x" and f ~= "X" and f ~= "-" then chord.fingers[i] = f end
      end
    elseif (key == "base" or key == "barre") and value:match("^%d+$") and tonumber(value) >= 1 then
      chord[key] = tonumber(value)
    else
      return nil, string.format("chord '%s': unknown option '%s'", name, tok)
    end
  end
  return chord
end

local function parse_chords(text)
  local chords = {}
  for line in (text .. "\n"):gmatch("([^\n]*)\n") do
    if line:match("%S") then
      local chord, err = parse_chord_line(line)
      if not chord then return nil, err end
      table.insert(chords, chord)
    end
  end
  if #chords == 0 then return nil, "no chords defined" end
  return chords
end

local function chord_description(chord)
  local frets = {}
  for i, f in ipairs(chord.frets) do frets[i] = tostring(f) end
  return string.format("%s chord: %s", chord.name, table.concat(frets, " "))
end

-- Renders one chord as a standalone SVG document. `fg` is the line/dot color
-- (currentColor inline in HTML; a fixed color in EPUB images) and finger
-- numbers use class "chord-finger" so page CSS can recolor them.
local function chord_svg(chord, fg)
  local n = #chord.frets
  local SX, FY, R = 16, 20, 6.5       -- string spacing, fret spacing, dot radius
  local LEFT, RIGHT, TOP = 26, 14, 44 -- padding (left leaves room for the fret label)

  local min_f, max_f = nil, 0
  for _, f in ipairs(chord.frets) do
    if f ~= "x" and f > 0 then
      min_f = (min_f and math.min(min_f, f)) or f
      max_f = math.max(max_f, f)
    end
  end
  local base = chord.base or ((max_f <= 4 or not min_f) and 1 or min_f)
  local rows = math.max(4, max_f - base + 1)

  local grid_w = (n - 1) * SX
  local width = math.max(LEFT + grid_w + RIGHT, utf8.len(chord.name) * 10 + 16)
  local x0 = (width - grid_w) / 2 + (LEFT - RIGHT) / 2
  local height = TOP + rows * FY + 10
  local function sx(i) return x0 + (i - 1) * SX end
  local function fy(f) return TOP + (f - base + 0.5) * FY end
  local function num(v) return string.format("%g", math.floor(v * 10 + 0.5) / 10) end

  local out = {}
  local function add(fmt, ...) table.insert(out, string.format(fmt, ...)) end
  local desc = html_escape(chord_description(chord))

  add('<svg xmlns="http://www.w3.org/2000/svg" class="chord-svg" width="%s" height="%s" viewBox="0 0 %s %s" ' ..
      'role="img" aria-label="%s" font-family="Helvetica, Arial, sans-serif">',
      num(width), num(height), num(width), num(height), desc)
  add('<title>%s</title>', desc)
  add('<text x="%s" y="18" text-anchor="middle" font-size="16" font-weight="bold" fill="%s">%s</text>',
      num(x0 + grid_w / 2), fg, html_escape(chord.name))

  -- Strings and frets
  for i = 1, n do
    add('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>',
        num(sx(i)), TOP, num(sx(i)), TOP + rows * FY, fg)
  end
  for r = 0, rows do
    add('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>',
        num(x0), TOP + r * FY, num(x0 + grid_w), TOP + r * FY, fg)
  end
  if base == 1 then
    add('<rect x="%s" y="%s" width="%s" height="4" fill="%s"/>', num(x0 - 0.5), TOP - 4, num(grid_w + 1), fg)
  else
    add('<text x="%s" y="%s" text-anchor="end" font-size="11" fill="%s">%dfr</text>',
        num(x0 - 7), num(fy(base) + 4), fg, base)
  end

  -- Barres: an explicit barre= fret, plus strings sharing a finger on one fret
  local barred = {}
  local barres = {}
  if chord.barre then
    for i = 1, n do
      if chord.frets[i] == chord.barre then
        table.insert(barres, { fret = chord.barre, from = i, to = n, finger = chord.fingers[i] })
        break
      end
    end
  end
  local groups = {}
  for i = 1, n do
    local finger, f = chord.fingers[i], chord.frets[i]
    if finger and f ~= "x" and f > 0 then
      local key = finger .. "@" .. f
      if groups[key] then
        groups[key].to = i
      else
        groups[key] = { fret = f, from = i, to = i, finger = finger }
        table.insert(groups, groups[key])
      end
    end
  end
  for _, g in ipairs(groups) do
    if g.to > g.from then table.insert(barres, g) end
  end
  for _, b in ipairs(barres) do
    if b.fret >= base and b.fret < base + rows then
      add('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>',
          num(sx(b.from) - R), num(fy(b.fret) - R), num(sx(b.to) - sx(b.from) + 2 * R), num(2 * R), num(R), fg)
      for i = b.from, b.to do
        if chord.frets[i] == b.fret then barred[i] = true end
      end
      if b.finger then
        add('<text x="%s" y="%s" text-anchor="middle" font-size="10" font-weight="bold" ' ..
            'class="chord-finger" fill="#fff">%s</text>',
            num(sx(b.from)), num(fy(b.fret) + 3.5), html_escape(b.finger))
      end
    end
  end

  -- Open/muted markers and fretted notes
  for i, f in ipairs(chord.frets) do
    local x = sx(i)
    if f == "x" then
      add('<path d="M%s %sL%s %sM%s %sL%s %s" stroke="%s" stroke-width="1.5"/>',
          num(x - 4), TOP - 15, num(x + 4), TOP - 7, num(x + 4), TOP - 15, num(x - 4), TOP - 7, fg)
    elseif f == 0 then
      add('<circle cx="%s" cy="%s" r="4" fill="none" stroke="%s" stroke-width="1.5"/>', num(x), TOP - 11, fg)
    elseif not barred[i] and f >= base and f < base + rows then
      add('<circle cx="%s" cy="%s" r="%s" fill="%s"/>', num(x), num(fy(f)), num(R), fg)
      if chord.fingers[i] then
        add('<text x="%s" y="%s" text-anchor="middle" font-size="10" font-weight="bold" ' ..
            'class="chord-finger" fill="#fff">%s</text>', num(x), num(fy(f) + 3.5), html_escape(chord.fingers[i]))
      end
    end
  end

  table.insert(out, '</svg>')
  return table.concat(out)
end

local chord_counter = 0

local function chord_block(block)
  chord_counter = chord_counter + 1
  local block_id = block.identifier ~= "" and block.identifier or ("chord-diagrams-" .. tostring(chord_counter))
  local chords, err = parse_chords(block.text)

  if not chords then
    io.stderr:write("[LibroMorph] Warning: chord diagram block '" .. block_id .. "': " .. err .. "\n")
    return pandoc.RawBlock('html', string.format(
      '<div class="chord-diagrams chord-diagrams-error" id="%s">\n' ..
      '<p class="chord-error">⚠ Could not draw chord diagram: %s</p>\n' ..
      '<pre class="chord-source"><code>%s</code></pre>\n' ..
      '</div>',
      block_id, html_escape(err), html_escape(block.text)
    ))
  end

  if is_epub then
    -- EPUB: embed each diagram as an SVG image (via the media bag), since
    -- inline SVG and currentColor aren't reliable across reading systems
    local images = {}
    for _, chord in ipairs(chords) do
      local svg = chord_svg(chord, "#1e1e1e")
      local path = "chord-" .. pandoc.utils.sha1(svg) .. ".svg"
      pandoc.mediabag.insert(path, "image/svg+xml", svg)
      table.insert(images, pandoc.Image({ pandoc.Str(chord_description(chord)) }, path, "",
        pandoc.Attr("", { "chord-svg" })))
      table.insert(images, pandoc.Space())
    end
    table.remove(images)
    return pandoc.Div({ pandoc.Plain(images) }, pandoc.Attr(block_id, { "chord-diagrams", "chord-diagrams-epub" }))
  end

  -- HTML website: inline SVG drawn in currentColor so it follows the color mode
  local parts = {}
  for _, chord in ipairs(chords) do
    table.insert(parts, '<div class="chord-diagram">' .. chord_svg(chord, "currentColor") .. '</div>')
  end
  return pandoc.RawBlock('html', string.format(
    '<div class="chord-diagrams" id="%s">\n%s\n</div>', block_id, table.concat(parts, "\n")
  ))
end

-- Rhythm grids: box notation for counts, cycles and accent patterns.
--
--   ```rhythm-grid
--   Count:   12  1  2 | 3  4  5 | 6  7 | 8  9 |10 11
--   Map A:    X  .  . | X  .  . | X  . | X  . | X  .
--   ```
--
-- Every line is "Label: cells". The first line is the header (the counts);
-- other rows are matched to its columns by character position, so grids
-- written for a monospaced font keep their meaning. `|` in the header marks
-- a group boundary. Cells: X strong, x light, o muted/open, . empty,
-- - held from the previous cell; anything else (F, Bb, "next cycle") is text.
-- Text past the last column becomes a note at the end of the row.
-- Add `.circle` to draw a cycle as a clock face instead of a table.
local rhythm_grid_counter = 0

local RG_SYMBOLS = {
  X = { class = "rg-strong", mark = "●", name = "strong" },
  x = { class = "rg-light", mark = "●", name = "light" },
  o = { class = "rg-muted", mark = "○", name = "muted" },
}

local function utf8_chars(s)
  local chars = {}
  for _, c in utf8.codes(s) do chars[#chars + 1] = utf8.char(c) end
  return chars
end

-- Split chars[from..] into tokens {text, s, e} at spaces; "|" positions are
-- returned separately.
local function rg_tokenize(chars, from)
  local tokens, bars = {}, {}
  local cur, start = nil, nil
  local function flush(i)
    if cur then
      tokens[#tokens + 1] = { text = cur, s = start, e = i - 1 }
      cur = nil
    end
  end
  for i = from, #chars do
    local c = chars[i]
    if c == " " or c == "\t" then
      flush(i)
    elseif c == "|" then
      flush(i)
      bars[#bars + 1] = i
    else
      if not cur then cur, start = "", i end
      cur = cur .. c
    end
  end
  flush(#chars + 1)
  return tokens, bars
end

local function rg_split_label(line)
  local chars = utf8_chars(line)
  for i, c in ipairs(chars) do
    if c == ":" then
      local label = table.concat(chars, "", 1, i - 1):gsub("^%s+", ""):gsub("%s+$", "")
      if label:match("^%a") then return label, chars, i + 1 end
      return nil
    end
  end
  return nil
end

local function rg_is_word(text)
  return utf8.len(text) >= 3 and text:match("^[%a(]") ~= nil
end

local function parse_rhythm_grid(text)
  local header, rows = nil, {}
  for line in (text .. "\n"):gmatch("(.-)\r?\n") do
    if line:match("%S") then
      local label, chars, from = rg_split_label(line)
      if not label then
        return nil, "line without a 'Label:' prefix: " .. line
      end
      local tokens, bars = rg_tokenize(chars, from)
      if not header then
        if #tokens == 0 then return nil, "the header row has no counts" end
        header = { label = label, cols = tokens, group_start = {} }
        for _, b in ipairs(bars) do
          for ci, col in ipairs(tokens) do
            if col.s > b then header.group_start[ci] = true; break end
          end
        end
      else
        rows[#rows + 1] = { label = label, tokens = tokens }
      end
    end
  end
  if not header then return nil, "empty grid" end
  if #rows == 0 then return nil, "no rows below the header" end

  local cols = header.cols
  local last_end = cols[#cols].e
  local function column_for(tok)
    local best, best_d = 1, math.huge
    for ci, col in ipairs(cols) do
      if tok.s <= col.e and tok.e >= col.s then return ci end
      local d = math.abs((tok.s + tok.e) / 2 - (col.s + col.e) / 2)
      if d < best_d then best, best_d = ci, d end
    end
    return best
  end

  for _, row in ipairs(rows) do
    -- Join multi-word phrases ("next cycle") separated by single spaces
    local phrases = {}
    for _, tok in ipairs(row.tokens) do
      local prev = phrases[#phrases]
      if prev and tok.s == prev.e + 2 and rg_is_word(prev.last) and rg_is_word(tok.text) then
        prev.text = prev.text .. " " .. tok.text
        prev.e, prev.last = tok.e, tok.text
      else
        phrases[#phrases + 1] = { text = tok.text, s = tok.s, e = tok.e, last = tok.text }
      end
    end
    row.cells, row.note = {}, nil
    local notes = {}
    for _, ph in ipairs(phrases) do
      if ph.s > last_end + 1 then
        notes[#notes + 1] = ph.text
      else
        local ci = column_for(ph)
        local span = 1
        if ph.text:find(" ") then
          local last_ci = column_for({ s = ph.e, e = ph.e })
          span = math.max(1, last_ci - ci + 1)
        end
        if row.cells[ci] then
          row.cells[ci].text = row.cells[ci].text .. " " .. ph.text
        else
          row.cells[ci] = { text = ph.text, span = span }
        end
      end
    end
    if #notes > 0 then row.note = table.concat(notes, " ") end
  end
  return { header = header, rows = rows }
end

local function rg_cell_kind(text)
  if text == "." then return "empty" end
  if text == "-" or text == "—" or text == "–" then return "hold" end
  if RG_SYMBOLS[text] then return "symbol" end
  return "text"
end

-- Spoken names for header counts: subdivisions take their beat ("3&").
local function rg_count_names(cols)
  local names, beat = {}, nil
  for ci, col in ipairs(cols) do
    if col.text:match("^%d") then
      beat = col.text
      names[ci] = col.text
    else
      names[ci] = (beat or "") .. col.text
    end
  end
  return names
end

local function rg_description(grid)
  local parts = {}
  local names = rg_count_names(grid.header.cols)
  for _, row in ipairs(grid.rows) do
    local by_kind, order = {}, { "strong", "light", "muted", "held" }
    for ci, col in ipairs(grid.header.cols) do
      local cell = row.cells[ci]
      if cell then
        local kind = rg_cell_kind(cell.text)
        local name = (kind == "symbol" and RG_SYMBOLS[cell.text].name) or (kind == "hold" and "held") or
          (kind == "text" and cell.text) or nil
        if name then
          if not by_kind[name] then
            by_kind[name] = {}
            if kind == "text" then order[#order + 1] = name end
          end
          table.insert(by_kind[name], names[ci])
        end
      end
    end
    local bits = {}
    for _, name in ipairs(order) do
      if by_kind[name] then
        bits[#bits + 1] = name .. " on " .. table.concat(by_kind[name], ", ")
      end
    end
    if #bits > 0 then parts[#parts + 1] = row.label .. ": " .. table.concat(bits, "; ") end
  end
  local counts = {}
  for _, col in ipairs(grid.header.cols) do counts[#counts + 1] = col.text end
  return "Rhythm grid, " .. grid.header.label:lower() .. " " .. table.concat(counts, " ") ..
    (#parts > 0 and (". " .. table.concat(parts, ". ")) or "")
end

local function rg_legend(used)
  local items = {}
  for _, key in ipairs({ "X", "x", "o" }) do
    if used[key] then
      local sym = RG_SYMBOLS[key]
      items[#items + 1] = '<span class="' .. sym.class .. '">' .. sym.mark .. '</span> ' .. sym.name
    end
  end
  if used.hold then items[#items + 1] = '<span class="rg-hold-sample"></span> held' end
  if #items == 0 then return "" end
  return '<p class="rg-legend">' .. table.concat(items, " · ") .. '</p>'
end

local function rhythm_grid_table(grid)
  local out, used = {}, {}
  local cols, group_start = grid.header.cols, grid.header.group_start
  local has_note = false
  for _, row in ipairs(grid.rows) do if row.note then has_note = true end end
  local function col_class(ci, base)
    return base .. (group_start[ci] and " rg-group-start" or "")
  end

  out[#out + 1] = '<table class="rg-table">'
  out[#out + 1] = '<thead><tr><th class="rg-label" scope="col">' .. html_escape(grid.header.label) .. '</th>'
  for ci, col in ipairs(cols) do
    out[#out + 1] = '<th class="' .. col_class(ci, "rg-count") .. '" scope="col">' .. html_escape(col.text) .. '</th>'
  end
  if has_note then out[#out + 1] = '<th class="rg-note" scope="col"></th>' end
  out[#out + 1] = '</tr></thead><tbody>'

  for _, row in ipairs(grid.rows) do
    out[#out + 1] = '<tr><th class="rg-label" scope="row">' .. html_escape(row.label) .. '</th>'
    local ci = 1
    while ci <= #cols do
      local cell = row.cells[ci]
      if not cell then
        out[#out + 1] = '<td class="' .. col_class(ci, "rg-cell rg-empty") .. '"></td>'
        ci = ci + 1
      else
        local kind = rg_cell_kind(cell.text)
        if kind == "empty" then
          out[#out + 1] = '<td class="' .. col_class(ci, "rg-cell rg-empty") .. '"></td>'
          ci = ci + 1
        elseif kind == "hold" then
          used.hold = true
          out[#out + 1] = '<td class="' .. col_class(ci, "rg-cell rg-hold") .. '"><span class="rg-hold-bar"></span></td>'
          ci = ci + 1
        elseif kind == "symbol" then
          local sym = RG_SYMBOLS[cell.text]
          used[cell.text] = true
          out[#out + 1] = '<td class="' .. col_class(ci, "rg-cell " .. sym.class) .. '" title="' .. sym.name .. '">' .. sym.mark .. '</td>'
          ci = ci + 1
        else
          local span = math.min(cell.span, #cols - ci + 1)
          local wordy = span > 1 or cell.text:match("%l%l%l") ~= nil
          local cls = col_class(ci, "rg-cell rg-text" .. (wordy and " rg-phrase" or ""))
          out[#out + 1] = '<td class="' .. cls .. '"' .. (span > 1 and (' colspan="' .. span .. '"') or "") ..
            '>' .. html_escape(cell.text) .. '</td>'
          ci = ci + span
        end
      end
    end
    if has_note then out[#out + 1] = '<td class="rg-note">' .. html_escape(row.note or "") .. '</td>' end
    out[#out + 1] = '</tr>'
  end
  out[#out + 1] = '</tbody></table>'
  return table.concat(out), used
end

-- Clock face: counts around the outside, one ring per row (outermost first),
-- ticks at group boundaries, the header's first count at the top.
local function rhythm_grid_circle_svg(grid, fg)
  local cols, n = grid.header.cols, #grid.header.cols
  local nrows = #grid.rows
  local R_LABEL, R_OUTER, RING_GAP = 132, 108, 26
  local cx, cy = 160, 152
  local legend_h = 18 * nrows + 8
  local W, H = 320, 304 + legend_h
  local function num(v) return string.format("%g", math.floor(v * 10 + 0.5) / 10) end
  local function pos(i, r)
    local a = -math.pi / 2 + 2 * math.pi * (i - 1) / n
    return cx + r * math.cos(a), cy + r * math.sin(a)
  end
  local out = {}
  local function add(fmt, ...) out[#out + 1] = string.format(fmt, ...) end
  local desc = html_escape(rg_description(grid))
  add('<svg xmlns="http://www.w3.org/2000/svg" class="rg-circle-svg" width="%d" height="%d" viewBox="0 0 %d %d" ' ..
      'role="img" aria-label="%s" font-family="Helvetica, Arial, sans-serif">', W, H, W, H, desc)
  add('<title>%s</title>', desc)
  local r_inner = R_OUTER - RING_GAP * (nrows - 1)
  -- rings
  for ri = 1, nrows do
    add('<circle cx="%d" cy="%d" r="%s" fill="none" stroke="%s" stroke-opacity="0.3" stroke-width="1"/>',
        cx, cy, num(R_OUTER - RING_GAP * (ri - 1)), fg)
  end
  -- group boundaries: radial ticks halfway before each group start; on a
  -- cycle the first count also starts a group
  local starts = {}
  for ci in pairs(grid.header.group_start) do starts[#starts + 1] = ci end
  if #starts > 0 and not grid.header.group_start[1] then starts[#starts + 1] = 1 end
  table.sort(starts)
  for _, ci in ipairs(starts) do
    local a = -math.pi / 2 + 2 * math.pi * (ci - 1.5) / n
    add('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2"/>',
        num(cx + (r_inner - 14) * math.cos(a)), num(cy + (r_inner - 14) * math.sin(a)),
        num(cx + (R_OUTER + 12) * math.cos(a)), num(cy + (R_OUTER + 12) * math.sin(a)), fg)
  end
  -- count labels
  for ci, col in ipairs(cols) do
    local x, y = pos(ci, R_LABEL)
    add('<text x="%s" y="%s" text-anchor="middle" dominant-baseline="central" font-size="15"%s fill="%s">%s</text>',
        num(x), num(y), ci == 1 and ' font-weight="bold"' or "", fg, html_escape(col.text))
  end
  -- marks
  for ri, row in ipairs(grid.rows) do
    local r = R_OUTER - RING_GAP * (ri - 1)
    for ci = 1, n do
      local x, y = pos(ci, r)
      local cell = row.cells[ci]
      local kind = cell and rg_cell_kind(cell.text) or "empty"
      if kind == "symbol" and cell.text == "X" then
        add('<circle cx="%s" cy="%s" r="9" fill="%s"/>', num(x), num(y), fg)
      elseif kind == "symbol" and cell.text == "x" then
        add('<circle cx="%s" cy="%s" r="5.5" fill="%s"/>', num(x), num(y), fg)
      elseif kind == "symbol" and cell.text == "o" then
        add('<circle cx="%s" cy="%s" r="7" fill="none" stroke="%s" stroke-width="2"/>', num(x), num(y), fg)
      elseif kind == "hold" then
        add('<circle cx="%s" cy="%s" r="3.5" fill="none" stroke="%s" stroke-width="1.5"/>', num(x), num(y), fg)
      elseif kind == "text" then
        add('<text x="%s" y="%s" text-anchor="middle" dominant-baseline="central" font-size="11" font-weight="bold" fill="%s">%s</text>',
            num(x), num(y), fg, html_escape(cell.text))
      else
        add('<circle cx="%s" cy="%s" r="1.8" fill="%s" fill-opacity="0.45"/>', num(x), num(y), fg)
      end
    end
  end
  -- ring legend
  for ri, row in ipairs(grid.rows) do
    local which = nrows == 1 and "" or (ri == 1 and "outer ring" or (ri == nrows and "inner ring" or "ring " .. ri)) .. ": "
    add('<text x="%d" y="%d" text-anchor="middle" font-size="13" fill="%s">%s%s</text>',
        cx, 304 + 18 * (ri - 1) + 4, fg, which, html_escape(row.label))
  end
  add('</svg>')
  return table.concat(out)
end

local function rhythm_grid_block(block)
  rhythm_grid_counter = rhythm_grid_counter + 1
  local block_id = block.identifier ~= "" and block.identifier or ("rhythm-grid-" .. rhythm_grid_counter)
  local grid, err = parse_rhythm_grid(block.text)
  if not grid then
    io.stderr:write("[LibroMorph] Warning: rhythm grid '" .. block_id .. "': " .. err .. "\n")
    return pandoc.RawBlock('html', string.format(
      '<div class="rhythm-grid rhythm-grid-error" id="%s">\n' ..
      '<p class="rg-error">⚠ Could not draw rhythm grid: %s</p>\n' ..
      '<pre class="rg-source"><code>%s</code></pre>\n</div>',
      block_id, html_escape(err), html_escape(block.text)))
  end
  local title = block.attributes["title"]
  local caption = title and ('<p class="rg-title">' .. html_escape(title) .. '</p>') or ""

  if block.classes:includes('circle') then
    if is_epub then
      local svg = rhythm_grid_circle_svg(grid, "#1e1e1e")
      local path = "rhythm-grid-" .. pandoc.utils.sha1(svg) .. ".svg"
      pandoc.mediabag.insert(path, "image/svg+xml", svg)
      local blocks = {}
      if title then blocks[#blocks + 1] = pandoc.RawBlock('html', caption) end
      blocks[#blocks + 1] = pandoc.Plain({ pandoc.Image({ pandoc.Str(rg_description(grid)) }, path, "",
        pandoc.Attr("", { "rg-circle-img" })) })
      return pandoc.Div(blocks, pandoc.Attr(block_id, { "rhythm-grid", "rhythm-grid-circle" }))
    end
    return pandoc.RawBlock('html', string.format(
      '<div class="rhythm-grid rhythm-grid-circle" id="%s">%s%s</div>',
      block_id, caption, rhythm_grid_circle_svg(grid, "currentColor")))
  end

  local tbl, used = rhythm_grid_table(grid)
  return pandoc.RawBlock('html', string.format(
    '<div class="rhythm-grid" id="%s" role="group" aria-label="%s">%s<div class="rg-scroll">%s</div>%s</div>',
    block_id, html_escape(rg_description(grid)), caption, tbl, rg_legend(used)))
end

-- Fretboard.js uses JSON; Fretdrom uses its native JSON5 input.
local function fretboard_block(block, engine)
  local count, svg_dir
  if engine == "fretdrom" then
    fretdrom_counter = fretdrom_counter + 1
    count, svg_dir = fretdrom_counter, fretdrom_svg_dir
  else
    fretboard_counter = fretboard_counter + 1
    count, svg_dir = fretboard_counter, fretboard_svg_dir
  end
  local block_id = block.identifier ~= "" and block.identifier or (engine .. "-diagram-" .. count)
  local alt = block.attributes["alt"] or (engine == "fretdrom" and "Fretted instrument diagram" or "Fretboard diagram")
  local images = is_epub and rendered_svg_images(svg_dir, block.text, alt, engine .. "-svg") or {}
  if #images > 0 then
    return pandoc.Div(images, pandoc.Attr(block_id, { "lm-fret-diagram", "lm-fret-diagram-epub" }))
  end
  if is_epub then
    return pandoc.RawBlock('html', string.format(
      '<div class="lm-fret-diagram lm-fret-diagram-epub" id="%s"><pre><code>%s</code></pre></div>',
      html_escape(block_id), html_escape(block.text)))
  end
  local script_type = engine == "fretdrom" and "fretdrom" or "application/json"
  local render_target = engine == "fretdrom" and "" or '<div class="lm-fretboard-render"></div>'
  return pandoc.RawBlock('html', string.format(
    '<div class="lm-fret-diagram lm-%s" id="%s" role="img" aria-label="%s">%s' ..
    '<script type="%s">%s</script></div>',
    engine, html_escape(block_id), html_escape(alt), render_target,
    script_type, block.text:gsub("</", "<\\/")))
end

-- Process CodeBlock elements (ABC music, Mermaid diagrams, chord diagrams)
function CodeBlock(block)
  if block.classes:includes('abc') then
    return abc_block(block)
  elseif block.classes:includes('mermaid') then
    return mermaid_block(block)
  elseif block.classes:includes('chord') or block.classes:includes('chords') then
    return chord_block(block)
  elseif block.classes:includes('fretboard') then
    return fretboard_block(block, "fretboard")
  elseif block.classes:includes('fretdrom') then
    return fretboard_block(block, "fretdrom")
  elseif block.classes:includes('rhythm-grid') then
    return rhythm_grid_block(block)
  end

  return block
end

-- Process Div elements (Quizzes, Callouts)
function Div(div)
  -- 1. Check for Quizzes
  if div.classes:includes('quiz') then
    quiz_counter = quiz_counter + 1
    local quiz_id = div.identifier
    if not quiz_id or quiz_id == "" then
      quiz_id = "quiz-" .. tostring(quiz_counter)
    end

    local title = div.attributes.title or ("Knowledge Check " .. tostring(quiz_counter))
    local question_blocks = {}
    local options = {}
    local explanation_blocks = {}
    local state = "question"

    for _, block in ipairs(div.content) do
      if block.t == 'BulletList' then
        state = "options"
        for idx, item in ipairs(block.content) do
          local is_correct = false
          local clean_item = pandoc.List({})

          -- Check item contents
          for b_idx, sub_block in ipairs(item) do
            if b_idx == 1 and sub_block.content then
              local inlines = pandoc.List({})
              local skip_next_space = false

              for inl_idx, inline in ipairs(sub_block.content) do
                if inl_idx == 1 and inline.t == 'Str' then
                  -- The Inlines pre-pass may have merged a trailing space into this
                  -- token (e.g. "☒ "), so trim before matching.
                  -- It may also carry the option's leading words ("☐ Plain words"),
                  -- so only the marker is removed and the remainder is kept.
                  local t, rest = inline.text:match("^(%S+)(.*)$")
                  local is_marker = true
                  if t == "☒" or t == "☑" or t == "[x]" or t == "[X]" or t == "(x)" or t == "(X)" then
                    is_correct = true
                  elseif t == "☐" or t == "[ ]" or t == "()" then
                    is_correct = false
                  else
                    is_marker = false
                    inlines:insert(inline)
                  end
                  if is_marker then
                    if rest == "" then
                      skip_next_space = true  -- marker was alone; drop the following Space
                    else
                      rest = rest:gsub("^%s+", "")
                      if rest ~= "" then inlines:insert(pandoc.Str(rest)) end
                    end
                  end
                elseif skip_next_space and inline.t == 'Space' then
                  skip_next_space = false
                else
                  inlines:insert(inline)
                end
              end
              clean_item:insert(pandoc[sub_block.t](inlines))
            else
              clean_item:insert(sub_block)
            end
          end

          -- Convert the item content to HTML inline representation
          local html_content = pandoc.write(pandoc.Pandoc(clean_item), 'html')
          -- strip outer <p> or <plain>
          html_content = html_content:gsub("^%s*<p>", ""):gsub("</p>%s*$", "")
          local plain_text = stringify(clean_item)

          table.insert(options, {
            index = idx,
            text = plain_text,
            html = html_content,
            correct = is_correct
          })
        end
        state = "explanation"
      elseif state == "options" or state == "explanation" then
        table.insert(explanation_blocks, block)
      else
        table.insert(question_blocks, block)
      end
    end

    local question_html = pandoc.write(pandoc.Pandoc(question_blocks), 'html')
    local explanation_html = ""
    if #explanation_blocks > 0 then
      explanation_html = pandoc.write(pandoc.Pandoc(explanation_blocks), 'html')
    else
      explanation_html = "<p>Excellent work testing your understanding!</p>"
    end

    local letters = {"A", "B", "C", "D", "E", "F", "G", "H"}

    if is_epub then
      -- EPUB output: Works cleanly with details/summary and accessible CSS
      local out = {}
      table.insert(out, string.format('<div class="quiz-card epub-quiz" id="%s">', quiz_id))
      table.insert(out, string.format('  <div class="quiz-header"><span class="quiz-badge">📝 %s</span></div>', title))
      table.insert(out, string.format('  <div class="quiz-question">%s</div>', question_html))
      table.insert(out, '  <div class="quiz-options-list">')

      local correct_label = ""
      for idx, opt in ipairs(options) do
        local ltr = letters[idx] or tostring(idx)
        local cls = opt.correct and "quiz-option is-correct-option" or "quiz-option"
        if opt.correct then
          correct_label = string.format("Option %s: %s", ltr, opt.text)
        end
        table.insert(out, string.format('    <div class="%s"><span class="quiz-opt-marker">(%s)</span> <span class="quiz-opt-text">%s</span></div>', cls, ltr, opt.html))
      end
      table.insert(out, '  </div>')

      table.insert(out, '  <details class="quiz-reveal">')
      table.insert(out, '    <summary class="quiz-reveal-btn">🔍 Reveal Answer &amp; Explanation</summary>')
      table.insert(out, '    <div class="quiz-explanation-box">')
      if correct_label ~= "" then
        table.insert(out, string.format('      <div class="quiz-correct-answer"><strong>✓ %s</strong></div>', correct_label))
      end
      table.insert(out, string.format('      <div class="quiz-explanation-text">%s</div>', explanation_html))
      table.insert(out, '    </div>')
      table.insert(out, '  </details>')
      table.insert(out, '</div>')

      return pandoc.RawBlock('html', table.concat(out, "\n"))
    else
      -- HTML website output: Rich interactive JS-driven widget
      local out = {}
      table.insert(out, string.format('<div class="quiz-card interactive-quiz" id="%s" data-quiz-id="%s">', quiz_id, quiz_id))
      table.insert(out, '  <div class="quiz-header">')
      table.insert(out, '    <span class="quiz-icon">📝</span>')
      table.insert(out, string.format('    <span class="quiz-badge">%s</span>', title))
      table.insert(out, '  </div>')
      table.insert(out, string.format('  <div class="quiz-question">%s</div>', question_html))
      table.insert(out, '  <div class="quiz-options" role="radiogroup">')

      for idx, opt in ipairs(options) do
        local ltr = letters[idx] or tostring(idx)
        table.insert(out, string.format(
          '    <button type="button" class="quiz-option-btn" data-correct="%s" data-index="%d">' ..
          '<span class="quiz-opt-letter">%s</span><span class="quiz-opt-content">%s</span>' ..
          '<span class="quiz-status-icon"></span></button>',
          tostring(opt.correct), idx - 1, ltr, opt.html
        ))
      end
      table.insert(out, '  </div>')

      table.insert(out, '  <div class="quiz-feedback" style="display: none;">')
      table.insert(out, '    <div class="quiz-feedback-banner"></div>')
      table.insert(out, string.format('    <div class="quiz-explanation-box">%s</div>', explanation_html))
      table.insert(out, '  </div>')

      table.insert(out, '  <div class="quiz-footer">')
      table.insert(out, '    <button type="button" class="quiz-retry-btn" style="display: none;">↺ Try Again</button>')
      table.insert(out, '  </div>')
      table.insert(out, '</div>')

      return pandoc.RawBlock('html', table.concat(out, "\n"))
    end
  end

  -- 2. Check for Writing Mode Islands (vertical / horizontal)
  if div.classes:includes('vertical') or div.classes:includes('horizontal') then
    local mode_class = div.classes:includes('vertical') and 'vertical' or 'horizontal'
    local inner_html = pandoc.write(pandoc.Pandoc(div.content), 'html')

    local out = string.format(
      '<div class="%s">\n%s\n</div>',
      mode_class, inner_html
    )
    return pandoc.RawBlock('html', out)
  end

  -- 3. Check for Admonitions / Callouts
  for ctype, info in pairs(callout_types) do
    if div.classes:includes(ctype) then
      local custom_title = div.attributes.title or info.title
      local icon = div.attributes.icon or info.icon
      local inner_html = pandoc.write(pandoc.Pandoc(div.content), 'html')

      local out = string.format(
        '<div class="callout callout-%s">\n' ..
        '  <div class="callout-header">\n' ..
        '    <span class="callout-icon">%s</span>\n' ..
        '    <span class="callout-title">%s</span>\n' ..
        '  </div>\n' ..
        '  <div class="callout-content">\n%s\n  </div>\n' ..
        '</div>',
        ctype, icon, custom_title, inner_html
      )
      return pandoc.RawBlock('html', out)
    end
  end

  return div
end
