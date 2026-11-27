[![news-image-20261127](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/competitions/news-image-20261127)
[![rank](https://make.fun/badge/news-image-20261127/Zikri167/makefun-news-image-20261127/rank.svg)](https://make.fun/competitions/news-image-20261127)
[![reward](https://make.fun/badge/news-image-20261127/Zikri167/makefun-news-image-20261127/reward.svg)](https://make.fun/competitions/news-image-20261127)

# makefun-news-image-20261127

A program that draws the front page of a newspaper summing up the world's news of Friday, 27 November 2026, in a single 1024x1024 image. The lead story is the Iranian drone attack on Kuwait that killed two Italian workers; below it, three panels cover the U.S. Thanksgiving storm, the strike on the Jazan refinery in Saudi Arabia, and the killing of a senior Hamas official in Gaza. A strip reports the drawn third game of the World Chess Championship between Gukesh and Sindarov, and an IN BRIEF column lists seven more stories from the day, from the Cairo tanker fire to the Ebola outbreak in Congo. Everything is drawn procedurally in pure Python with a self-made bitmap font and a hand-built PNG encoder, so the output is byte-identical on every run.

## Run it

```sh
python3 main.py
```

This writes `entry.png` to `/output` by default. Set `MAKEFUN_OUTPUT_DIR` to write it somewhere else:

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

Built with [make.fun](https://make.fun/?ref=63s6rw9w).
