from diart.sources import *
from whisperTranscriber import WhisperTranscriber
from util_func import concat,colorize_transcription

import torch

import logging
import traceback
import diart.operators as dops
import rich
import rx.operators as ops
from diart import OnlineSpeakerDiarization, PipelineConfig
from diart.sources import MicrophoneAudioSource,FileAudioSource


# refer to: https://gist.github.com/juanmc2005/ed6413e697e176cb36a149d8c40a3a5b
# and : https://betterprogramming.pub/color-your-captions-streamlining-live-transcriptions-with-diart-and-openais-whisper-6203350234ef




# Suppress whisper-timestamped warnings for a clean output
logging.getLogger("whisper_timestamped").setLevel(logging.ERROR)

# We configure the system to use sliding windows of 5 seconds with a step of 500ms (the default) 
# and we set the latency to the minimum (500ms) to increase responsiveness.


# If you have a GPU, you can also set device=torch.device("cuda")

config = PipelineConfig(
    duration=5,
    step=0.5,
    latency="min",
    tau_active=0.5, #Only recognize speakers whose probability of speech is higher than 50%.
    rho_update=0.1, #Diart automatically gathers information from speakers to improve itself (don’t worry, this is done locally and is not shared with anyone). Here we only use speech longer than 100ms per speaker for self-improvement.
    delta_new=0.57, # This is an internal threshold between 0 and 2 that regulates new speaker detection. The lower the value, the more sensitive the system will be to differences in voices.
    device=torch.device("cuda")
)
print(f"config sample rate: {config.sample_rate}")
dia = OnlineSpeakerDiarization(config)
print(f"OnlineSpeakerDiarization initialised")
source = MicrophoneAudioSource(config.sample_rate)

# source = FileAudioSource(file='/media/zytest/sda2/AMI/ES2002a/audio/ES2002a.Mix-Headset.wav',
#                          sample_rate = 16000)
print(f"source initialised")
# Creating the ASR module
# If you have a GPU, you can also set device="cuda"
asr = WhisperTranscriber(model="medium",device='cuda')

# Split the stream into 2s chunks for transcription
transcription_duration = 2

# Apply models in batches for better efficiency
batch_size = int(transcription_duration // config.step)

# Chain of operations to apply on the stream of microphone audio
source.stream.pipe(
    dops.rearrange_audio_stream(
        config.duration, config.step, config.sample_rate
    ),
    # Wait until a batch is full
    # The output is a list of audio chunks
    ops.buffer_with_count(count=batch_size),
    # Obtain diarization prediction
    # The output is a list of pairs `(diarization, audio chunk)`
    ops.map(dia),
    # Concatenate 500ms predictions/chunks to form a single 2s chunk
    ops.map(concat),
    # Ignore this chunk if it does not contain speech
    ops.filter(lambda ann_wav: ann_wav[0].get_timeline().duration() > 0),
    # Obtain speaker-aware transcriptions
    # The output is a list of pairs `(speaker: int, caption: str)`
    ops.starmap(asr),
     # Color transcriptions according to the speaker
    # The output is plain text with color references for rich
    ops.map(colorize_transcription),
).subscribe(
    on_next=rich.print, 
    on_error=lambda _: traceback.print_exc())# print stacktrace if error

print("Listening...")
source.read()

