"General settings
set number
set relativenumber
set hlsearch
set encoding=utf8
syntax enable

"Gruvbox
"set background=dark
"set t_Co=256
"syntax on
"colorscheme gruvbox

"Solarized --- Set terminal colors to solarized preset
"set background=dark
"colorscheme solarized
"set t_Co=16

"Indentation
filetype plugin indent on
set tabstop=4
set shiftwidth=4
set expandtab

"Autocomplete CoC
inoremap <expr> <Tab> pumvisible() ? "\<C-n>" : "\<Tab>"
inoremap <expr> <S-Tab> pumvisible() ? "\<C-p>" : "\<S-Tab>"
inoremap <expr> <cr> pumvisible() ? "\<C-y>" : "\<C-g>u\<CR>"

"Autocomplete for braces and quotes
inoremap " ""<left>
inoremap ' ''<left>
inoremap ( ()<left>
inoremap [ []<left>
inoremap { {}<left>
inoremap {<CR> {<CR>}<ESC>O
inoremap {;<CR> {<CR>};<ESC>O

"Row highlight in normal mode
set cul
:autocmd InsertEnter * set nocul
:autocmd insertLeave * set cul

"Key remaps and command macros
noremap <silent><esc> <esc>:noh<CR><esc>
map <C-h> :nohlsearch <CR>
inoremap ii <Esc>
map <C-n> :NERDTreeToggle <CR>

"Vim powerline enable
set rtp+=/home/tkyc/.vim/plugged/powerline/powerline/bindings/vim
set laststatus=2

"Plugins start --- vim-plug
call plug#begin('~/.vim/plugged')

Plug 'powerline/powerline'
Plug 'scrooloose/nerdtree'
Plug 'junegunn/fzf.vim'
Plug 'maxmellon/vim-jsx-pretty'
Plug 'sheerun/vim-polyglot'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'airblade/vim-gitgutter'
Plug 'ryanoasis/vim-devicons'

call plug#end()
