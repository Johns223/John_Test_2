import io

from shipping import uploads


class FakeUpload:
    def __init__(self, filename, content_type, data, checksum="abc123"):
        self.filename = filename
        self.content_type = content_type
        self.stream = io.BytesIO(data)
        self.size_bytes = len(data)
        self.checksum = checksum


class FakeStore:
    def __init__(self):
        self.attachments = []

    def list_attachments(self, parcel_id):
        return [a for a in self.attachments if a["parcel_id"] == parcel_id]

    def insert_attachment(self, record):
        self.attachments.append(record)


def test_a_photo_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "STORAGE_ROOT", str(tmp_path))
    store = FakeStore()
    upload = FakeUpload("doorstep.jpg", "image/jpeg", b"\xff\xd8\xff\xe0 photo")
    record = uploads.save_attachment(store, "PCL-1", upload)
    assert record["filename"] == "doorstep.jpg"
    assert record["kind"] == "pod"


def test_an_executable_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "STORAGE_ROOT", str(tmp_path))
    store = FakeStore()
    upload = FakeUpload("payload.exe", "application/octet-stream", b"MZ")
    try:
        uploads.save_attachment(store, "PCL-1", upload)
        assert False, "should have been rejected"
    except ValueError:
        pass


def test_images_are_recognised():
    assert uploads.is_image(FakeUpload("a.png", "image/png", b""))
    assert not uploads.is_image(FakeUpload("invoice.pdf", "application/pdf", b""))


def test_the_tracking_page_lists_attachments(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "STORAGE_ROOT", str(tmp_path))
    store = FakeStore()
    uploads.save_attachment(
        store, "PCL-2", FakeUpload("doorstep.jpg", "image/jpeg", b"photo")
    )
    listed = uploads.attachments_for_tracking_page(store, "PCL-2")
    assert len(listed) == 1
    assert listed[0]["filename"] == "doorstep.jpg"
