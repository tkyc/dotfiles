-- nam: Google AI Mode inside Neovim (local plugin)
return {
  {
    "tkyc/nam",
    name = "nam",
    -- Install the Node backend dependency (puppeteer-core) on install/update.
    build = "cd backend && npm install",
    cmd = "Nam", -- lazy-load when :Nam (or :nam) is first used
    opts = {}, -- calls require("nam").setup({}); override options here
    config = function(_, opts)
      require("nam").setup(opts)
    end,
  },
}
