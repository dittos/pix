from sqlalchemy import BigInteger, String

from pixdb.schema import IndexField, get_index_name


def test_get_index_name():
    assert get_index_name("Image", [IndexField("created_at", BigInteger, descending=False)]) == "idx_Image_on_created_at"
    assert get_index_name("Image", [IndexField("created_at", BigInteger, descending=True)]) == "idx_Image_on_created_at_desc"
    assert get_index_name("Image", [
        IndexField("tag", String),
        IndexField("created_at", BigInteger, descending=True),
    ]) == "idx_Image_on_tag_and_created_at_desc"
