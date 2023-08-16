import whisper_timestamped  # donot comment this line out

import os
import sys
import numpy as np
# import whisper_timestamped as whisper
from faster_whisper import WhisperModel
from pyannote.core import Segment
from contextlib import contextmanager
# import torch


# from faster_whisper import WhisperModel
# from datetime import datetime

# whisper_model_path='/home/zytest/ASR/Faster_Whisper/Medium_FineTuned'


# # Run on GPU with FP16
# model = WhisperModel(whisper_model_path, device="cuda", compute_type="float16")
# print("model loaded")
# # or run on GPU with INT8
# # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# # or run on CPU with INT8
# # model = WhisperModel(model_size, device="cpu", compute_type="int8")
# # file = '/media/zytest/sda2/ASR/IMDA/PART1/DATA/CHANNEL0/WAVE/SPEAKER0001/SESSION1/000011401.WAV'
# # file = '/media/zytest/sda2/AMI/EN2001a/audio/EN2001a.Mix-Headset.wav'
# file = '/media/zytest/sda2/ASR/IMDA/PART4/sur_0009_1018_phns_cs-chn.wav' 

# segments, info = model.transcribe(file, beam_size=5)

# print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

# s = datetime.now()

# print(f"start at {s}")

# for segment in segments:
#     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

# e = datetime.now()
# print(f"stop at {e}")

# print(f"time elapsed {e-s}")
# exit()
@contextmanager
def suppress_stdout():
    # Auxiliary function to suppress Whisper logs (it is quite verbose)
    # All credit goes to: https://thesmithfam.org/blog/2012/10/25/temporarily-suppress-console-output-in-python/
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

class FasterWhisperTranscriber:
    def __init__(self, model=None, device=None,language = None):
        try:
            if device =='cuda':
                self.model = WhisperModel(model, device="cuda", compute_type="float16")
            else:
                self.model = WhisperModel(model, device="cpu", compute_type="int8")
        except:
            raise ValueError("Faster Whisper Model loading not successful")

        self._buffer = ""

        self.language = language

    #  def transcribe(
    #     self,
    #     audio: Union[str, BinaryIO, np.ndarray],
    #     language: Optional[str] = None,
    #     task: str = "transcribe",
    #     beam_size: int = 5,
    #     best_of: int = 5,
    #     patience: float = 1,
    #     length_penalty: float = 1,
    #     repetition_penalty: float = 1,
    #     temperature: Union[float, List[float], Tuple[float, ...]] = [
    #         0.0,
    #         0.2,
    #         0.4,
    #         0.6,
    #         0.8,
    #         1.0,
    #     ],
    #     compression_ratio_threshold: Optional[float] = 2.4,
    #     log_prob_threshold: Optional[float] = -1.0,
    #     no_speech_threshold: Optional[float] = 0.6,
    #     condition_on_previous_text: bool = True,
    #     prompt_reset_on_temperature: float = 0.5,
    #     initial_prompt: Optional[Union[str, Iterable[int]]] = None,
    #     prefix: Optional[str] = None,
    #     suppress_blank: bool = True,
    #     suppress_tokens: Optional[List[int]] = [-1],
    #     without_timestamps: bool = False,
    #     max_initial_timestamp: float = 1.0,
    #     word_timestamps: bool = False,
    #     prepend_punctuations: str = "\"'“¿([{-",
    #     append_punctuations: str = "\"'.。,，!！?？:：”)]}、",
    #     vad_filter: bool = False,
    #     vad_parameters: Optional[Union[dict, VadOptions]] = None,
    # )

    def transcribe(self, waveform):
        """Transcribe audio using Faster Whisper"""
        
        audio = waveform.data.astype("float16").reshape(-1)
        # segments, info = self.model.transcribe(audio, beam_size=5)

        # audio = whisper.pad_or_trim(audio)

        # Transcribe the given audio while suppressing logs
        with suppress_stdout():
            segments,info = self.model.transcribe(
                audio,
                # We use past transcriptions to condition the model
                language = self.language,
                initial_prompt=self._buffer,
            )

        # segments = list(segments) 
        transcription = ''
        segmentlst  = []
        for segment in segments:
               transcription += segment.text
               segmentlst.append(segment)

        return transcription,segmentlst

    def identify_speakers(self, segments, diarization, time_shift):
        """Iterate over transcription segments to assign speakers"""
        speaker_captions = []
        for segment in segments:

            # Crop diarization to the segment timestamps
            start = time_shift + segment.start
            end = time_shift + segment.end
            dia = diarization.crop(Segment(start, end))

            # Assign a speaker to the segment based on diarization
            speakers = dia.labels()
            num_speakers = len(speakers)
            if num_speakers == 0:
                # No speakers were detected
                caption = (-1, segment.text)
            elif num_speakers == 1:
                # Only one speaker is active in this segment
                spk_id = int(speakers[0].split("speaker")[1])
                caption = (spk_id, segment.text)
            else:
                # Multiple speakers, select the one that speaks the most
                max_speaker = int(np.argmax([
                    dia.label_duration(spk) for spk in speakers
                ]))
                caption = (max_speaker, segment.text)
            speaker_captions.append(caption)

        return speaker_captions

    def __call__(self, diarization, waveform):
        # Step 1: Transcribe
        transcription,segmentlst = self.transcribe(waveform)
        # print(transcription)
        # Update transcription buffer
        

        self._buffer += transcription
        # The audio may not be the beginning of the conversation
        time_shift = waveform.sliding_window.start
        # Step 2: Assign speakers
        speaker_transcriptions = self.identify_speakers(segmentlst, diarization, time_shift)
        return speaker_transcriptions
    

