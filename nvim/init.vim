"File belongs in ~/.config/nvim/init.vim

"Read in settings for neovim from .vimrc
set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath=&runtimepath
source ~/.vimrc

"Turn on nvim-treesitter
lua <<EOF
require'nvim-treesitter.configs'.setup {
    ensure_installed = {"java", "cpp", "c", "python", "javascript", "typescript", "lua"},
  highlight = {
    enable = true,
  },
}
EOF

"Configure colorscheme
colorscheme profile

source ~/.config/nvim/coc.vim
