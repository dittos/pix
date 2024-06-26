import csv
from dataclasses import dataclass
import functools
import time
from typing_extensions import Annotated
import huggingface_hub
import numpy as np
import onnx
import onnxruntime as rt
import PIL.Image

from pathlib import Path
from typing import List, Tuple, Union
from pix.model.image import TagType

from pixdb.inject import Value

from . import dbimutils

MOAT_MODEL_REPO = "SmilingWolf/wd-v1-4-moat-tagger-v2"
SWIN_MODEL_REPO = "SmilingWolf/wd-v1-4-swinv2-tagger-v2"
CONV_MODEL_REPO = "SmilingWolf/wd-v1-4-convnext-tagger-v2"
CONV2_MODEL_REPO = "SmilingWolf/wd-v1-4-convnextv2-tagger-v2"
VIT_MODEL_REPO = "SmilingWolf/wd-v1-4-vit-tagger-v2"
MODEL_FILENAME = "model.onnx"
LABEL_FILENAME = "selected_tags.csv"


@dataclass
class AutotagResult:
    tags: List[Tuple[str, Union[TagType, None], float]]
    embedding: Union[np.array, None]


class WdAutotagger:
    def __init__(self, huggingface_token: Annotated[str, Value], data_dir: Annotated[Path, Value]) -> None:
        self.huggingface_token = huggingface_token
        self.modified_model_cache_path = data_dir / "wd-autotagger-model.onnx"
        self.score_general_threshold = 0.35
        self.score_character_threshold = 0.85
        self._predict = None

    def load_model(self):
        if self._predict is not None:
            return

        tag_names, rating_indexes, general_indexes, character_indexes = load_labels(self.huggingface_token)

        # TODO: invalidation
        if not self.modified_model_cache_path.exists():
            path = huggingface_hub.hf_hub_download(
                MOAT_MODEL_REPO, MODEL_FILENAME, use_auth_token=self.huggingface_token
            )

            print("modifying model...")
            start = time.perf_counter()
            raw_model = onnx.load(path)
            raw_model.graph.output.append(onnx.ValueInfoProto(name="StatefulPartitionedCall/MoAt2/predictions_norm/add:0"))
            onnx.save_model(raw_model, self.modified_model_cache_path)
            del raw_model
            end = time.perf_counter()
            print(f"modifying model finished - took {end - start} s")

        model = rt.InferenceSession(self.modified_model_cache_path)
        
        self._predict = functools.partial(
            predict,
            model=model,
            tag_names=tag_names,
            rating_indexes=rating_indexes,
            general_indexes=general_indexes,
            character_indexes=character_indexes,
        )

    def extract(self, file: Path) -> AutotagResult:
        with PIL.Image.open(file) as im:
            return self._predict(
                im,
                general_threshold=self.score_general_threshold,
                character_threshold=self.score_character_threshold,
            )


def load_labels(huggingface_token: str) -> List[str]:
    path = huggingface_hub.hf_hub_download(
        MOAT_MODEL_REPO, LABEL_FILENAME, use_auth_token=huggingface_token
    )

    with open(path) as fp:
        tags = list(csv.DictReader(fp))

    tag_names = [tag["name"] for tag in tags]
    rating_indexes = [i for i, tag in enumerate(tags) if tag["category"] == "9"]
    general_indexes = [i for i, tag in enumerate(tags) if tag["category"] == "0"]
    character_indexes = [i for i, tag in enumerate(tags) if tag["category"] == "4"]
    return tag_names, rating_indexes, general_indexes, character_indexes


def predict(
    image: PIL.Image.Image,
    model: rt.InferenceSession,
    general_threshold: float,
    character_threshold: float,
    tag_names: List[str],
    rating_indexes: List[np.int64],
    general_indexes: List[np.int64],
    character_indexes: List[np.int64],
):
    _, height, width, _ = model.get_inputs()[0].shape

    # Alpha to white
    image = image.convert("RGBA")
    new_image = PIL.Image.new("RGBA", image.size, "WHITE")
    new_image.paste(image, mask=image)
    image = new_image.convert("RGB")
    image = np.asarray(image)

    # PIL RGB to OpenCV BGR
    image = image[:, :, ::-1]

    image = dbimutils.make_square(image, height)
    image = dbimutils.smart_resize(image, height)
    image = image.astype(np.float32)
    image = np.expand_dims(image, 0)

    input_name = model.get_inputs()[0].name
    label_name = model.get_outputs()[0].name
    emb_name = model.get_outputs()[1].name
    probs, emb = model.run([label_name, emb_name], {input_name: image})

    labels = list(zip(tag_names, probs[0].astype(float)))

    # First 4 labels are actually ratings: pick one with argmax
    ratings_names = [labels[i] for i in rating_indexes]
    ratings = [(f"rating:{tag[0]}", TagType.RATING, score) for tag, score in ratings_names if score > general_threshold]

    # Then we have general tags: pick any where prediction confidence > threshold
    general_names = [labels[i] for i in general_indexes]
    general_res = [(tag, None, score) for tag, score in general_names if score > general_threshold]

    # Everything else is characters: pick any where prediction confidence > threshold
    character_names = [labels[i] for i in character_indexes]
    character_res = [(tag, TagType.CHARACTER, score) for tag, score in character_names if score > character_threshold]

    return AutotagResult(
        tags=ratings + general_res + character_res,
        embedding=emb[0],
    )
