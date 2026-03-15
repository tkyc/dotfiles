require('nvim-treesitter').setup {
  -- Directory to install parsers and queries to (prepended to `runtimepath` to have priority)
  install_dir = vim.fn.stdpath('data') .. '/site'
}

require('nvim-treesitter').install { "java", "cpp" }

vim.api.nvim_create_autocmd('FileType', {
  pattern = { 'java', 'cpp' },
  callback = function() vim.treesitter.start() end,
})

