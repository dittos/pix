from pathlib import Path
from typing import List, Mapping, Tuple, Union
import numpy as np
import faiss


class EmbeddingIndex:
    _INDEX_FILENAME = "index"
    _ID_FILENAME = "ids"

    def __init__(self) -> None:
        self._index: Union[faiss.IndexFlatIP, None] = None
        self._doc_ids = []
    
    def _ensure_index(self, dim: Union[int, None]):
        if self._index is None:
            self._index = faiss.IndexFlatIP(dim)
            return self._index
        
        if self._index.d != dim:
            raise ValueError(f"index dimension is but {self._index.d} tried to add {dim}")
        
        return self._index

    def add(self, doc_id: str, emb: np.array):
        index = self._ensure_index(emb.shape[-1])
        xb = np.stack([emb])
        faiss.normalize_L2(xb)
        index.add(xb)
        self._doc_ids.append(doc_id)
    
    def search(self, emb: np.array, top_k: int) -> List[Tuple[str, float]]:
        xb = np.stack([emb])
        faiss.normalize_L2(xb)
        distances, indices = self._ensure_index(emb.shape[-1]).search(xb, top_k)
        return [(self._doc_ids[i], float(distance)) for i, distance in zip(indices[0], distances[0]) if i != -1]

    def load(self, dir: Path):
        self._index = faiss.read_index(str(dir / EmbeddingIndex._INDEX_FILENAME))
        with (dir / EmbeddingIndex._ID_FILENAME).open() as fp:
            self._doc_ids = [x.rstrip() for x in fp]

    def save(self, dir: Path):
        faiss.write_index(self._index, str(dir / EmbeddingIndex._INDEX_FILENAME))
        with (dir / EmbeddingIndex._ID_FILENAME).open("w") as fp:
            fp.writelines(x + "\n" for x in self._doc_ids)


class EmbeddingIndexManager:
    def __init__(self, dir: Path):
        self.dir = dir
        self._index: Union[EmbeddingIndex, None] = None
        self._last_modified = -1
    
    def search(self, emb: np.array, top_k: int) -> List[Tuple[str, float]]:
        index = self._load_index()
        return index.search(emb, top_k)

    def _load_index(self) -> EmbeddingIndex:
        mtime = (self.dir / EmbeddingIndex._INDEX_FILENAME).stat().st_mtime

        if self._index is not None and self._last_modified != mtime:
            self._index = None

        if self._index is None:
            index = EmbeddingIndex()
            index.load(self.dir)
            self._index = index
            self._last_modified = mtime
        return self._index


class MultiEmbeddingIndexManager:
    def __init__(self, dirs: Mapping[str, Path]):
        self.dirs = dirs
        self.managers = {
            name: EmbeddingIndexManager(dir)
            for name, dir in dirs.items()
        }
    
    def get_manager(self, name: str):
        return self.managers[name]
