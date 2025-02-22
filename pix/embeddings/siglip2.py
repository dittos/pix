from pathlib import Path
from typing import List
import PIL
import torch
from transformers import AutoImageProcessor, AutoModel


class Siglip2Embedding:
    batch_size = 200

    def __init__(self):
        self._model_loaded = False
        self._traced_model = None
        self._device = 'cuda'
        # self._device = 'cpu'

    def load_model(self):
        if self._model_loaded:
            return

        self.model = AutoModel.from_pretrained('google/siglip2-large-patch16-256').to(self._device)
        self.preprocess = AutoImageProcessor.from_pretrained('google/siglip2-large-patch16-256')
        self._model_loaded = True
    
    def extract_batch(self, files: List[Path]):
        images = []
        inputs = None
        try:
            for file in files:
                im = PIL.Image.open(file)
                if im.mode != 'RGB':
                    im = im.convert('RGB')
                images.append(im)
            inputs = self.preprocess(images=images, return_tensors='pt')
        finally:
            for im in images:
                im.close()
            images = None
        
        return self._model(inputs.to(self._device)).cpu().numpy()

    def extract(self, file: Path):
        with PIL.Image.open(file) as im:
            inputs = self.preprocess(images=im, return_tensors='pt').to(self._device)
            return self._model(inputs).cpu().numpy()
    
    def _model(self, inputs):
        with torch.no_grad(), torch.cuda.amp.autocast():
            # if self._traced_model is None:
            #     self.model.config.return_dict = False
            #     self._traced_model = torch.jit.trace(self.model, [inputs.pixel_values])

            # return self._traced_model(inputs.pixel_values)
            return self.model.get_image_features(**inputs)
