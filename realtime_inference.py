from diart import OnlineSpeakerDiarization
from diart.sources import MicrophoneAudioSource
from diart.inference import RealTimeInference
# from diart.sinks import RTTMWriter

dia = OnlineSpeakerDiarization()
sample_rate = dia.config.sample_rate
mic = MicrophoneAudioSource(sample_rate)
inference = RealTimeInference(dia,mic,do_plot=True)
prediction = inference()

# mic = MicrophoneAudioSource(pipeline.config.sample_rate)
# inference = RealTimeInference(pipeline, mic, do_plot=True)

# # import os

# # output_directory = '/output/'
# # file_path = os.path.join(output_directory, 'file.rttm')

# # os.makedirs(output_directory, exist_ok=True)  # Creates the directory if it doesn't exist



# inference.attach_observers(RTTMWriter(mic.uri, "/output/file.rttm"))
# prediction = inference()