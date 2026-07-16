# Neovim Config

This directory is the source of truth for `~/.config/nvim`. It's copied (not symlinked)
into place via the `update_dotfiles` tag in the Ansible playbook, or `scripts/update.sh`,
so changes here need a sync before they take effect live.

Leader key is `<space>` (set in `lua/config/lazy.lua`, and again redundantly in
`init.lua`). `maplocalleader` is `\` but nothing currently uses it.

## Global keymaps

Active in every buffer, all the time.

| Key | Mode | Action | File |
|---|---|---|---|
| `<C-h>` | n | Clear search highlight (`:nohlsearch`) | `init.lua` |
| `<leader>ff` | n | Telescope find files | `lua/config/telescope.lua` |
| `<leader>fg` | n | Telescope live grep | `lua/config/telescope.lua` |
| `<leader>fb` | n | Telescope buffers | `lua/config/telescope.lua` |
| `<leader>fh` | n | Telescope help tags | `lua/config/telescope.lua` |

## LSP keymaps

Buffer-local — only exist in buffers where an LSP client has attached (set in the
`LspAttach` autocmd in `lua/config/mason.lua`). Currently guaranteed for `jdtls`
(Java) and `clangd` (C/C++) via `ensure_installed`, and automatic for any other
server later installed through `:Mason`, since `automatic_enable = true`.

| Key | Mode | Action |
|---|---|---|
| `gd` | n | Go to definition |
| `gD` | n | Go to declaration |
| `gi` | n | Go to implementation |
| `gr` | n | List references |
| `K` | n | Hover documentation |
| `<leader>rn` | n | Rename symbol |
| `<leader>ca` | n, v | Code action |
| `[d` | n | Previous diagnostic |
| `]d` | n | Next diagnostic |
| `<leader>e` | n | Show line diagnostics |
| `<leader>q` | n | Diagnostics to location list |

## Commands

`:ClearMarks` — runs `delmarks! | delmarks A-Z 0-9`. Defined in `init.lua`, no key bound.

