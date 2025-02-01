#!/usr/bin/bash

while read urlpath; do
  array=($urlpath)
  url="${array[0]}"
  name="${array[1]}"

  echo "processing $url"
  if grep -Fxq "$url" downloaded.txt
  then 
    echo "already processed $url"
  else
    python ./make-whisper-cpp.py "$url" "$name"
  fi
done < "$1"
