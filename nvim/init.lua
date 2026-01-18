require("config.lazy")
require("config.lualine")
require("config.tokyonight")
require("config.treesitter")

-- Transparency
vim.cmd [[
    highlight Normal guibg=none
    highlight NonText guibg=none
    highlight Normal ctermbg=none
    highlight NonText ctermbg=none
    colorscheme tokyonight-night
]]

-- Relative line numbering
vim.opt.number = true
vim.opt.relativenumber = true

-- Four spaces for TAB
vim.o.tabstop = 4
vim.o.shiftwidth = 4
vim.o.expandtab = true
vim.o.softtabstop = 4

