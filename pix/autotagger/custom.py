import json
from typing_extensions import Annotated
import numpy as np
import onnxruntime as rt
from pathlib import Path

from pixdb.inject import Value


class CustomAutotagger:
    def __init__(self, model_dir: Annotated[Path, Value("custom_autotagger_model_dir")]):
        self._model_dir = model_dir
        self.score_character_threshold = 0.7
        self._model = None
    
    def load_model(self):
        if self._model is not None:
            return

        self._model = rt.InferenceSession(self._model_dir / "model.onnx")
        with open(self._model_dir / "meta.json") as fp:
            self._meta = json.load(fp)
    
    def extract(self, embedding: np.array):
        input_name = self._model.get_inputs()[0].name
        label_name = self._model.get_outputs()[0].name
        probs, = self._model.run([label_name], {input_name: np.expand_dims(embedding, 0)})
        tags = list(zip(self._meta["tags"], probs[0].astype(float)))
        tags = [(tag, score) for tag, score in tags if score > self.score_character_threshold]
        return tags
