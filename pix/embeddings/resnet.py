from pathlib import Path
import PIL
import torch
from torchvision import models
from torchvision.models.feature_extraction import create_feature_extractor


class ResnetEmbedding:
    def __init__(self):
        self._model_loaded = False

    def load_model(self):
        if self._model_loaded:
            return

        model = models.resnet152(weights=models.ResNet152_Weights.DEFAULT)
        model = create_feature_extractor(model, return_nodes={'flatten': 'flatten'})
        model.eval()
        self.model = model
        self.preprocess = models.ResNet152_Weights.DEFAULT.transforms()
        self._model_loaded = True

    def extract(self, file: Path):
        with PIL.Image.open(file) as im:
            if im.mode != 'RGB':
                im = im.convert('RGB')
            image = self.preprocess(im).unsqueeze(0)
            with torch.no_grad(), torch.cuda.amp.autocast():
                return self.model(image)['flatten'].numpy()
