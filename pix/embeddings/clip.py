from pathlib import Path
import PIL
import open_clip
import torch


class ClipEmbedding:
    def __init__(self):
        self._model_loaded = False

    def load_model(self):
        if self._model_loaded:
            return

        model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        model.eval()  # model in train mode by default, impacts some models with BatchNorm or stochastic depth active
        self.model = model
        self.preprocess = preprocess
        self.tokenizer = open_clip.get_tokenizer('ViT-B-32')
        self._model_loaded = True

    def extract(self, file: Path):
        with PIL.Image.open(file) as im:
            image = self.preprocess(im).unsqueeze(0)
            with torch.no_grad(), torch.cuda.amp.autocast():
                return self.model.encode_image(image)[0].numpy()
    
    def encode_text(self, text: str):
        with torch.no_grad(), torch.cuda.amp.autocast():
            return self.model.encode_text(self.tokenizer([text]))[0].numpy()
