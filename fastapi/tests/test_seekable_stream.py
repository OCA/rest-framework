import io
import random

from odoo.tests.common import TransactionCase

from ..seekable_stream import SeekableStream


class TestSeekableStream(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # create a random large content
        cls.original_content = random.randbytes(1024 * 1024)

    def setUp(self):
        super().setUp()
        self.original_stream = NonSeekableStream(self.original_content)

    def test_read_all(self):
        self.assertFalse(self.original_stream.seekable())
        stream = SeekableStream(self.original_stream)
        data = stream.read()
        self.assertEqual(data, self.original_content)
        stream.seek(0)
        data = stream.read()
        self.assertEqual(data, self.original_content)

    def test_read_partial(self):
        self.assertFalse(self.original_stream.seekable())
        stream = SeekableStream(self.original_stream)
        data = stream.read(10)
        self.assertEqual(data, self.original_content[:10])
        data = stream.read(10)
        self.assertEqual(data, self.original_content[10:20])
        # read the rest
        data = stream.read()
        self.assertEqual(data, self.original_content[20:])

    def test_seek(self):
        self.assertFalse(self.original_stream.seekable())
        stream = SeekableStream(self.original_stream)
        stream.seek(10)
        self.assertEqual(stream.tell(), 10)
        data = stream.read(10)
        self.assertEqual(data, self.original_content[10:20])
        stream.seek(0)
        self.assertEqual(stream.tell(), 0)
        data = stream.read(10)
        self.assertEqual(data, self.original_content[:10])

    def test_seek_relative(self):
        self.assertFalse(self.original_stream.seekable())
        stream = SeekableStream(self.original_stream)
        stream.seek(10)
        self.assertEqual(stream.tell(), 10)
        stream.seek(5, io.SEEK_CUR)
        self.assertEqual(stream.tell(), 15)
        data = stream.read(10)
        self.assertEqual(data, self.original_content[15:25])

    def test_seek_end(self):
        self.assertFalse(self.original_stream.seekable())
        stream = SeekableStream(self.original_stream)
        stream.seek(-10, io.SEEK_END)
        self.assertEqual(stream.tell(), len(self.original_content) - 10)
        data = stream.read(10)
        self.assertEqual(data, self.original_content[-10:])
        stream.seek(0, io.SEEK_END)
        self.assertEqual(stream.tell(), len(self.original_content))
        data = stream.read(10)
        self.assertEqual(data, b"")
        stream.seek(-len(self.original_content), io.SEEK_END)
        self.assertEqual(stream.tell(), 0)
        data = stream.read(10)


class NonSeekableStream(io.BytesIO):
    def seekable(self):
        return False

    def seek(self, offset, whence=io.SEEK_SET):
        raise io.UnsupportedOperation("seek")

    def tell(self):
        raise io.UnsupportedOperation("tell")
