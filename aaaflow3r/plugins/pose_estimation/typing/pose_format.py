from dataclasses import dataclass, field
from typing import List

from py3r.pose.core.types import PoseInstanceType


@dataclass
class PoseFormat:
    instance_types: List[PoseInstanceType] = field(default_factory=list)
