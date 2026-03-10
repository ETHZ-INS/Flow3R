from flow3r.core.api.plugins.plugins import IPluginAPI
from flow3r.core.plugin.plugin import IPlugin
from flow3r.plugins.core.pipeline.record_audio.pipeline_type import RecordAudioPipelineType
from flow3r.plugins.core.pipeline.record_video.pipeline_type import RecordVideoPipelineType
from flow3r.plugins.core.pipeline.record_video_with_audio.pipeline_type import RecordVideoWithAudioPipelineType
from flow3r.plugins.core.source.audio.audio_file.source_type import AudioFileSourceType
from flow3r.plugins.core.source.audio.microphone.source_type import MicrophoneSourceType
from flow3r.plugins.core.source.video.pylon.source_type import PylonCameraSourceType
from flow3r.plugins.core.source.video.video_file.source_type import VideoFileSourceType
from flow3r.plugins.core.source.video.webcam.source_type import WebcamSourceType
from flow3r.plugins.core.visualization.audio.spectogram.visualizer_type import SpectrogramVisualizerType
from flow3r.plugins.core.visualization.audio.waveform.visualizer_type import WaveformVisualizerType
from flow3r.plugins.core.visualization.video.video.visualizer_type import VideoVisualizerType


class CorePlugin(IPlugin):
    @property
    def name(self) -> str:
        return "Core"

    def initialize(self, api: IPluginAPI):
        api.source_types.register(WebcamSourceType())
        api.source_types.register(VideoFileSourceType())
        api.source_types.register(PylonCameraSourceType())
        api.source_types.register(MicrophoneSourceType())
        api.source_types.register(AudioFileSourceType())

        api.visualizer_types.register(VideoVisualizerType())
        api.visualizer_types.register(WaveformVisualizerType())
        api.visualizer_types.register(SpectrogramVisualizerType())

        api.pipeline_types.register(RecordVideoPipelineType())
        api.pipeline_types.register(RecordAudioPipelineType())
        api.pipeline_types.register(RecordVideoWithAudioPipelineType())
