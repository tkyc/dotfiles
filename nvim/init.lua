require("config.lazy")
require("config.mason")
require("config.lualine")
require("config.tokyonight")
require("config.treesitter")
require("config.telescope")
require("config.blink")
require("config.gitsigns")

-- Colourscheme
vim.cmd [[
    colorscheme tokyonight-night
]]

-- Clear marks
local function clear_marks()
  vim.cmd('delmarks! | delmarks A-Z 0-9')
end

vim.api.nvim_create_user_command(
  'ClearMarks',
  clear_marks,
  {
    desc = 'Clear all marks'
  }
)

-- Preview .md file
local function preview_markdown()
  vim.cmd('term glow -w 150 %')
end

vim.api.nvim_create_user_command(
  'PreviewMarkdown',
  preview_markdown,
  {
    desc = 'Preview markdown file'
  }
)

-- Clear search highlight
local function clear_search_highlight()
    vim.cmd('nohlsearch')
end

vim.keymap.set('n', '<C-h>', clear_search_highlight, { desc = 'Clear search highlights' })

vim.opt.signcolumn = "yes"

-- Set leader key to spacebar
vim.g.mapleader = ' '

-- Relative line numbering
vim.opt.number = true
vim.opt.relativenumber = true

-- Four spaces for TAB
vim.o.tabstop = 4
vim.o.shiftwidth = 4
vim.o.expandtab = true
vim.o.softtabstop = 4

