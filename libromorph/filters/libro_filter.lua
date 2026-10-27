-- libro_filter.lua: Pandoc Lua filter for LibroMorph
-- Supports: Ruby text (furigana), Tate-chu-yoko, Quizzes, Callouts, Dropcaps, and Index anchors.

local is_epub = (FORMAT:match("^epub") ~= nil)
local quiz_counter = 0

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
                  local t = inline.text:match("^%S+")  -- leading non-space token
                  local has_trailing_space = inline.text:find(" ")
                  if t == "☒" or t == "☑" or t == "[x]" or t == "[X]" or t == "(x)" or t == "(X)" then
                    is_correct = true
                    skip_next_space = not has_trailing_space  -- only skip next Space token if not already consumed
                  elseif t == "☐" or t == "[ ]" or t == "()" then
                    is_correct = false
                    skip_next_space = not has_trailing_space
                  else
                    inlines:insert(inline)
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

  -- 2. Check for Admonitions / Callouts
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
