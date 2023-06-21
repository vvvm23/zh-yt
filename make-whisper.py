from whisper_jax import FlaxWhisperPipline
import jax.numpy as jnp
from jax.experimental.compilation_cache import compilation_cache

compilation_cache.initialize_cache("compilation_cache")

from main import download_audio, convert_audio
import sys

url = sys.argv[1]
out_file = sys.argv[2]

codec = 'mp3'
res = download_audio(url, codec=codec)
title, video_id = res['title'].replace('?', ''), res['display_id']

base_name = f'{title}-{video_id}'
in_file = f'{base_name}.{codec}'
convert_audio(base_name, codec)

pipeline = FlaxWhisperPipline("openai/whisper-large-v2", dtype=jnp.bfloat16, batch_size=1)

outputs = pipeline(in_file, task="transcribe", return_timestamps=True, language="chinese")

with open(out_file, mode='w') as f:
    f.write(f"{url}\n")
    for c in outputs['chunks']:
        (time_start, time_end), text = c['timestamp'], c['text']
        try:
            f.write(f'"{text}",definition,{time_start:.2f},{time_end:.2f}\n')
        except Exception as e:
            print("failed")
            print(text, time_start, time_end)
