"General settings
"Uncomment if vim is booting in replace mode
set noek
set number
set relativenumber
set hlsearch
set encoding=utf8
syntax enable



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
set pastetoggle=<C-p>



"Vim powerline enable
set laststatus=2
set showtabline=2
let g:airline#extensions#tabline#enabled=1
let g:airline#extensions#tabline#tab_nr_type=1
if !exists('g:airline_symbols')
    let g:airline_symbols={}
endif
"let g:airline_theme='powerlineish'
let g:airline_theme='angr'
let g:airline_symbols.linenr=''
let g:airline_symbols.maxlinenr=' '



"Git Gutter
set updatetime=250
"let g:gitgutter_max_signs = 500
"let g:gitgutter_map_keys = 0
"let g:gitgutter_override_sign_column_highlight = 0
highlight clear SignColumn
"highlight GitGutterAdd ctermfg=2
"highlight GitGutterChange ctermfg=3
"highlight GitGutterDelete ctermfg=1
"highlight GitGutterChangeDelete ctermfg=4



"Plugins start --- vim-plug is the plugin manager
call plug#begin('~/.vim/plugged')

Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'scrooloose/nerdtree'
"Install fzf and ripgrep for fzf to work in vim
Plug 'junegunn/fzf.vim'
Plug 'maxmellon/vim-jsx-pretty'
Plug 'sheerun/vim-polyglot'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'airblade/vim-gitgutter'
Plug 'ryanoasis/vim-devicons'

call plug#end()
