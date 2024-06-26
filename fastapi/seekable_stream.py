# Copyright 2024 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
import io


class SeekableStream(io.RawIOBase):
    """A seekable stream that wraps another stream and buffers read data.

    This class allows to seek and read data from the original stream.
    It buffers read data to allow seeking back to read data again.

    This class is useful to handle the case where the original stream does not
    support seeking, but the data could eventually be read multiple times.
    To avoid reading the original stream a first time to buffer the data, we
    buffer the data as it is read. In this way we do not add delay when the
    data is read only once.
    """

    def __init__(self, original_stream):
        super().__init__()
        self.original_stream = original_stream
        self.buffer = bytearray()
        self.buffer_position = 0
        self.seek_position = 0
        self.end_of_stream = False

    def read(self, size=-1):  # pylint: disable=method-required-super
        if size == -1:
            # Read all remaining data
            size = len(self.buffer) - self.buffer_position
            data_from_buffer = bytes(self.buffer[self.buffer_position :])
            self.buffer_position = len(self.buffer)

            # Read remaining data from the original stream if not already buffered
            remaining_data = self.original_stream.read()
            self.buffer.extend(remaining_data)
            self.end_of_stream = True
            return data_from_buffer + remaining_data

        buffer_len = len(self.buffer)
        remaining_buffer = buffer_len - self.buffer_position

        if remaining_buffer >= size:
            # Read from the buffer if there is enough data
            data = self.buffer[self.buffer_position : self.buffer_position + size]
            self.buffer_position += size
            return bytes(data)
        else:
            # Read remaining buffer data
            data = self.buffer[self.buffer_position :]
            self.buffer_position = buffer_len

            # Read the rest from the original stream
            additional_data = self.original_stream.read(size - remaining_buffer)
            if additional_data is None:
                additional_data = b""

            # Store read data in the buffer
            self.buffer.extend(additional_data)
            self.buffer_position += len(additional_data)
            if len(additional_data) < (size - remaining_buffer):
                self.end_of_stream = True
            return bytes(data + additional_data)

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            new_position = offset
        elif whence == io.SEEK_CUR:
            new_position = self.buffer_position + offset
        elif whence == io.SEEK_END:
            if not self.end_of_stream:
                # Read the rest of the stream to buffer it
                # This is needed to know the total size of the stream
                self.read()
            new_position = len(self.buffer) + offset

        if new_position < 0:
            raise ValueError("Negative seek position {}".format(new_position))

        if new_position <= len(self.buffer):
            self.buffer_position = new_position
        else:
            # Read from the original stream to fill the buffer up to the new position
            to_read = new_position - len(self.buffer)
            additional_data = self.original_stream.read(to_read)
            if additional_data is None:
                additional_data = b""
            self.buffer.extend(additional_data)
            if len(self.buffer) < new_position:
                raise io.UnsupportedOperation(
                    "Cannot seek beyond the end of the stream"
                )
            self.buffer_position = new_position

        return self.buffer_position

    def tell(self):
        return self.buffer_position

    def readable(self):
        return True
