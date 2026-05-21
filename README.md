# Flow3R

**Flow3R** is a multi-source video and data recording application built with Python and PySide6. It is developed at the [ETH3RHub](https://github.com/ETHZ-INS) lab for scientific and animal welfare research.

> 📖 **Full documentation:** [https://ethz-ins.github.io/Flow3R](https://ethz-ins.github.io/Flow3R) *(once GitHub Pages is enabled)*

---

## Features

- Configure multiple **sources** — webcams, Basler Pylon cameras, video/audio files, microphones, RTSP streams
- Organise sources into **recording groups**, each with independent recording controls and timing
- Attach **pipelines** to groups — record video, record audio, run pose estimation, grimace scale analysis, and more
- Define **placeholders** (template variables) that are injected into file paths and session metadata
- Save and load full project configurations as `.f3r` YAML files
- Extend via a **plugin API** — add new source types, pipeline types, and settings panels without touching core code

---

## Requirements

- Windows 10/11 (primary target; Linux untested)
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda
- Python 3.11+

---

## Installation

### From source (development)

```bash
# 1. Create and activate the conda environment
conda create -n GrimaceRecorder python=3.11
conda activate GrimaceRecorder

# 2. Clone the repository
git clone https://github.com/ETHZ-INS/Flow3R.git
cd Flow3R

# 3. Install in editable mode (all dependencies pulled automatically)
pip install -e .
```

### Running

```bash
conda activate GrimaceRecorder
python src/main.py
```

---

## Project layout

```
Flow3R/
├── src/
│   └── flow3r/
│       ├── app/          # Application layer — UI, config dataclasses, controller
│       ├── core/         # Framework abstractions (source, pipeline, streaming ABCs)
│       └── plugins/      # Built-in plugin implementations (core sources & pipelines)
├── docs/                 # Documentation source (MkDocs)
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── pyproject.toml
```

---

## Documentation

See the [`docs/`](docs/) folder or the published site for:

- [User Guide](docs/user-guide/index.md) — GUI walkthrough for researchers
- [Plugin Development](docs/plugin-dev/index.md) — how to write and package Flow3R plugins
- [Architecture](docs/architecture/index.md) — config layer, controller, signals/slots

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).

