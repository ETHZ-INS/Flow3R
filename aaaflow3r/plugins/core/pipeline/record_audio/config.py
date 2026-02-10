from dataclasses import dataclass


@dataclass
class RecordAudioConfig:
    audio_file: str = "my_audio.wav"
