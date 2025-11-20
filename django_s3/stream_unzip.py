from struct import Struct
import zlib

# sourced from https://github.com/coolaf/stream-unzip/blob/main/stream_unzip.py
def stream_unzip(zipfile_chunks, chunk_size=65536):
    local_file_header_signature = b'\x50\x4b\x03\x04'
    local_file_header_struct = Struct('<H2sHHHIIIHH')
    zip64_compressed_size = 4294967295
    zip64_size_signature = b'\x01\x00'
    central_directory_signature = b'\x50\x4b\x01\x02'

    def get_byte_readers(iterable):
        # Return functions to return/"replace" bytes from/to the iterable
        # - _yield_all: yields chunks as they come up (often for a "body")
        # - _yield_num: yields chunks as the come up, up to a fixed number of bytes
        # - _get_num: returns a single `bytes` of a given length
        # - _return_unused: puts "unused" bytes "back", to be retrieved by a yield/get call

        chunk = b''
        offset = 0
        it = iter(iterable)

        def _yield_all():
            nonlocal chunk
            nonlocal offset

            while True:
                if not chunk:
                    try:
                        chunk = next(it)
                    except StopIteration:
                        break
                prev_offset = offset
                prev_chunk = chunk
                to_yield = min(len(chunk) - offset, chunk_size)
                offset = (offset + to_yield) % len(chunk)
                chunk = chunk if offset else b''
                yield prev_chunk[prev_offset:prev_offset + to_yield]

        def _yield_num(num):
            nonlocal chunk
            nonlocal offset

            while num:
                if not chunk:
                    try:
                        chunk = next(it)
                    except StopIteration:
                        raise ValueError('Fewer bytes than expected in zip') from None
                prev_offset = offset
                prev_chunk = chunk
                to_yield = min(num, len(chunk) - offset, chunk_size)
                offset = (offset + to_yield) % len(chunk)
                chunk = chunk if offset else b''
                num -= to_yield
                yield prev_chunk[prev_offset:prev_offset + to_yield]

        def _get_num(num):
            return b''.join(chunk for chunk in _yield_num(num))

        def _return_unused(unused):
            nonlocal chunk
            nonlocal offset
            if len(unused) <= offset:
                offset -= len(unused)
            else:
                chunk = unused + chunk[offset:]
                offset = 0

        return _yield_all, _yield_num, _get_num, _return_unused

    yield_all, yield_num, get_num, return_unused = get_byte_readers(zipfile_chunks)

    def get_extra_data(extra, desired_signature):
        extra_offset = 0
        while extra_offset != len(extra):
            extra_signature = extra[extra_offset:extra_offset+2]
            extra_offset += 2
            extra_data_size, = Struct('<H').unpack(extra[extra_offset:extra_offset+2])
            extra_offset += 2
            extra_data = extra[extra_offset:extra_offset+extra_data_size]
            extra_offset += extra_data_size
            if extra_signature == desired_signature:
                return extra_data

    def yield_file():
        version, flags, compression, mod_time, mod_date, crc_32_expected, compressed_size, uncompressed_size, file_name_len, extra_field_len = \
            local_file_header_struct.unpack(get_num(local_file_header_struct.size))

        if compression not in [0, 8]:
            raise ValueError('Unsupported compression type {}'.format(compression))

        def _flag_bits():
            for b in flags:
                for i in range(8):
                    yield (b >> i) & 1

        flag_bits = tuple(_flag_bits())
        if (
            flag_bits[0]      # Encrypted
            or flag_bits[4]   # Enhanced deflate (Deflate64)
            or flag_bits[5]   # Compressed patched
            or flag_bits[6]   # Strong encrypted
            or flag_bits[13]  # Masked header values
        ):
            raise ValueError('Unsupported flags {}'.format(flag_bits))

        file_name = get_num(file_name_len)
        extra = get_num(extra_field_len)

        is_zip64 = compressed_size == zip64_compressed_size and uncompressed_size == zip64_compressed_size
        if is_zip64:
            uncompressed_size, compressed_size = Struct('<QQ').unpack(get_extra_data(extra, zip64_size_signature))

        has_data_descriptor = flags == b'\x08\x00'

        if has_data_descriptor:
            uncompressed_size = None

        def _decompress_deflate():
            nonlocal crc_32_expected

            dobj = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
            crc_32_actual = zlib.crc32(b'')
            all_iter = yield_all()

            while not dobj.eof:
                try:
                    compressed_chunk = next(all_iter)
                except StopIteration:
                    raise ValueError('Fewer bytes than expected in zip') from None

                uncompressed_chunk = dobj.decompress(compressed_chunk, chunk_size)
                if uncompressed_chunk:
                    crc_32_actual = zlib.crc32(uncompressed_chunk, crc_32_actual)
                    yield uncompressed_chunk

                while dobj.unconsumed_tail and not dobj.eof:
                    uncompressed_chunk = dobj.decompress(dobj.unconsumed_tail, chunk_size)
                    if uncompressed_chunk:
                        crc_32_actual = zlib.crc32(uncompressed_chunk, crc_32_actual)
                        yield uncompressed_chunk

            return_unused(dobj.unused_data)

            if has_data_descriptor:
                dd_optional_signature = get_num(4)
                dd_so_far_num = \
                    0 if dd_optional_signature == b'PK\x07\x08' else \
                    4
                dd_so_far = dd_optional_signature[:dd_so_far_num]
                dd_remaining = \
                    (20 - dd_so_far_num) if is_zip64 else \
                    (12 - dd_so_far_num)
                dd = dd_so_far + get_num(dd_remaining)
                crc_32_expected, = Struct('<I').unpack(dd[:4])

            if crc_32_actual != crc_32_expected:
                raise ValueError('CRC-32 does not match')

        def _with_crc_32_check(chunks):
            crc_32_actual = zlib.crc32(b'')
            for chunk in chunks:
                crc_32_actual = zlib.crc32(chunk, crc_32_actual)
                yield chunk

            if crc_32_actual != crc_32_expected:
                raise ValueError('CRC-32 does not match')

        uncompressed_bytes = \
            _with_crc_32_check(yield_num(compressed_size)) if compression == 0 else \
            _decompress_deflate()

        return file_name, uncompressed_size, uncompressed_bytes

    while True:
        signature = get_num(len(local_file_header_signature))
        if signature == local_file_header_signature:
            yield yield_file()
        elif signature == central_directory_signature:
            for _ in yield_all():
                pass
            break
        else:
            raise ValueError(b'Unexpected signature ' + signature)