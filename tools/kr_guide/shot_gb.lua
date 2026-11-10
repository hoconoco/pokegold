-- Headless mGBA screen test for the Game Boy ROMs (REA_repo tools/mgba-headless image: run.sh <rom> <lua> <sec>).
-- Environment:
--   OUT      file name prefix of the screenshots (default /w/shot_)
--   MASH     "from:to[:every]" — press A every `every` frames (default 40) between the frames (intro, new game talk)
--   KEYS     "frame:KEY[+KEY][:len] ..." — keys at exact frames (KEY = A B START SELECT UP DOWN LEFT RIGHT), len default 6
--   SHOTS    "frame,frame,..." — screenshots at these frames; SHOTEVERY=N also every N frames from SHOTFROM
--   WRITE8   "frame:addr:value,..." (hex addr/value) — poke RAM at that frame (test state: map, time of day)
--   ENDFRAME stop here
local OUT = os.getenv("OUT") or "/w/shot_"
local K = C.GBA_KEY  -- the same bit numbers on the Game Boy (A B SELECT START RIGHT LEFT UP DOWN)
local function parse_keys(s)
  local ks = {}
  for fr, k, n in (s or ""):gmatch("(%d+):([%a%+]+):?(%d*)") do
    local t = {}
    for name in k:gmatch("%a+") do t[#t + 1] = K[name] end
    ks[tonumber(fr)] = { keys = t, len = tonumber(n) or 6 }
  end
  return ks
end
local keys = parse_keys(os.getenv("KEYS"))
local shots = {}
for fr in (os.getenv("SHOTS") or ""):gmatch("%d+") do shots[tonumber(fr)] = true end
local every, from = tonumber(os.getenv("SHOTEVERY") or "0"), tonumber(os.getenv("SHOTFROM") or "0")
local m1, m2, me = (os.getenv("MASH") or "0:0"):match("(%d+):(%d+):?(%d*)")
m1, m2, me = tonumber(m1), tonumber(m2), tonumber(me) or 40
local writes = {}
for fr, ad, v in (os.getenv("WRITE8") or ""):gmatch("(%d+):(%x+):(%x+)") do
  writes[#writes + 1] = { tonumber(fr), tonumber(ad, 16), tonumber(v, 16) }
end
local ENDFRAME = tonumber(os.getenv("ENDFRAME") or "0")
local release_at = {}
callbacks:add("frame", function()
  local f = emu:currentFrame()
  for k, at in pairs(release_at) do if f >= at then emu:clearKey(k); release_at[k] = nil end end
  if f >= m1 and f < m2 and (f - m1) % me == 0 then emu:addKey(K.A); release_at[K.A] = f + 6 end
  local k = keys[f]
  if k then for _, x in ipairs(k.keys) do emu:addKey(x); release_at[x] = f + k.len end end
  for _, w in ipairs(writes) do if w[1] == f then emu:write8(w[2], w[3]) end end
  if shots[f] or (every > 0 and f >= from and (f - from) % every == 0) then
    emu:screenshot(OUT .. string.format("%06d", f) .. ".png")
  end
  if ENDFRAME > 0 and f >= ENDFRAME then
    emu:screenshot(OUT .. "end.png")
    os.exit(0)
  end
end)
