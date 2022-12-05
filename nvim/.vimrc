"General settings
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
map <C-h> :nohlsearch <CR>
map <C-n> :NERDTreeToggle <CR>
map <Tab> :call TabKey()<CR>
inoremap ii <Esc>
nnoremap <SPACE> <Nop>
let mapleader=" " "Leader key is spacebar
noremap <silent><esc> <esc>:noh<CR><esc>
nnoremap <leader>ff <cmd>Telescope find_files<cr>
nnoremap <leader>fg <cmd>Telescope live_grep<cr>
nnoremap <leader>rr <cmd>CocRestart<cr><cr>



"Custom commands and functions
command Tab :normal i    
function TabKey()
    execute "Tab"
endfunction



"Vim powerline enable
set laststatus=2
set showtabline=2
let g:airline#extensions#whitespace#enabled=0 "Toggle whitespace check extension
let g:airline#extensions#tabline#enabled=1 "Toggle showing of tab panel, 0 = false 1 = true
let g:airline#extensions#tabline#tab_nr_type=1 "Configure individual tab display content
let g:airline#extensions#tabline#tab_min_count = 2 "Minimum number of tabs to appear in tab panel
let g:airline#extensions#tabline#buffer_min_count = 2 "Minimim number of buffers to appear in tab panel
 let g:airline#extensions#tabline#show_buffers = 0 "Toggle showing of buffers, 0 = false 1 = true
if !exists('g:airline_symbols')
    let g:airline_symbols={}
endif
"let g:airline_theme='powerlineish'
"let g:airline_theme='angr'
"let g:airline_theme='luna'
let g:airline_theme='minimalist'
let g:airline_symbols.linenr=''
let g:airline_symbols.maxlinenr=' col '



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



"Execute scripts on vim events
:autocmd VimLeave * !$HOME/Scripts/close-lsp.sh %



"Plugins start --- vim-plug is the plugin manager
call plug#begin('~/.vim/plugged')
"Plug 'maxmellon/vim-jsx-pretty'
"Plug 'sheerun/vim-polyglot'
"Plug 'christianchiarulli/nvcode-color-schemes.vim'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'scrooloose/nerdtree'
Plug 'junegunn/fzf.vim' "Install fzf and ripgrep for fzf to work in vim
Plug 'junegunn/fzf'
Plug 'airblade/vim-gitgutter'
Plug 'ryanoasis/vim-devicons'
Plug 'nvim-treesitter/nvim-treesitter' "https://github.com/nvim-treesitter/nvim-treesitter/issues/700
Plug 'nvim-lua/plenary.nvim'
Plug 'nvim-telescope/telescope.nvim'
call plug#end()
