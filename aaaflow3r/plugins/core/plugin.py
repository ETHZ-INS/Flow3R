from aaaflow3r.core.api.plugins.plugins import IPluginAPI
from aaaflow3r.core.plugin.plugin import IPlugin
from aaaflow3r.plugins.core.pipeline.record_audio.pipeline_type import RecordAudioPipelineType
from aaaflow3r.plugins.core.pipeline.record_video.pipeline_type import RecordVideoPipelineType
from aaaflow3r.plugins.core.pipeline.record_video_with_audio.pipeline_type import RecordVideoWithAudioPipelineType
from aaaflow3r.plugins.core.source.audio.audio_file.source_type import AudioFileSourceType
from aaaflow3r.plugins.core.source.audio.microphone.source_type import MicrophoneSourceType
from aaaflow3r.plugins.core.source.video.video_file.source_type import VideoFileSourceType
from aaaflow3r.plugins.core.source.video.webcam.source_type import WebcamSourceType
from aaaflow3r.plugins.core.visualization.audio.visualizer_type import AudioVisualizerType
from aaaflow3r.plugins.core.visualization.video.visualizer_type import VideoVisualizerType


class CorePlugin(IPlugin):
    def initialize(self, api: IPluginAPI):
        api.source_types.register(WebcamSourceType())
        api.source_types.register(VideoFileSourceType())
        api.source_types.register(MicrophoneSourceType())
        api.source_types.register(AudioFileSourceType())

        api.visualizer_types.register(VideoVisualizerType())
        api.visualizer_types.register(AudioVisualizerType())

        api.pipeline_types.register(RecordVideoPipelineType())
        api.pipeline_types.register(RecordAudioPipelineType())
        api.pipeline_types.register(RecordVideoWithAudioPipelineType())
