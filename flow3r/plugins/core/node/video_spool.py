import reactivex as rx
from reactivex import operators as ops

from py3r.media.types import VideoFrame

from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.node.video_segment_concatenator import VideoSegmentConcatenator
from flow3r.plugins.core.node.video_segment_reader import VideoSegmentReader
from flow3r.plugins.core.node.video_segment_writer import VideoSegmentWriter
from flow3r.plugins.core.typing.video import VideoFormat

"""
A transform node that writes a stream of video frames to disk in chunks of 5 seconds, 
then loads the chunks from disk again as a stream of video frames. 
At the end of the recording, the chunks are concatenated to a full video file.
This serves multiple purposes:
1. It makes sure that the live video is written to disk immediately.
2. Any secondary processing can be done on the frames read from disk with bounded queues and 
blocking backpressure without slowing down the acquisition 
3. Any processing done on the frames (like pose estimation) is reproducible. 
The frames read live from the video chunks are identical to the frames read from the final video file, 
so processing can be rerun if necessary and yield the exact same results
"""
class VideoSpool:
    def __init__(self, writer: VideoSegmentWriter, reader: VideoSegmentReader, concatenator: VideoSegmentConcatenator):
        self._writer = writer
        self._reader = reader
        self._concatenator = concatenator

    def pipe(self, input_stream: IStream[VideoFormat, VideoFrame]) -> Stream[VideoFormat, VideoFrame]:
        segment_stream = self._writer.pipe(input_stream)
        segment_stream = Stream(segment_stream.descriptor, segment_stream.observable.pipe(ops.share()))
        concatenator_subscription = self._concatenator.subscribe(segment_stream)

        output_stream = self._reader.pipe(segment_stream)

        wrapped_output_data = rx.using(lambda: concatenator_subscription, lambda sub: output_stream.observable)
        wrapped_output_stream = Stream(output_stream.descriptor, wrapped_output_data)

        return wrapped_output_stream
