from collections import OrderedDict
from pathlib import Path
from typing import Union
from typing_extensions import Annotated
import PIL
import torch
from torch import nn
import torchvision.transforms as transforms
import torchvision.transforms.functional as F

from pix.embeddings.csd_model import CSD_CLIP
from pixdb.inject import Value

DEVICE = None  # change to `cuda` to use gpu


class CsdEmbedding:
    def __init__(self, csd_pretrained_model_path: Annotated[Path, Value]):
        self._model_loaded = False
        self._model_path = csd_pretrained_model_path

    def load_model(self):
        if self._model_loaded:
            return

        model = CSD_CLIP()
        if has_batchnorms(model):
            model = nn.SyncBatchNorm.convert_sync_batchnorm(model)

        checkpoint = torch.load(self._model_path, map_location="cpu", weights_only=False)
        state_dict = convert_state_dict(checkpoint['model_state_dict'])
        msg = model.load_state_dict(state_dict, strict=False)
        # print(f"=> loaded checkpoint with msg {msg}")

        if DEVICE:
            model = model.to(DEVICE)
        
        model.eval()  # model in train mode by default, impacts some models with BatchNorm or stochastic depth active

        size = 224

        normalize = transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))

        transforms_branch0 = transforms.Compose([
            transforms.Resize(size=size, interpolation=F.InterpolationMode.BICUBIC),
            transforms.CenterCrop(size),
            transforms.ToTensor(),
            normalize,
        ])

        self.model = model
        self.preprocess = transforms_branch0
        self._model_loaded = True

    def extract(self, file: Path):
        with PIL.Image.open(file) as im:
            if im.mode != 'RGB':
                im = im.convert('RGB')
            image = self.preprocess(im).unsqueeze(0).to(DEVICE)
            with torch.no_grad(), torch.cuda.amp.autocast():
                _, _, emb = self.model(image)
                return emb[0].cpu().numpy()


def convert_state_dict(state_dict):
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        if k.startswith("module."):
            k = k.replace("module.", "")
        new_state_dict[k] = v
    return new_state_dict


def has_batchnorms(model):
    bn_types = (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d, nn.SyncBatchNorm)
    for name, module in model.named_modules():
        if isinstance(module, bn_types):
            return True
    return False
