import youtube_dl

import re
import argparse
import subprocess
import pinyin
from typing import List, Tuple, Dict
from tqdm import tqdm
from pathlib import Path
import csv

def load_file(path: str):
    with open(path, mode='r') as f:
        url, *entries = f.readlines()
        url, entries = url.rstrip(), [e.rstrip() for e in entries]
    return url, entries

def parse_entries(entries: List[str]) -> List[Tuple[str, List[str], float, float]]:
    entries = list(csv.reader(entries))
    
    output_entries = []
    for e in entries:
        if len(e) > 3:
            s, *definitions, start, end = e
            output_entries.append((s, *definitions, float(start), float(end)))
        s, start, end = e
        output_entries.append((s, [], float(start), float(end)))

    return output_entries

def md_to_html_bold(entries: List[Tuple[str, List[str], float, float]]):
    match = r'\*\*(.+?)\*\*'
    replace = r'<b>\1</b>'
    return [(re.sub(match, replace, s), list(set(re.findall(match, s))), *_) for s, *_ in entries]

def download_audio(url: str, opts: Dict[str, str] = {}, codec: str = 'mp3'):
    audio_opts = {
        'download-archive': 'downloaded.txt',
        'format': 'bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec,
            'preferredquality': '192',
        }],
    }
    opts.update(audio_opts)
    with youtube_dl.YoutubeDL({'format': 'mp4'}) as ydl:
        res = ydl.extract_info(url)

    with open('downloaded.txt', mode='a') as f:
        f.write(f"{url}\n")

    return res

def convert_audio(title: str, ext: str = 'mp3'):
    command = ["ffmpeg", "-y", "-i", title + '.mp4', "-q:a", "0", "-map", "a", title + f".{ext}"]
    subprocess.call(command)

def get_screenshot(title: str, time: float, out_name):
    command = ["ffmpeg", "-y", "-ss", str(time), "-i", title + '.mp4', "-frames:v", "1", "-q:v", "2", out_name + ".jpg"]
    subprocess.call(command)

def create_clip(start_time: float, end_time: float, in_file: str, out_file: str):
    length = end_time - start_time
    command = ['ffmpeg', "-y", '-i', in_file, '-ss', str(start_time), '-t', str(length), out_file]
    subprocess.call(command)

def create_line(sentence, words, definitions, audio_path, img_path):
    pinyins = [pinyin.get(w) for w in words] + ['']*(5 - len(words))
    words = words + ['']*(5 - len(words))
    definitions = definitions + ['']*(5 - len(definitions))

    line = f'{sentence},{words[0]},{pinyins[0]},"{definitions[0]}",[sound:{audio_path}],<img src="{img_path}">'
    for w, p, d in zip(words[1:], pinyins[1:], definitions[1:]):
        line += f',{w},{p},"{d}"'
    line += '\n'
    return line

def main(args):
    url, entries = load_file(args.path)
    entries = parse_entries(entries)
    entries = md_to_html_bold(entries)
    res = download_audio(url, codec=args.codec)
    title, video_id = res['title'].replace('?', ''), res['display_id']

    base_name = f'{title}-{video_id}'
    in_file = f'{base_name}.{args.codec}'
    convert_audio(base_name, args.codec)
    
    f = open(f"{base_name}.csv", mode='w')

    for i, e in enumerate(tqdm(entries)):
        sentence, words, definitions, start, end = e
        clip_name = f'{base_name}_{i:03}.{args.codec}'
        img_name = f"{base_name}_{i:03}"
        create_clip(start, end, in_file, clip_name)

        get_screenshot(base_name, start, img_name)

        print(f'Provide definitions for sentence "{sentence}"')
        for w in words[len(definitions):]:
            d = input(f"{w} - ")
            definitions.append(d)

        f.write(create_line(sentence, words, definitions, clip_name, img_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    parser.add_argument('--codec', type=str, default='mp3')
    args = parser.parse_args()
    main(args)
