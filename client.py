"""N3DS adapter and MLDT client.
"""

import logging
from typing import Optional

# This launcher intentionally uses the local emulator bridge implementation.
# Importing the reference `albw.Interface` here causes the launcher to silently
# use the wrong adapter path and skip the process-selection diagnostics we need
# for Azahar/Citra bridge debugging.
N3DSInterface = None


class ConnectionError(Exception):
    pass

logger = logging.getLogger("mldtclient")

# BizHawk to Azahar address conversion
# BizHawk exposes FCRAM-style addresses directly. Azahar exposes the same
# memory in a linear heap starting at 0x14000000. The real conversion for the
# MLDT addresses we use is simply adding the linear heap offset.
# Example: 0x007b1404 (BizHawk) -> 0x147b1404 (Azahar)
BIZHAWK_TO_AZAHAR_OFFSET = 0x14000000


def to_azahar_addr(bizhawk_addr: int) -> int:
    """Translate BizHawk/FCRAM addresses to Azahar linear heap addresses.

    This preserves already-translated Azahar pointers and handles the common
    BizHawk ranges used by MLDT. A direct conversion is required for the
    FCRAM-style pointers seen in the client and in the ROM validation flow.
    """
    addr = int(bizhawk_addr)
    if addr >= BIZHAWK_TO_AZAHAR_OFFSET:
        return addr

    # BizHawk's FCRAM and memory offsets are exposed as a linear pointer space.
    # The Azahar bridge exposes that same data at +0x14000000.
    if 0 <= addr < 0x10000000:
        translated = addr + BIZHAWK_TO_AZAHAR_OFFSET
        #logger.debug("to_azahar_addr: %#x -> %#x", addr, translated)
        return translated

    # Some emulation variants can expose a physical FCRAM PADDR window; map that
    # to the same Azahar linear space used by the emulator bridge.
    if 0x20000000 <= addr < 0x30000000:
        translated = addr - 0x20000000 + BIZHAWK_TO_AZAHAR_OFFSET
        #logger.debug("to_azahar_addr: %#x (physical PADDR) -> %#x", addr, translated)
        return translated

    #logger.debug("to_azahar_addr: leaving non-FCRAM address %#x unchanged", addr)
    return addr


to_azahar_address = to_azahar_addr


# Force the local bridge implementation to be active for the MLDT launcher.
# The reference ALBW adapter is kept for comparison only and is not used here.
if True:
    import asyncio
    import socket
    import struct

    class N3DSAdapter:
        """
        Implements the same packet protocol used by `albw.Interface.N3DSInterface`:
        - UDP port 45987
        - packet header (version,id,type,len)
        - Process selection and read/write semantics

        This allows the adapter to connect to bridges that implement the
        N3DS bridge protocol (Citra/Azahar forks that expose the same API).
        """

        import asyncio
        import socket
        import struct

        PACKET_VERSION: int = 1
        HEADER_SIZE: int = 0x10
        MAX_PACKET_SIZE: int = 0x410
        TIMEOUT: float = 1.0

        def __init__(self) -> None:
            self.id = 0
            self.max_request_size = 32
            self.sock = None
            # Set by _set_process() to the title id that was actually matched,
            # e.g. so the caller can tell NA vs PAL apart after an auto-detect
            # connect() call that was given multiple candidate title ids.
            self.connected_title_id = None

        def _max_read_size(self) -> int:
            return self.max_request_size

        def _max_write_size(self) -> int:
            return self.max_request_size - 8

        async def _send_packet(self, request_type: int, request_data: bytes, response_size: Optional[int] = None, retry: bool = True) -> bytes:
            loop = asyncio.get_running_loop()
            tries = 4 if retry else 1
            for _ in range(tries):
                try:
                    request_id = self.id
                    self.id = (self.id + 1) & 0xffffffff
                    request = struct.pack("=IIII", self.PACKET_VERSION, request_id, request_type, len(request_data))
                    request += request_data
                    await asyncio.wait_for(loop.sock_sendall(self.sock, request), self.TIMEOUT)
                    for _ in range(16):
                        response = await asyncio.wait_for(loop.sock_recv(self.sock, self.MAX_PACKET_SIZE), self.TIMEOUT)
                        if not response or len(response) < self.HEADER_SIZE:
                            break
                        try:
                            version, id, response_type, size = struct.unpack("=IIII", response[:self.HEADER_SIZE])
                        except Exception as e:
                            logger.debug("_send_packet: bad header unpack: %s", e)
                            continue
                        #logger.debug("_send_packet: got response ver=%s id=%s type=%s size=%s payload_len=%s", version, id, response_type, size, len(response)-self.HEADER_SIZE)
                        if version == self.PACKET_VERSION and id == request_id and response_type == request_type:
                            return response[self.HEADER_SIZE:]
                except Exception as e:
                    #logger.debug("_send_packet exception: %s", e)
                    continue
            raise ConnectionError("Lost connection to game")

        async def _set_process(self, titles) -> bool:
            # `titles` may be a single title id (int) or an iterable of
            # acceptable title ids -- e.g. all known regions -- so we can
            # match whichever region build is actually running instead of
            # requiring the caller to guess the right one up front.
            if isinstance(titles, int):
                titles = {titles}
            else:
                titles = set(titles)
            self.connected_title_id = None
            start_process = 0
            while True:
                request_data = struct.pack("=II", start_process, 0x7fffffff)
                try:
                    response = await self._send_packet(3, request_data, retry=False)
                    if len(response) < 4:
                        #print(f"N3DSAdapter._set_process: no process list returned for target titles {[f'{t:#x}' for t in titles]}; game not ready yet")
                        #logger.warning("N3DSAdapter._set_process: no process list returned; game not ready for titles %s", titles)
                        self.max_request_size = 32
                        return False
                    count = struct.unpack("=I", response[0:4])[0]
                    #print(f"N3DSAdapter._set_process: targets={titles} process_count={count} raw={response[:64].hex()}")
                    #logger.info("N3DSAdapter._set_process: titles=%s reported process_count=%d", titles, count)
                    if count == 0:
                        #print(f"N3DSAdapter._set_process: bridge reported zero running processes for titles {titles}")
                        #logger.warning("N3DSAdapter._set_process: bridge reported zero running processes for titles %s", titles)
                        return False
                    start_process += count
                    for i in range(count):
                        entry = response[4 + i * 0x14 : 4 + (i + 1) * 0x14]
                        if len(entry) < 0x14:
                            break
                        # Azahar/Citra process entries are laid out as:
                        #   <proc_id: I, title_id: Q, proc_name: 8s>
                        # for a total of 20 bytes (0x14). The original ALBW logic
                        # used the wrong 16-byte layout and caused the unpack error.
                        proc_id, title_id, proc_name = struct.unpack("<IQ8s", entry)
                        proc_name = proc_name.rstrip(b"\x00").decode("ascii", errors="replace")
                        print(f"N3DSAdapter._set_process: candidate proc_id={proc_id} title_id={title_id:#x} process_name={proc_name!r} targets={[f'{t:#x}' for t in titles]}")
                        #logger.info("N3DSAdapter._set_process: candidate proc_id=%d title_id=%#x process_name=%s targets=%s", proc_id, title_id, proc_name, titles)
                        if title_id in titles:
                            request_data = struct.pack("=II", 1, proc_id)
                            print(f"N3DSAdapter._set_process: selecting proc_id={proc_id} for title {title_id:#x}")
                            #logger.info("N3DSAdapter._set_process: selecting proc_id=%d for title %#x", proc_id, title_id)
                            await self._send_packet(4, request_data, 0)
                            self.max_request_size = 1024
                            self.connected_title_id = title_id
                            return True
                except ConnectionError:
                    print(f"N3DSAdapter._set_process: lost connection while selecting process for titles {[f'{t:#x}' for t in titles]}")
                    logger.warning("N3DSAdapter._set_process: lost connection while selecting process for titles %s", titles)
                    self.max_request_size = 32
                    return True

        async def connect(self, address: str, title) -> bool:
            # `title` may be a single title id (int) or an iterable of
            # candidate title ids to auto-detect the running region from
            # (see _set_process()).
            # close previous socket if any
            try:
                self.disconnect()
            except Exception:
                pass
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Use ALBW default port 45987
            host = address
            port = 45987
            if isinstance(address, str) and ":" in address:
                parts = address.rsplit(":", 1)
                host = parts[0]
                try:
                    port = int(parts[1])
                except Exception:
                    port = 45987
            self.sock.connect((host, port))
            self.sock.setblocking(False)
            try:
                await self._send_packet(0, b"", 0)
                return await self._set_process(title)
            except ConnectionError:
                return False

        def disconnect(self):
            if hasattr(self, 'sock') and self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass

        async def read(self, address: int, size: int) -> bytes:
            # NOTE: no to_azahar_address() translation here. This adapter is
            # used with real process addresses (e.g. from CTRPluginFramework),
            # not BizHawk-relative FCRAM offsets. Translating them here was
            # silently corrupting any address below 0x10000000.
            mem = b""
            import struct as _struct
            while size > 0:
                request_size = min(size, self._max_read_size())
                request_data = struct.pack("=II", address, request_size)
                mem += await self._send_packet(1, request_data, request_size)
                address += request_size
                size -= request_size
            return mem

        async def write(self, address: int, data: bytes) -> None:
            # See note in read() above — no address translation here either.
            start = 0
            while start < len(data):
                end = min(start + self._max_write_size(), len(data))
                request_data = struct.pack("=II", address + start, end - start)
                request_data += data[start:end]
                await self._send_packet(2, request_data, 0, retry=False)
                start += self._max_write_size()

        async def read_u32(self, address: int) -> int:
            return int.from_bytes(await self.read(address, 4), "little")

        async def write_u32(self, address: int, value: int) -> None:
            await self.write(address, value.to_bytes(4, "little"))

else:
    class N3DSAdapter:

        def __init__(self) -> None:
            self._iface = N3DSInterface()

        async def connect(self, address: str, title: int) -> bool:
                # Underlying `N3DSInterface.connect` expects a host (no port).
                # Accept `host:port` addresses here and strip the port when present
                # so callers can provide either format (useful for Azahar/Citra).
                host = address
                if isinstance(address, str) and ":" in address:
                    host = address.rsplit(":", 1)[0]
                return await self._iface.connect(host, title)

        def disconnect(self) -> None:
            self._iface.disconnect()

        async def read(self, address: int, size: int) -> bytes:
            return await self._iface.read(to_azahar_address(address), size)

        async def write(self, address: int, data: bytes) -> None:
            await self._iface.write(to_azahar_address(address), data)

        async def read_u32(self, address: int) -> int:
            return await self._iface.read_u32(to_azahar_address(address))

        async def write_u32(self, address: int, value: int) -> None:
            await self._iface.write_u32(to_azahar_address(address), value)


def create_n3ds_mldt_client(mltd_client_cls, connect_addr: str, password: Optional[str] = None):

    if password is None:
        instance = mltd_client_cls(connect_addr, "")
    else:
        instance = mltd_client_cls(connect_addr, password)

    # attach adapter
    try:
        instance.interface = N3DSAdapter()
    except RuntimeError:
        # surface a clearer error for callers of this helper
        raise RuntimeError("Unable to attach N3DSAdapter: missing 'albw' package in the Launcher environment.")
    # helper flags commonly used by ALBW-style clients
    instance.interface_connected = False
    instance.initial_delay = True
    instance.show_triple_connected_message = True
    instance.show_citra_connect_message = True

    #logger.info("Attached N3DSAdapter to MLDT client instance")
    return instance
