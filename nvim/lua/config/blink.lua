require('blink.cmp').setup({
  keymap = { preset = 'enter' },
  completion = {
    documentation = { auto_show = true },
  },
  sources = {
    default = { 'lsp', 'path', 'buffer' },
  },
})

vim.lsp.config('*', {
  capabilities = require('blink.cmp').get_lsp_capabilities(),
})
