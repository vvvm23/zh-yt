#!/bin/sh
whoami
p="~/.local/share/Anki2/User\ 1/collection.media/"

for mp3 in *.mp3; do
        cp "$mp3" "$p";
done
