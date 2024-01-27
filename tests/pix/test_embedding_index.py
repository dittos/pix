from pathlib import Path

from pix.embedding_index import EmbeddingIndex


def test_e2e(tmpdir: Path):
    index = EmbeddingIndex()

    import numpy as np
    d = 128
    nb = 10
    np.random.seed(1234) # make reproducible
    xb = np.random.random((nb, d)).astype('float32')
    xb[:, 0] += np.arange(nb) / 1000.

    for i, x in enumerate(xb):
        index.add(f"id{i}", x)

    before_save_result = index.search(xb[0], 5)

    index.save(tmpdir)

    index = EmbeddingIndex()
    index.load(tmpdir)

    after_save_result = index.search(xb[0], 5)

    assert before_save_result == after_save_result
