require("config.lazy")
require("config.lualine")
require("config.tokyonight")
require("config.treesitter")
require("config.telescope")

-- Transparency
vim.cmd [[
    highlight Normal guibg=none
    highlight NonText guibg=none
    highlight Normal ctermbg=none
    highlight NonText ctermbg=none
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

-- Clear search highlight
local function clear_search_highlight()
    vim.cmd('nohlsearch')
end

vim.keymap.set('n', '<C-h>', clear_search_highlight, { desc = 'Clear search highlights' })

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

