from tqdm.auto import tqdm
from pix.app import create_graph
from pix.autotagger.wd import WdAutotagger
from pix.config import Settings
from pix.model.image import ImageRepo, ImageTag


class Autotag:
    def __init__(
            self,
            settings: Settings,
            image_repo: ImageRepo,
            autotagger: WdAutotagger,
    ):
        self.settings = settings
        self.image_repo = image_repo
        self.autotagger = autotagger

    def handle(self):
        self.autotagger.load_model()

        images = self.image_repo.list_needs_autotagging()
        for image in tqdm(images):
            f = self.settings.images_dir / image.content.local_filename
            tags = self.autotagger.extract(f)
            image.content.tags = [ImageTag(tag=tag, score=score) for tag, score in tags]
            self.image_repo.put(image.id, image.content)


if __name__ == "__main__":
    task = create_graph().get_instance(Autotag)
    task.handle()
