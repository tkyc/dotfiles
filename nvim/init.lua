require("config.lazy")
require("config.lualine")
require("config.tokyonight")

-- Makes Neovim transparent
vim.cmd [[
    highlight Normal guibg=none
    highlight NonText guibg=none
    highlight Normal ctermbg=none
    highlight NonText ctermbg=none
    colorscheme tokyonight-night
]]

