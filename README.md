# nest-fishtank

An ambient aquarium for a Google Nest Hub: one self-contained `tank.html` (canvas, no external assets), cast to the Hub and kept alive.

## Preview locally

```sh
python3 -m http.server 8765
open http://localhost:8765/preview.html
```

`preview.html` frames the tank at 1024×600 (Hub) or 1280×800 (Hub Max) and lets you scrub the day/night clock.

## tank.html options

| Param | Default | |
|---|---|---|
| `fps` | 30 | Frame-rate cap |
| `dpr` | 2 | Max device-pixel-ratio to render at (`dpr=1` is cheapest) |
| `hour` | live | Pin the day/night clock, e.g. `hour=21.5` |
| `tz` | `Australia/Sydney` | Timezone for day/night |
| `lite` | off | Skip light rays and caustics (for slow devices) |
| `debug` | off | Show FPS |
| `reload` | off | Hard-reload every N hours |
| `clock` | `12` | Clock style: `12`, `24`, or `off` |

## Hosting

GitHub Pages from `main` on [nullaware/nest-fishtank](https://github.com/nullaware/nest-fishtank):
<https://nullaware.github.io/nest-fishtank/tank.html>. Push to `main` to update.

## Casting

```sh
uv tool install catt                # or: pip install catt
catt scan                           # find your Hub's name; use it in place of "My Nest Hub"
catt -d "My Nest Hub" cast_site https://nullaware.github.io/nest-fishtank/tank.html
catt -d "My Nest Hub" stop
```

`cast_site` uses the DashCast receiver, which shows the page full-screen.

## Keep-alive (macOS launchd)

`keepalive.py` runs every 2 minutes. Between 7am and 10pm Sydney time it casts the tank once the Hub has been idle for 5 minutes (`--grace`), so it won't jump in while you're using the touchscreen. It leaves other casts (music, video) alone. Outside those hours it stops the tank.

```sh
./install-launchd.sh                                  # defaults: "My Nest Hub", 7–22
./install-launchd.sh --start 6.5 --end 23 --device "My Nest Hub"
./install-launchd.sh --uninstall
tail -f ~/Library/Logs/nest-fishtank.log
```

The Mac has to be awake and on the same network as the Hub; launchd doesn't run jobs while the Mac sleeps.
