-- Promotes fenced Divs to coloured panels: ::: key / why / say / warn / load
-- An optional title="..." attribute replaces the default label.
local boxes = {
  key  = {"keybg",  "keyrule",  "Top-3 number"},
  why  = {"whybg",  "whyrule",  "Why? What is it?"},
  say  = {"saybg",  "sayrule",  "Say it in the room"},
  warn = {"warnbg", "warnrule", "Trap"},
  load = {"loadbg", "loadrule", "Under load"},
}
function Div(el)
  for cls, spec in pairs(boxes) do
    if el.classes:includes(cls) then
      local label = el.attributes["title"] or spec[3]
      -- titles are plain text: escape LaTeX specials (%, ~, & … would break or vanish)
      label = label:gsub("([%%&#_%$%{%}])", "\\%1")
                   :gsub("~", "\\textasciitilde{}"):gsub("%^", "\\textasciicircum{}")
      table.insert(el.content, 1, pandoc.RawBlock("latex",
        "\\begin{sdbox}{" .. spec[1] .. "}{" .. spec[2] .. "}{" .. label .. "}"))
      table.insert(el.content, pandoc.RawBlock("latex", "\\end{sdbox}"))
      return el
    end
  end
end
