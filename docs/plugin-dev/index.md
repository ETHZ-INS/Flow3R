# Plugin Development

Flow3R's plugin system lets you add new **source types**, **pipeline types**, **visualizers**, and **settings panels** as separate Python packages — without modifying the core application.

---

## How plugins are loaded

Flow3R discovers plugins through Python's [entry-point](https://packaging.python.org/en/latest/specifications/entry-points/) mechanism.  Any installed package that declares a `flow3r.plugins` entry point will have its plugin class instantiated and its `initialize()` method called at startup.

```toml
# your plugin's pyproject.toml
[project.entry-points."flow3r.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

---

## Minimal plugin skeleton

```python
# my_package/plugin.py
from flow3r.core.plugin.plugin import IPlugin
from flow3r.core.api.plugins.plugins import IPluginAPI


class MyPlugin:
    @property
    def name(self) -> str:
        return "My Plugin"

    def initialize(self, api: IPluginAPI) -> None:
        # register your source types, pipeline types, etc. here
        pass
```

That's a valid (empty) plugin.  Install your package in the `GrimaceRecorder` conda environment and Flow3R will load it automatically.

---

## Adding a source type

A source type tells Flow3R how to create config objects, config-editor widgets, and live source instances for a new kind of input device.

### 1. Implement the config

```python
from dataclasses import dataclass, field
from flow3r.core.source.abc.source_config import SourceConfigBase


@dataclass
class MyCameraConfig(SourceConfigBase):
    TYPE_ID: ClassVar[str] = "my_plugin.my_camera"
    VERSION: ClassVar[int] = 1

    device_index: int = 0

    def _to_dict_data(self) -> dict:
        return {"device_index": self.device_index}

    @classmethod
    def _from_dict_data(cls, data: dict, type_registry) -> "MyCameraConfig":
        return cls(device_index=data.get("device_index", 0))
```

### 2. Implement the source

```python
from flow3r.core.source.abc.source import ISource

class MyCameraSource:
    def __init__(self, config: MyCameraConfig):
        self._config = config
        self._stream = ...  # create your IStream here

    @property
    def stream(self):
        return self._stream

    def open(self):
        ...  # open device

    def close(self):
        ...  # release device
```

### 3. Implement the config widget

```python
from flow3r.core.widgets.config_widget import IConfigWidget
from PySide6.QtWidgets import QWidget, QSpinBox, QFormLayout

class MyCameraConfigWidget(QWidget, IConfigWidget):
    def __init__(self, config: MyCameraConfig, parent: QWidget = None):
        super().__init__(parent)
        self._config = config
        # build UI...

    def get_config(self) -> MyCameraConfig:
        return self._config
```

### 4. Register in your plugin

```python
from flow3r.core.source.abc.source_type import SourceType

MY_CAMERA_TYPE = SourceType(
    name="My Camera",
    category=("Video", "Camera"),
    config_factory=MyCameraConfig,
    config_widget_factory=MyCameraConfigWidget,
    source_factory=MyCameraSource,
)

class MyPlugin:
    ...
    def initialize(self, api: IPluginAPI) -> None:
        api.config_types.register(MyCameraConfig.TYPE_ID, MyCameraConfig)
        api.source_types.register(MY_CAMERA_TYPE)
```

> **Important:** Always call `api.config_types.register(...)` for every config class you introduce.  This is required for Flow3R to deserialise `.f3r` project files that contain your source.

---

## Adding a pipeline type

Pipelines are more flexible than sources — they can read from multiple streams simultaneously and write output files, run ML models, or do anything else during a recording session.

See [`PipelineConfigBase`][flow3r.core.pipeline.abc.pipeline_config.PipelineConfigBase] for the config base class.

### Option A — Reactive pipeline

Subclass [`PipelineBase`][flow3r.core.pipeline.abc.pipeline.PipelineBase] and override `build()`.
Instead of returning an object, **register** your completion signals on the
[`PipelineContext`][flow3r.core.pipeline.abc.pipeline.PipelineContext] that the framework provides:

```python
from flow3r.core.pipeline.abc.pipeline import PipelineBase, PipelineContext
from flow3r.core.streaming.abc.stream import IStream
from typing import Dict

class MyPipeline(PipelineBase[MyConfig]):
    def configure(self, session_context, config: MyConfig):
        self._config = config

    def build(self, context: PipelineContext, sources: Dict[str, IStream]) -> None:
        sub = my_sink.subscribe(sources["Video"])
        context.register_primary_done(sub.done)   # required
        context.add_disposable(sub.disposable)     # disposed on abort
```

`context.control` is an observable that emits `None` once when the recording gate
opens and completes when stop is requested.  Useful for pipelines that manage their
own resources instead of consuming application-provided streams.

### Option B — Iterative pipeline (recommended for data scientists)

Subclass [`IterativePipeline`][flow3r.core.pipeline.iterative_pipeline.IterativePipeline] and
override `run()`.  Each source arrives as a plain Python iterable — no reactive
programming required:

```python
from pathlib import Path
from typing import Dict, Iterable
from flow3r.core.pipeline.iterative_pipeline import IterativePipeline

class MyPipeline(IterativePipeline[MyConfig]):
    def configure(self, session_context, config: MyConfig):
        self._output_path = Path(config.output_file)

    def run(self, sources: Dict[str, Iterable]) -> None:
        with open(self._output_path, "w") as f:
            for frame in sources["Video"]:
                result = my_model.predict(frame)
                f.write(result.to_json() + "\n")
        # returning normally signals primary_done automatically
```

`run()` is called on a background thread when the recording starts.  The iterables
stop yielding and raise `StopIteration` when stop is requested, so ordinary `for`
loops exit naturally.  Any uncaught exception is forwarded as a pipeline error.

### Registration

The registration pattern is identical to source types:

```python
from flow3r.core.pipeline.abc.pipeline_type import PipelineType

MY_PIPELINE_TYPE = PipelineType(
    name="My Pipeline",
    category=("Analysis",),
    config_factory=MyConfig,
    config_widget_factory=MyConfigWidget,
    pipeline_factory=MyPipeline,
)

class MyPlugin:
    def initialize(self, api: IPluginAPI) -> None:
        api.config_types.register(MyConfig.TYPE_ID, MyConfig)
        api.pipeline_types.register(MY_PIPELINE_TYPE)
```

> **Important:** Always call `api.config_types.register(...)` for every config class you introduce.  This is required for Flow3R to deserialise `.f3r` project files that contain your pipeline.

---

## API Reference

See the [API Reference](../api-reference/index.md) for full, auto-generated documentation of all public plugin API classes.
