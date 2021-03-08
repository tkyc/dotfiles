"File belongs in ~/.config/nvim/init.vim

"Readin settings for neovim from .vimrc
set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath=&runtimepath
source ~/.vimrc

"Turn on nvim-treesitter
lua <<EOF
require'nvim-treesitter.configs'.setup {
  ensure_installed = "maintained",
  highlight = {
    enable = true,
  },
}
EOF

"Configure colorscheme
colorscheme profile
