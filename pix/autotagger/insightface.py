from dataclasses import dataclass
from pathlib import Path
from typing import List
import cv2
from insightface.app import FaceAnalysis
import numpy as np


@dataclass
class Face:
    x: int
    y: int
    width: int
    height: int
    embedding: np.array
    score: float


class InsightFaceAutotagger:
    def __init__(self):
        pass

    def load_model(self):
        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=0)
    
    def extract(self, file: Path) -> List[Face]:
        image = cv2.imread(str(file))

        faces = self.app.get(image)
        if not faces:
            return []

        result = []
        for face in faces:
            minx, miny, maxx, maxy = face.bbox.astype(int)
            result.append(Face(
                x=minx,
                y=miny,
                width=maxx - minx,
                height=maxy - miny,
                embedding=face.embedding,
                score=float(face.det_score),
            ))
        
        return result
