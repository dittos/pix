from pathlib import Path
from typing import List
from typing_extensions import Annotated
from PIL import Image as PILImage
from tqdm.auto import tqdm
from pix.autotagger.insightface import Face, InsightFaceAutotagger
from pix.model.image import Image, ImageFace, ImageRepo, Vector
from pixdb.doc import Doc
from pixdb.inject import Value


def main(
        image_repo: ImageRepo,
        autotagger: InsightFaceAutotagger,
        images_dir: Annotated[Path, Value],
):
    autotagger.load_model()
    face_images_dir = images_dir / "faces"
    face_images_dir.mkdir(parents=True, exist_ok=True)

    # TODO: make index on `faces is None`
    images = image_repo.list_by_tag_collected_at_desc("realistic", 0, 1000)
    for image in tqdm(images):
        if image.content.faces is not None: continue
        f = images_dir / image.content.local_filename
        result = autotagger.extract(f)
        filenames = save_face_images(image, result, images_dir, face_images_dir)
        image.content.faces = [ImageFace(
            x=face.x,
            y=face.y,
            width=face.width,
            height=face.height,
            embedding=Vector.from_numpy(face.embedding),
            score=face.score,
            local_filename=filename,
        ) for face, filename in zip(result, filenames)]
        image_repo.put(image.id, image.content)


def save_face_images(image: Doc[Image], faces: List[Face], images_dir: Path, face_images_dir: Path):
    filenames = []
    with PILImage.open(images_dir / image.content.local_filename) as im:
        for i, face in enumerate(faces):
            filename = f"{image.id}.{i}.jpg"
            face_im = im.crop((face.x, face.y, face.x + face.width, face.y + face.height))
            face_im.thumbnail((100000, 200))
            face_im.save(face_images_dir / filename)
            filenames.append(filename)
    return filenames
