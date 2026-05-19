from flow3r.core.api.plugins.plugins import IPluginAPI
from flow3r.core.pipeline.abc.pipeline_type import PipelineType
from flow3r.core.plugin.plugin import IPlugin
from flow3r.core.source.abc.source_type import SourceType

from flow3r.plugins.core.pipeline.record_audio.config import RecordAudioConfig
from flow3r.plugins.core.pipeline.record_audio.config_widget import RecordAudioConfigWidget
from flow3r.plugins.core.pipeline.record_audio.pipeline import RecordAudioPipeline

from flow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from flow3r.plugins.core.pipeline.record_video.config_widget import RecordVideoConfigWidget
from flow3r.plugins.core.pipeline.record_video.pipeline import RecordVideoPipeline

from flow3r.plugins.core.pipeline.record_video_with_audio.config import RecordVideoWithAudioConfig
from flow3r.plugins.core.pipeline.record_video_with_audio.config_widget import RecordVideoWithAudioConfigWidget
from flow3r.plugins.core.pipeline.record_video_with_audio.pipeline import RecordVideoWithAudioPipeline

from flow3r.plugins.core.source.audio.audio_file.config import AudioFileSourceConfig
from flow3r.plugins.core.source.audio.audio_file.config_widget import AudioFileSourceConfigWidget
from flow3r.plugins.core.source.audio.audio_file.source import AudioFileSource

from flow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig
from flow3r.plugins.core.source.audio.microphone.config_widget import MicrophoneSourceConfigWidget
from flow3r.plugins.core.source.audio.microphone.source import MicrophoneSource

from flow3r.plugins.core.source.video.pylon.config import PylonCameraSourceConfig
from flow3r.plugins.core.source.video.pylon.config_widget import PylonCameraSourceConfigWidget
from flow3r.plugins.core.source.video.pylon.source import PylonCameraSource

from flow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig
from flow3r.plugins.core.source.video.video_file.config_widget import VideoFileSourceConfigWidget
from flow3r.plugins.core.source.video.video_file.source import VideoFileSource

from flow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
from flow3r.plugins.core.source.video.webcam.config_widget import WebcamSourceConfigWidget
from flow3r.plugins.core.source.video.webcam.source import WebcamSource

from flow3r.plugins.core.visualization.audio.spectrogram.visualizer_type import SpectrogramVisualizerType
from flow3r.plugins.core.visualization.audio.waveform.visualizer_type import WaveformVisualizerType
from flow3r.plugins.core.visualization.video.video.visualizer_type import VideoVisualizerType

# Source Types
WEBCAM_SOURCE_TYPE = SourceType(
    name="Webcam",
    category=("Video", "Camera"),
    config_factory=WebcamSourceConfig,
    config_widget_factory=WebcamSourceConfigWidget,
    source_factory=WebcamSource
)

VIDEO_FILE_SOURCE_TYPE = SourceType(
    name="Video File",
    category=("Video",),
    config_factory=VideoFileSourceConfig,
    config_widget_factory=VideoFileSourceConfigWidget,
    source_factory=VideoFileSource
)

PYLON_CAMERA_SOURCE_TYPE = SourceType(
    name="Pylon Camera",
    category=("Video",),
    config_factory=PylonCameraSourceConfig,
    config_widget_factory=PylonCameraSourceConfigWidget,
    source_factory=PylonCameraSource
)

AUDIO_FILE_SOURCE_TYPE = SourceType(
    name="Audio File",
    category=("Audio",),
    config_factory=AudioFileSourceConfig,
    config_widget_factory=AudioFileSourceConfigWidget,
    source_factory=AudioFileSource
)

MICROPHONE_SOURCE_TYPE = SourceType(
    name="Microphone",
    category=("Audio", "Microphone"),
    config_factory=MicrophoneSourceConfig,
    config_widget_factory=MicrophoneSourceConfigWidget,
    source_factory=MicrophoneSource
)

# Pipeline Types
RECORD_VIDEO_PIPELINE_TYPE = PipelineType(
    name="Record Video",
    category=("Video",),
    config_factory=RecordVideoConfig,
    config_widget_factory=RecordVideoConfigWidget,
    pipeline_factory=RecordVideoPipeline
)

RECORD_AUDIO_PIPELINE_TYPE = PipelineType(
    name="Record Audio",
    category=("Audio",),
    config_factory=RecordAudioConfig,
    config_widget_factory=RecordAudioConfigWidget,
    pipeline_factory=RecordAudioPipeline
)

RECORD_VIDEO_WITH_AUDIO_PIPELINE_TYPE = PipelineType(
    name="Record Video with Audio",
    category=("Video",),
    config_factory=RecordVideoWithAudioConfig,
    config_widget_factory=RecordVideoWithAudioConfigWidget,
    pipeline_factory=RecordVideoWithAudioPipeline
)


class CorePlugin(IPlugin):
    @property
    def name(self) -> str:
        return "Core"

    def initialize(self, api: IPluginAPI):
        api.config_types.register(WebcamSourceConfig.TYPE_ID, WebcamSourceConfig)
        api.config_types.register(AudioFileSourceConfig.TYPE_ID, AudioFileSourceConfig)
        api.config_types.register(PylonCameraSourceConfig.TYPE_ID, PylonCameraSourceConfig)
        api.config_types.register(VideoFileSourceConfig.TYPE_ID, VideoFileSourceConfig)
        api.config_types.register(MicrophoneSourceConfig.TYPE_ID, MicrophoneSourceConfig)

        api.config_types.register(RecordVideoConfig.TYPE_ID, RecordVideoConfig)
        api.config_types.register(RecordAudioConfig.TYPE_ID, RecordAudioConfig)
        api.config_types.register(RecordVideoWithAudioConfig.TYPE_ID, RecordVideoWithAudioConfig)

        api.source_types.register(WEBCAM_SOURCE_TYPE)
        api.source_types.register(VIDEO_FILE_SOURCE_TYPE)
        api.source_types.register(PYLON_CAMERA_SOURCE_TYPE)
        api.source_types.register(MICROPHONE_SOURCE_TYPE)
        api.source_types.register(AUDIO_FILE_SOURCE_TYPE)

        api.visualizer_types.register(VideoVisualizerType())
        api.visualizer_types.register(WaveformVisualizerType())
        api.visualizer_types.register(SpectrogramVisualizerType())

        api.pipeline_types.register(RECORD_VIDEO_PIPELINE_TYPE)
        api.pipeline_types.register(RECORD_AUDIO_PIPELINE_TYPE)
        api.pipeline_types.register(RECORD_VIDEO_WITH_AUDIO_PIPELINE_TYPE)
