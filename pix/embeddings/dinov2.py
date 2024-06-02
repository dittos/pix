from pathlib import Path
import PIL
import torch
from transformers import AutoImageProcessor, AutoModel


class Dinov2Embedding:
    def __init__(self):
        self._model_loaded = False
        self._traced_model = None

    def load_model(self):
        if self._model_loaded:
            return

        self.model = AutoModel.from_pretrained('facebook/dinov2-base')
        self.preprocess = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
        self._model_loaded = True

    def extract(self, file: Path):
        with PIL.Image.open(file) as im:
            inputs = self.preprocess(images=im, return_tensors='pt')
            return self._model(inputs).pooler_output[0].numpy()
    
    def _model(self, inputs):
        with torch.no_grad(), torch.cuda.amp.autocast():
            # if self._traced_model is None:
            #     self.model.config.return_dict = False
            #     self._traced_model = torch.jit.trace(self.model, [inputs.pixel_values])

            # return self._traced_model(inputs.pixel_values)
            return self.model(**inputs)
            