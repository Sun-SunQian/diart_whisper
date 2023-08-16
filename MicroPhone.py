# from diart.sources import AudioSource
# import pyaudio  # For audio input streaming


# class AudioSource:
#     """Represents a source of audio that can start streaming via the `stream` property.

#     Parameters
#     ----------
#     uri: Text
#         Unique identifier of the audio source.
#     sample_rate: int
#         Sample rate of the audio source.
#     """
#     def __init__(self, uri: Text, sample_rate: int):
#         self.uri = uri
#         self.sample_rate = sample_rate
#         self.stream = Subject()

#     @property
#     def duration(self) -> Optional[float]:
#         """The duration of the stream if known. Defaults to None (unknown duration)."""
#         return None

#     def read(self):
#         """Start reading the source and yielding samples through the stream."""
#         raise NotImplementedError

#     def close(self):
#         """Stop reading the source and close all open streams."""
#         raise NotImplementedError



# class MicrophoneAudioSource2(AudioSource):
#     """Audio source tied to a local microphone.

#     Parameters
#     ----------
#     sample_rate: int
#         Sample rate for the emitted audio chunks.
#     block_size: int
#         Number of samples per chunk emitted.
#         Defaults to 1000.
#     device: int | str | (int, str) | None
#         Device identifier compatible for the sounddevice stream.
#         If None, use the default device.
#         Defaults to None.
#     """

#     def __init__(
#         self,
#         sample_rate: int,
#         block_size: int = 1000,
#         device: Optional[Union[int, Text, Tuple[int, Text]]] = None,
#     ):
#         super().__init__("live_recording", sample_rate)
#         self.block_size = block_size
#         self._mic_stream = sd.InputStream(
#             channels=1,
#             samplerate=sample_rate,
#             latency=0,
#             blocksize=self.block_size,
#             callback=self._read_callback,
#             device=device,
#         )

#         self.audio = pyaudio.PyAudio()

#         self.stream = self.audio.open(format=pyaudio.paInt16,
#                     channels=1,
#                     rate=SAMPLE_RATE,
#                     input=True,
#                     frames_per_buffer=CHUNK_SIZE)



#         self._queue = SimpleQueue()

#     def _read_callback(self, samples, *args):
#         self._queue.put_nowait(samples[:, [0]].T)

#     def read(self):
#         self._mic_stream.start()
#         while self._mic_stream:
#             try:
#                 while self._queue.empty():
#                     if self._mic_stream.closed:
#                         break
#                 self.stream.on_next(self._queue.get_nowait())
#             except BaseException as e:
#                 self.stream.on_error(e)
#                 break
#         self.stream.on_completed()
#         self.close()

#     def close(self):
#         self._mic_stream.stop()
#         self._mic_stream.close()


# class WebSocketAudioSource(AudioSource):
#     """Represents a source of audio coming from the network using the WebSocket protocol.

#     Parameters
#     ----------
#     sample_rate: int
#         Sample rate of the chunks emitted.
#     host: Text
#         The host to run the websocket server.
#         Defaults to 127.0.0.1.
#     port: int
#         The port to run the websocket server.
#         Defaults to 7007.
#     key: Text | Path | None
#         Path to a key if using SSL.
#         Defaults to no key.
#     certificate: Text | Path | None
#         Path to a certificate if using SSL.
#         Defaults to no certificate.
#     """
#     def __init__(
#         self,
#         sample_rate: int,
#         host: Text = "127.0.0.1",
#         port: int = 7007,
#         key: Optional[Union[Text, Path]] = None,
#         certificate: Optional[Union[Text, Path]] = None
#     ):
#         # FIXME sample_rate is not being used, this can be confusing and lead to incompatibilities.
#         #  I would prefer the client to send a JSON with data and sample rate, then resample if needed
#         super().__init__(f"{host}:{port}", sample_rate)
#         self.client: Optional[Dict[Text, Any]] = None
#         self.server = WebsocketServer(host, port, key=key, cert=certificate)
#         self.server.set_fn_message_received(self._on_message_received)

#     def _on_message_received(
#         self,
#         client: Dict[Text, Any],
#         server: WebsocketServer,
#         message: AnyStr,
#     ):
#         # Only one client at a time is allowed
#         if self.client is None or self.client["id"] != client["id"]:
#             self.client = client
#         # Send decoded audio to pipeline
#         self.stream.on_next(utils.decode_audio(message))

#     def read(self):
#         """Starts running the websocket server and listening for audio chunks"""
#         self.server.run_forever()

#     def close(self):
#         """Close the websocket server"""
#         if self.server is not None:
#             self.stream.on_completed()
#             self.server.shutdown_gracefully()

#     def send(self, message: AnyStr):
#         """Send a message through the current websocket.

#         Parameters
#         ----------
#         message: AnyStr
#             Bytes or string to send.
#         """
#         if len(message) > 0:
#             self.server.send_message(self.client, message)


# class TorchStreamAudioSource(AudioSource):
#     def __init__(
#         self,
#         uri: Text,
#         sample_rate: int,
#         streamer: StreamReader,
#         stream_index: Optional[int] = None,
#         block_size: int = 1000,
#     ):
#         super().__init__(uri, sample_rate)
#         self.block_size = block_size
#         self._streamer = streamer
#         self._streamer.add_basic_audio_stream(
#             frames_per_chunk=self.block_size,
#             stream_index=stream_index,
#             format="fltp",
#             sample_rate=self.sample_rate,
#         )
#         self.is_closed = False

#     def read(self):
#         for item in self._streamer.stream():
#             try:
#                 if self.is_closed:
#                     break
#                 # shape (samples, channels) to (1, samples)
#                 chunk = np.mean(item[0].numpy(), axis=1, keepdims=True).T
#                 self.stream.on_next(chunk)
#             except BaseException as e:
#                 self.stream.on_error(e)
#                 break
#         self.stream.on_completed()
#         self.close()

#     def close(self):
#         self.is_closed = True
