require('mason').setup({
  ui = { border = "single" },
})

require('mason-lspconfig').setup({
  ensure_installed = { 'jdtls', 'clangd' },
  automatic_enable = true,
})

vim.api.nvim_create_autocmd('LspAttach', {
  group = vim.api.nvim_create_augroup('UserLspAttach', { clear = true }),
  callback = function(event)
    local buf = event.buf

    vim.keymap.set('n', 'gd', vim.lsp.buf.definition, { buffer = buf, desc = 'LSP: Go to definition' })
    vim.keymap.set('n', 'gD', vim.lsp.buf.declaration, { buffer = buf, desc = 'LSP: Go to declaration' })
    vim.keymap.set('n', 'gi', vim.lsp.buf.implementation, { buffer = buf, desc = 'LSP: Go to implementation' })
    vim.keymap.set('n', 'gr', vim.lsp.buf.references, { buffer = buf, desc = 'LSP: List references' })
    vim.keymap.set('n', 'K', vim.lsp.buf.hover, { buffer = buf, desc = 'LSP: Hover documentation' })
    vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename, { buffer = buf, desc = 'LSP: Rename symbol' })
    vim.keymap.set({ 'n', 'v' }, '<leader>ca', vim.lsp.buf.code_action, { buffer = buf, desc = 'LSP: Code action' })
    vim.keymap.set('n', '[d', function() vim.diagnostic.jump({ count = -1, float = true }) end, { buffer = buf, desc = 'LSP: Previous diagnostic' })
    vim.keymap.set('n', ']d', function() vim.diagnostic.jump({ count = 1, float = true }) end, { buffer = buf, desc = 'LSP: Next diagnostic' })
    vim.keymap.set('n', '<leader>e', vim.diagnostic.open_float, { buffer = buf, desc = 'LSP: Show line diagnostics' })
    vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { buffer = buf, desc = 'LSP: Diagnostics to loclist' })
  end,
})

