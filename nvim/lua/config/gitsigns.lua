require('gitsigns').setup({
  on_attach = function(bufnr)
    local gitsigns = require('gitsigns')

    local function map(mode, l, r, opts)
      opts = opts or {}
      opts.buffer = bufnr
      vim.keymap.set(mode, l, r, opts)
    end

    -- Navigation
    map('n', ']c', function()
      if vim.wo.diff then
        vim.cmd.normal({ ']c', bang = true })
      else
        gitsigns.nav_hunk('next')
      end
    end, { desc = 'Gitsigns: Next hunk' })

    map('n', '[c', function()
      if vim.wo.diff then
        vim.cmd.normal({ '[c', bang = true })
      else
        gitsigns.nav_hunk('prev')
      end
    end, { desc = 'Gitsigns: Previous hunk' })

    -- Actions
    map('n', '<leader>hs', gitsigns.stage_hunk, { desc = 'Gitsigns: Stage hunk' })
    map('n', '<leader>hr', gitsigns.reset_hunk, { desc = 'Gitsigns: Reset hunk' })
    map('n', '<leader>hp', gitsigns.preview_hunk, { desc = 'Gitsigns: Preview hunk' })
    map('n', '<leader>hb', function() gitsigns.blame_line({ full = true }) end, { desc = 'Gitsigns: Blame line' })
    map('n', '<leader>hd', gitsigns.diffthis, { desc = 'Gitsigns: Diff this' })
  end,
})
