import pyaudio  # For audio input streaming
import numpy as np  # For audio data manipulation
import time  # For timing
# import your_asr_module  # Import your ASR model

# Parameters
CHUNK_SIZE = 16000  # Number of audio samples in a chunk (1 second for 16 kHz)
SAMPLE_RATE = 16000  # Sampling rate of the audio (16 kHz)
# ASR_MODEL_PATH = 'path/to/your/asr/model'  # Path to your ASR model

# Initialize ASR model
# asr_model = your_asr_module.load_model(ASR_MODEL_PATH)  # Replace with your model loading code

# Initialize PyAudio
audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)

print("Starting live streaming and ASR...")

try:
    while True:
        # Read audio chunk from the microphone
        audio_chunk = stream.read(CHUNK_SIZE)
        
        # Convert audio chunk to numpy array
        audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
        
        # Perform ASR on the audio chunk
        # transcription = asr_model.transcribe(audio_np)
        
        # Print the ASR output
        # print("ASR:", transcription)
        print(audio_np)
        
        # Sleep for a short time to simulate real-time processing
        time.sleep(0.5)  # Adjust the sleep duration as needed
        
except KeyboardInterrupt:
    print("Stopping live streaming and ASR...")
    stream.stop_stream()
    stream.close()
    audio.terminate()
