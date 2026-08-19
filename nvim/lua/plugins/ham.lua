-- ham: Google AI Mode inside Neovim (local plugin)
return {
  {
    dir = "/home/tkyc/repo/ham",
    name = "ham",
    -- Install the Node backend dependency (puppeteer-core) on install/update.
    build = "cd backend && npm install",
    cmd = "Ham", -- lazy-load when :Ham (or :ham) is first used
    opts = {}, -- calls require("ham").setup({}); override options here
    config = function(_, opts)
      require("ham").setup(opts)
    end,
  },
}
