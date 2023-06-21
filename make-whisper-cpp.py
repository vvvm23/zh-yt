import sys
import subprocess
import re
from main import download_audio

def convert_audio(title: str):
    # command = ["ffmpeg", "-y", "-i", title + '.mp4', "-t", "10", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-q:a", "0", "-map", "a", title + f".wav"]
    command = ["ffmpeg", "-y", "-i", title + '.mp4', "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-q:a", "0", "-map", "a", title + f".wav"]
    subprocess.call(command)

def get_whisper_cpp(path: str, model_path: str = "./whisper.cpp/models/ggml-large-v1.bin", threads: int = 8, lang: str = "chinese"):
    command = ["./whisper.cpp/main", "-f", path, "-m", model_path, "-t", str(threads), "-l", lang]
    res = subprocess.run(command, stdout=subprocess.PIPE, text=True)

    if res.returncode:
        raise RuntimeError(res.stderr)

    return res.stdout

def convert_timestamp(timestamp: str):
    timestamp, ms = timestamp.split('.')
    h, m, s = timestamp.split(':')

    MINUTE = 60
    HOUR = 60 * MINUTE
    return int(h) * HOUR + int(m) * MINUTE + int(s) + float(ms)

if __name__ == "__main__":
    url = sys.argv[1]
    out_file = sys.argv[2]

    res = download_audio(url)
    title, video_id = res['title'].replace('?', ''), res['display_id']

    base_name = f'{title}-{video_id}'
    convert_audio(base_name)
    in_file = f'{base_name}.wav'

    whisper_res = get_whisper_cpp(in_file)

    filtered_res = [l for l in whisper_res.split('\n') if l]

    with open(out_file, mode='w') as f:
        f.write(f"{url}\n")
        for l in filtered_res:
            split_l = l.split(' ')
            time_str = ''.join(split_l[:3])
            text = ' '.join(split_l[4:])

            match = re.match(r"^\[(?P<start>.+?)\s*-->\s*(?P<end>.+?)\]$", time_str)
            time_start, time_end = match.group('start'), match.group('end')
            time_start, time_end = [convert_timestamp(t) for t in (time_start, time_end)]

            # (time_start, time_end), text = c['timestamp'], c['text']
            try:
                f.write(f'"{text}",definition,{time_start:.2f},{time_end:.2f}\n')
            except Exception as e:
                print("failed")
                print(text, time_start, time_end)