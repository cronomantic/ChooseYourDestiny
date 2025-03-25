import time
import os

from struct import *

################################################################################


class DSK_ERR:
    OK = 0
    BADPTR = -1
    NOMEM = -2
    SYSERR = -6
    NOTRDY = -10
    CTRLR = -23


class P3FS_ERR:
    DISKFULL = 101
    DIRFULL = 102
    EXISTS = 103
    MISALIGN = 104


################################################################################


class DSK_GEOMETRY:
    def __init__(self):
        self.dg_secsize = 0
        self.dg_sectors = 0
        self.dg_cylinders = 0
        self.dg_heads = 0
        self.dg_secbase = 0
        self.dg_sidedness = 0
        self.dg_rwgap = 0
        self.dg_fmtgap = 0

    def dg_pcwgeom(self, bootsec):
        self.dg_sectors = bootsec[3]
        self.dg_secsize = 128 << bootsec[4]
        self.dg_rwgap = bootsec[8]
        self.dg_fmtgap = bootsec[9]
        self.dg_heads = 2 if (bootsec[1] & 3) != 0 else 1
        return DSK_ERR.OK


################################################################################


class DSK_PDRIVER:
    def __init__(self):
        self.fp = None
        self.sectors = 9
        self.secsize = 512
        self.heads = 1
        self.gap = 0

    def dsk_creat(self, name, type):
        try:
            self.fp = open(name, "wb")
            return DSK_ERR.OK
        except IOError:
            return DSK_ERR.SYSERR

    def dsk_open(self, name, type):
        try:
            self.fp = open(name, "rb")
            return DSK_ERR.OK
        except IOError:
            return DSK_ERR.SYSERR

    def dsk_close(self):
        if self.fp:
            self.fp.close()
            self.fp = None
            return DSK_ERR.OK
        return DSK_ERR.BADPTR

    def dsk_alform(self, track, filler):
        try:
            filler = bytes([filler])
            self.fp.seek(track * self.secsize * self.sectors)
            for _ in range(self.secsize * self.sectors):
                self.fp.write(filler)
            return DSK_ERR.OK
        except IOError:
            return DSK_ERR.SYSERR

    def dsk_lwrite(self, buf, sector):
        try:
            self.fp.seek(sector * self.secsize)
            self.fp.write(buf)
            return DSK_ERR.OK
        except IOError:
            return DSK_ERR.SYSERR

    def dsk_set_geom(self, dg):
        self.sectors = dg.dg_sectors
        self.secsize = dg.dg_secsize
        self.heads = dg.dg_heads
        self.gap = dg.dg_fmtgap


################################################################################


class DSK_PDRIVER_EXT(DSK_PDRIVER):
    def __init__(self):
        super().__init__()
        self.type = "raw"
        self.name = ""
        self.tracks = dict()
        self.filler = 0xFE

    def dsk_creat(self, name, type):
        self.type = type
        if self.type == "dsk":
            self.name = name
            self.tracks.clear()
            return DSK_ERR.OK
        else:
            return super().dsk_creat(name=name, type=type)

    def dsk_open(self, name, type):
        self.type = type
        if self.type == "dsk":
            self.name = name
            self.tracks.clear()
            return DSK_ERR.OK
        else:
            return super().dsk_open(name=name, type=type)

    def dsk_alform(self, track, filler):
        if self.type == "dsk":
            self.filler = filler & 0xFF
            track_data = []
            for s in range(self.sectors):
                track_data.append(bytearray([self.filler for _ in range(self.secsize)]))
            self.tracks[track] = track_data
            return DSK_ERR.OK
        else:
            return super().dsk_alform(track=track, filler=filler)

    def dsk_lwrite(self, buf, sector):
        if self.type == "dsk":
            track_pos = sector // self.sectors
            sector_pos = sector % self.sectors
            if len(self.tracks[track_pos][sector_pos]) != self.secsize:
                return DSK_ERR.SYSERR
            for p in range(self.secsize):
                self.tracks[track_pos][sector_pos][p] = buf[p]
            return DSK_ERR.OK
        else:
            return super().dsk_lwrite(buf=buf, sector=sector)

    def dsk_close(self):
        if self.type == "dsk":
            err = super().dsk_creat(name=self.name, type=self.type)
            if err != DSK_ERR.OK:
                return err
            disk_image = self.make_dsk_image()
            self.fp.write(disk_image)
            return super().dsk_close()
        else:
            return super().dsk_close()

    def make_dsk_image(self):
        num_tracks = max(self.tracks.keys()) + 1
        num_tracks = num_tracks // self.heads
        track_size = 0x100 + (self.sectors * self.secsize)
        # print(f"->{num_tracks} {self.heads} {track_size}\n")

        disk_image = bytearray()
        disk_image += pack(
            "<34s", "MV - CPCEMU Disk-File\r\nDisk-Info\r\n".encode("ascii")
        )
        disk_image += pack("<14s", "[Cronomantic]".encode("ascii"))
        disk_image += pack("<BBH", num_tracks, self.heads, track_size)
        disk_image += bytearray([0 for _ in range(0x100 - len(disk_image))])

        for t in self.tracks.keys():
            tr = t // self.heads
            si = t % self.heads
            trk = self.tracks[t]

            track_header = bytearray()
            track_header += pack("<16s", "Track-Info\r\n".encode("ascii"))
            track_header += pack(
                "<BBBBBBBB",
                tr,
                si,
                1,
                2,
                self.secsize // 256,
                self.sectors,
                self.gap,
                self.filler,
            )
            track_data = bytearray()
            for i, s in enumerate(trk):
                track_header += pack(
                    "<BBBBBBBB",
                    tr,
                    si,
                    i + 1,
                    self.secsize // 256,
                    0,
                    0,
                    0,
                    0,
                )
                track_data += s
                # print(f"-Side {si} Track {tr} Sector {i + 1}: {track_header}\n")
            disk_image += (
                track_header
                + bytearray([0 for _ in range(0x100 - len(track_header))])
                + track_data
            )
        return disk_image


################################################################################


class PLUS3FS:
    def __init__(self, dsk_report):
        self.dsk_report = dsk_report
        self.drive = None
        self.geom = DSK_GEOMETRY()
        self.bootsec = None
        self.cpmdir = None
        self.dosdir = None
        self.dosfat = None
        self.nextblock = 0
        self.blocksize = 0
        self.maxblock = 0
        self.maxtrack = 0
        self.offset = 0
        self.maxdir = 0
        self.dirblocks = 0
        self.timestamped = 0
        self.clustersize = 0
        self.cluster_offset = 0
        self.exm = 0

    def p3fs_umount(self):
        if self is None:
            return DSK_ERR.BADPTR
        self.p3fs_sync()
        err = self.drive.dsk_close()
        # Free fs.bootsec and fs.dosdir by setting to None.
        self.bootsec = None
        if self.dosdir is not None:
            self.dosdir = None
        # Zero out fs object attributes
        self.drive = None
        self.geom = DSK_GEOMETRY()
        self.cpmdir = None
        self.dosfat = None
        self.nextblock = 0
        self.blocksize = 0
        self.maxblock = 0
        self.maxtrack = 0
        self.offset = 0
        self.maxdir = 0
        self.dirblocks = 0
        self.timestamped = 0
        self.clustersize = 0
        self.cluster_offset = 0
        self.exm = 0
        return err

    def p3fs_mkfs(self, name, type, dsk_format, boot_spec, timestamped):
        heads = 2 if (boot_spec[1] & 3) != 0 else 1
        # Work out how big the buffers for the boot sector and directory need to be.
        # Start by getting the drive geometry straight.
        err = self.geom.dg_pcwgeom(boot_spec)
        if err != DSK_ERR.OK:
            return err
        self.blocksize = 128 << boot_spec[6]  # Block size
        self.offset = boot_spec[5]  # Reserved tracks
        self.maxtrack = heads * boot_spec[2]
        self.dirblocks = boot_spec[7]
        self.nextblock = self.dirblocks  # First free block
        self.maxdir = (self.dirblocks * self.blocksize) // 32
        # Max block number is number of usable sectors divided by sectors per block
        self.maxblock = ((self.maxtrack - self.offset) * self.geom.dg_sectors) // (
            self.blocksize // self.geom.dg_secsize
        )
        self.maxblock -= 1
        if self.maxblock < 256:
            self.exm = (self.blocksize // 1024) - 1
        else:
            self.exm = (self.blocksize // 2048) - 1
        # Allocate the buffers
        total_bootsec = self.geom.dg_secsize + 32 * self.maxdir
        self.bootsec = bytearray(total_bootsec)
        if not self.bootsec:
            return DSK_ERR.NOMEM
        # cpmdir is a memoryview into bootsec starting at offset geom.dg_secsize
        self.cpmdir = memoryview(self.bootsec)[self.geom.dg_secsize :]
        memset(self.bootsec, 0, self.geom.dg_secsize, 0xE5)
        memset(self.cpmdir, 0, 32 * self.maxdir, 0xE5)
        self.timestamped = timestamped
        if timestamped:
            for dirent in range(3, self.maxdir, 4):
                memset(self.cpmdir, dirent * 32, 32, 0)
                # Assign first byte to 0x21
                self.cpmdir[dirent * 32] = 0x21
        memcpy(self.bootsec, 0, boot_spec, 0, 10)

        # Create a new DSK file
        self.drive = DSK_PDRIVER_EXT()
        self.drive.dsk_set_geom(self.geom)
        err = self.drive.dsk_creat(name, type)
        if err != DSK_ERR.OK:
            return err
        # Format all its tracks
        for track in range(self.maxtrack):
            msg = f"Formatting track {track}/{self.maxtrack}"
            self.dsk_report(msg)
            if err == DSK_ERR.OK:
                err = self.drive.dsk_alform(track, 0xE5)
        self.dsk_report("Writing boot sector")
        if err == DSK_ERR.OK:
            err = self.drive.dsk_lwrite(self.bootsec, 0)
        return err

    def p3fs_new_dirent(self):
        # Returns an integer offset into fs.cpmdir if found, else None.
        for n in range(self.maxdir):
            offset = n * 32
            if self.cpmdir[offset] == 0xE5:
                return offset
        return None

    def p3fs_findextent(self, uid, extent, name):
        for n in range(self.maxdir):
            offset = n * 32
            dirent = self.cpmdir[offset : offset + 32]
            if dirent[0] != uid:
                continue
            m = 0
            for m in range(11):
                if (dirent[m + 1] & 0x7F) != (name[m] & 0x7F):
                    break
            if m == 10:
                # In C, m==11 means full match, but our loop runs 0..10.
                # We check if all 11 characters match.
                ext = dirent[12] + 32 * dirent[14]
                ext //= self.exm + 1
                if ext == extent:
                    return offset
        return None

    def p3fs_exists(self, uid, name):
        return self.p3fs_findextent(uid, 0, name) is not None

    def p3fs_creat(self, uid, name):
        # Can't overwrite existing, since we have no p3fs_unlink.
        if self.p3fs_exists(uid, name):
            return (P3FS_ERR.EXISTS, None)
        fp = PLUS3FILE(self)
        # Allocate buffer with size fs.blocksize (if not already allocated)
        fp.buf = bytearray(self.blocksize)
        fp.bufptr = 0
        fp.extent = 0
        memset(fp.buf, 0, self.blocksize, 0x1A)
        fp.dirent = self.p3fs_new_dirent()
        if fp.dirent is None:
            # Directory full
            return (P3FS_ERR.DIRFULL, None)
        # Calculate directory entry index n from pointer
        n = fp.dirent // 32
        memset(self.cpmdir, fp.dirent, 32, 0)
        self.cpmdir[fp.dirent] = uid
        # Copy 11 bytes from name to directory entry starting at offset 1
        for i in range(11):
            self.cpmdir[fp.dirent + 1 + i] = name[i] if i < len(name) else ord(" ")
        # Check for stamping: if fs.cpmdir[(n|3)*32] == 0x21
        stamp_index = (n | 3) * 32
        if self.cpmdir[stamp_index] == 0x21:
            # fp.stamp = fs.cpmdir + (n|3)*32 + 1 + ((n & 3)*10)
            fp.stamp = stamp_index + 1 + ((n & 3) * 10)
            stamp_now(self.cpmdir[fp.stamp : fp.stamp + 4])
            stamp_now(self.cpmdir[fp.stamp + 4 : fp.stamp + 8])
        else:
            fp.stamp = None
        return (DSK_ERR.OK, fp)

    def lookup_block(self, block):
        # Sector of block 0
        off = self.offset * self.geom.dg_sectors
        return off + (self.blocksize // self.geom.dg_secsize) * block

    def p3fs_sync(self):
        base = 0
        for block in range(self.dirblocks):
            blk = self.lookup_block(block)
            n = 0
            while n < self.blocksize:
                block_data = self.cpmdir[base : base + self.geom.dg_secsize]
                err = self.drive.dsk_lwrite(block_data, blk)
                if err:
                    return err
                blk += 1
                base += self.geom.dg_secsize
                n += self.geom.dg_secsize
        return DSK_ERR.OK

    def get_alloc(self, src):
        if self.maxblock <= 255:
            return src[0]
        return src[0] + 256 * src[1]

    def put_fat(self, cluster, value):
        offset = (cluster // 2) * 3
        if cluster & 1:
            self.dosfat[offset + 1] &= 0x0F
            self.dosfat[offset + 1] |= (value << 4) & 0xF0
            self.dosfat[offset + 2] = (value >> 4) & 0xFF
        else:
            self.dosfat[offset] = value & 0xFF
            self.dosfat[offset + 1] &= 0xF0
            self.dosfat[offset + 1] |= (value >> 8) & 0x0F

    def p3fs_filesize(self, uid, filename):
        lrbc = 0
        extent = 0
        size = 0
        while True:
            dirent_offset = self.p3fs_findextent(
                uid,
                extent,
                filename.decode() if isinstance(filename, bytes) else filename,
            )
            if dirent_offset is None:
                break
            dirent = self.cpmdir[dirent_offset : dirent_offset + 32]
            if extent == 0:
                lrbc = dirent[13] & 0x7F
            size += (dirent[12] & self.exm) * 16384
            size += dirent[15] * 128
            extent += 1
        if lrbc:
            size -= 0x80
            size += lrbc
        return size

    def find_cluster(self, uid, filename, offset):
        # Given a position in the file, determine what DOS cluster it falls in
        ext = offset // (16384 * (self.exm + 1))
        dirent_offset = self.p3fs_findextent(uid, ext, filename)
        if dirent_offset is None:
            return 0xFFF
        offset = offset % (16384 * (self.exm + 1))
        data = dirent_offset + 16  # start of block list in dirent
        while offset >= self.blocksize:
            if self.maxblock >= 256:
                data += 2
            else:
                data += 1
            offset -= self.blocksize
        if self.maxblock >= 256:
            block = self.cpmdir[data] + 256 * self.cpmdir[data + 1]
        else:
            block = self.cpmdir[data]
        block -= self.dirblocks
        multi = self.blocksize // self.clustersize
        block *= multi
        while offset >= self.clustersize:
            block += 1
            offset -= self.clustersize
        block += self.cluster_offset + 2
        return block

    def label_to_dos(cpm_dirent, dos_dirent):
        # Copy 11 bytes from cpm_dirent+1 to dos_dirent
        for i in range(11):
            dos_dirent[i] = cpm_dirent[1 + i]
        dos_dirent[11] = 8  # Label
        stamp2dos(cpm_dirent[24:28], dos_dirent[22:26])

    def file_to_dos(self, cpm_dirent, dos_dirent):
        stamp = None
        filename = "%-11.11s" % "".join([chr(c) for c in cpm_dirent[1:12]])
        size = self.p3fs_filesize(cpm_dirent[0], filename)
        for i in range(11):
            dos_dirent[i] = cpm_dirent[1 + i]
        dos_dirent[0x1C] = size & 0xFF
        dos_dirent[0x1D] = (size >> 8) & 0xFF
        dos_dirent[0x1E] = (size >> 16) & 0xFF
        dos_dirent[0x1F] = (size >> 24) & 0xFF
        prev = -1
        offset_val = 0
        while size > 0:
            cur = self.find_cluster(cpm_dirent[0], filename, offset_val)
            if prev == -1:
                dos_dirent[0x1A] = cur & 0xFF
                dos_dirent[0x1B] = (cur >> 8) & 0xFF
            else:
                self.put_fat(prev, cur)
            prev = cur
            offset_val += self.clustersize
            size -= self.clustersize
        if prev != -1:
            self.put_fat(prev, 0xFFF)

    def p3fs_dossync(self, format, dosonly):
        err = DSK_ERR.OK
        sec = 0
        # Zero out boot sector from offset 11
        memset(self.bootsec, 11, self.geom.dg_secsize - 11, 0)
        self.bootsec[11] = self.geom.dg_secsize & 0xFF
        self.bootsec[12] = (self.geom.dg_secsize >> 8) & 0xFF  # Sector size
        self.bootsec[14] = 1  # Reserved sectors
        self.bootsec[15] = 0
        self.bootsec[16] = 2  # FAT copies
        self.bootsec[18] = 0
        self.bootsec[23] = 0
        self.bootsec[24] = 9  # Sectors / track
        self.bootsec[25] = 0
        self.bootsec[27] = 0
        # Switch format
        if format == 720:
            self.bootsec[13] = 2  # Sectors / cluster
            self.bootsec[17] = 112  # Root dir entries
            self.bootsec[19] = 0xA0
            self.bootsec[20] = 5  # Total sectors
            self.bootsec[21] = 0xF9  # Media descriptor
            self.bootsec[22] = 3  # Sectors / FAT
            self.bootsec[26] = 2  # Heads
            cluster_add = 10  # Skip 10k
        elif format == 180:
            self.bootsec[13] = 1  # Sectors / cluster
            self.bootsec[17] = 64  # Root dir entries
            self.bootsec[19] = 0x68
            self.bootsec[20] = 1  # Total sectors
            self.bootsec[21] = 0xFC  # Media descriptor
            self.bootsec[22] = 2  # Sectors / FAT
            self.bootsec[26] = 1  # Heads
            cluster_add = 4  # Skip 2k
        self.clustersize = self.bootsec[13] * self.geom.dg_secsize
        if dosonly:
            self.bootsec[0] = 0xEB
            self.bootsec[1] = 0x40
            self.bootsec[2] = 0x90
            self.bootsec[3:11] = bytearray("IBM  3.3", "ascii")
            self.bootsec[0x42] = 0xCD
            self.bootsec[0x43] = 0x18
            self.bootsec[self.geom.dg_secsize - 2] = 0x55
            self.bootsec[self.geom.dg_secsize - 1] = 0xAA
        dirlen = self.bootsec[17] * 32
        fatlen = self.bootsec[22] * self.geom.dg_secsize
        self.dosdir = bytearray(dirlen + fatlen)
        if not self.dosdir:
            return DSK_ERR.NOMEM
        memset(self.dosdir, 0, dirlen + fatlen, 0)
        self.dosfat = memoryview(self.dosdir)[dirlen:]
        self.dosfat[0] = self.bootsec[21]
        self.dosfat[1] = 0xFF
        self.dosfat[2] = 0xFF
        dirsecs = (dirlen + self.geom.dg_secsize - 1) // self.geom.dg_secsize
        sec = self.lookup_block(self.dirblocks)
        sec -= self.bootsec[14]  # Boot sector
        sec -= self.bootsec[16] * self.bootsec[22]  # FATs
        sec -= dirsecs
        self.cluster_offset = sec // self.bootsec[13]
        if (self.cluster_offset * self.bootsec[13]) != sec:
            return P3FS_ERR.MISALIGN
        dos_dirent = 0  # offset into self.dosdir
        ndos = 0
        ncpm = 0
        while ncpm < self.maxdir:
            if ndos >= self.bootsec[19]:
                break  # DOS dir full
            cpm_dirent_offset = ncpm * 32
            cpm_dirent = self.cpmdir[cpm_dirent_offset : cpm_dirent_offset + 32]
            if cpm_dirent[0] == 0x20:  # Label
                self.label_to_dos(cpm_dirent, self.dosdir[dos_dirent : dos_dirent + 32])
                ndos += 1
                dos_dirent += 32
                ncpm += 1
                continue
            if cpm_dirent[0] < 0x10:  # File
                extent = cpm_dirent[14] * 32 + cpm_dirent[12]
                extent //= self.exm + 1
                if extent == 0:
                    self.file_to_dos(
                        cpm_dirent, self.dosdir[dos_dirent : dos_dirent + 32]
                    )
                    ndos += 1
                    dos_dirent += 32
            ncpm += 1
        if not dosonly:
            ncpm = self.dirblocks * (self.blocksize // self.clustersize)
            sec_val = self.cluster_offset + 2  # First real cluster
            for ndos in range(ncpm - 1, -1, -1):
                sec_val -= 1
                self.put_fat(sec_val, 0xFF7)
        sec = 0
        err = self.drive.dsk_lwrite(self.bootsec, sec)
        sec += 1
        if err == DSK_ERR.OK:
            for ndos in range(self.bootsec[16]):
                for ncpm in range(0, fatlen, self.geom.dg_secsize):
                    err = self.drive.dsk_lwrite(
                        self.dosfat[ncpm : ncpm + self.geom.dg_secsize],
                        sec,
                    )
                    sec += 1
                    if err != DSK_ERR.OK:
                        break
        if err == DSK_ERR.OK:
            for ndos in range(0, dirlen, self.geom.dg_secsize):
                err = self.drive.dsk_lwrite(
                    self.dosdir[ndos : ndos + self.geom.dg_secsize],
                    sec,
                )
                sec += 1
        return err

    def p3fs_setlabel(self, name):
        if not self.timestamped:
            return DSK_ERR.OK
        dirent = self.p3fs_new_dirent()
        if dirent is None:
            return P3FS_ERR.DIRFULL
        memset(self.cpmdir, dirent, 32, 0)
        self.cpmdir[dirent] = 0x20
        for i in range(11):
            self.cpmdir[dirent + 1 + i] = name[i] if i < len(name) else ord(" ")
        self.cpmdir[dirent + 12] = 0x31  # Label exists: Create & update stamps
        stamp_now(self.cpmdir[dirent + 24 : dirent + 28])
        stamp_now(self.cpmdir[dirent + 28 : dirent + 32])
        return DSK_ERR.OK


################################################################################


class PLUS3FILE:
    def __init__(self, fs):
        self.fs = fs
        self.bufptr = 0
        self.extent = 0
        self.dirent = None
        self.stamp = None
        self.buf = None

    def write_block(self, buf, length):
        n = 0
        err = DSK_ERR.OK
        blk = self.fs.lookup_block(self.fs.nextblock)
        # Firstly actually write the data
        while n < self.fs.blocksize:
            err = self.fs.drive.dsk_lwrite(buf[n : n + self.fs.geom.dg_secsize], blk)
            if err != DSK_ERR.OK:
                return err
            blk += 1
            n += self.fs.geom.dg_secsize
        # Now allocate it in the directory entry
        # Since fs.cpmdir is a memoryview into a bytearray, we compute offset fp.dirent.
        if self.fs.cpmdir[self.dirent + 15] >= 0x80 and (
            (self.dirent and self.fs.cpmdir[self.dirent + 12] & self.fs.exm)
            == self.fs.exm
        ):
            # Directory entry full. Need a new one.
            de2 = self.fs.p3fs_new_dirent()
            if de2 is None:
                return P3FS_ERR.DIRFULL
            memset(self.fs.cpmdir, de2, 32, 0)
            # Copy 13 bytes from old dirent to new one
            for i in range(13):
                self.fs.cpmdir[de2 + i] = self.fs.cpmdir[self.dirent + i]
            self.fs.cpmdir[de2 + 12] = (self.fs.cpmdir[de2 + 12] + 1) & 0xFF
            if self.fs.cpmdir[de2 + 12] >= 32:
                self.fs.cpmdir[de2 + 14] = (self.fs.cpmdir[de2 + 14] + 1) & 0xFF
                self.fs.cpmdir[de2 + 12] = (self.fs.cpmdir[de2 + 12] - 32) & 0xFF
            self.dirent = de2
        elif self.fs.cpmdir[self.dirent + 15] > 0x80:
            self.fs.cpmdir[self.dirent + 15] = (
                self.fs.cpmdir[self.dirent + 15] - 0x80
            ) & 0xFF
            self.fs.cpmdir[self.dirent + 12] = (
                self.fs.cpmdir[self.dirent + 12] + 1
            ) & 0xFF
        if self.fs.maxblock <= 255:
            for n in range(16, 32):
                if self.fs.cpmdir[self.dirent + n] == 0:
                    self.fs.cpmdir[self.dirent + n] = self.fs.nextblock & 0xFF
                    break
        else:
            for n in range(16, 32, 2):
                if (
                    self.fs.cpmdir[self.dirent + n] == 0
                    and self.fs.cpmdir[self.dirent + n + 1] == 0
                ):
                    self.fs.cpmdir[self.dirent + n] = self.fs.nextblock & 0xFF
                    self.fs.cpmdir[self.dirent + n + 1] = (
                        self.fs.nextblock >> 8
                    ) & 0xFF
                    break
        self.fs.cpmdir[self.dirent + 15] = (
            self.fs.cpmdir[self.dirent + 15] + ((length + 127) // 128)
        ) & 0xFF
        self.fs.cpmdir[self.dirent + 13] = length & 0x7F
        self.fs.nextblock += 1
        if self.stamp is not None:
            stamp_now(self.fs.cpmdir[self.stamp + 4 : self.stamp + 8])
        return DSK_ERR.OK

    def p3fs_flush(self):
        if self.bufptr == 0:
            return DSK_ERR.OK
        res = self.write_block(self.buf, self.bufptr)
        self.bufptr = 0
        return res

    def p3fs_close(self):
        err = self.p3fs_flush()
        # Free fp by letting garbage collection reclaim it.
        return err

    def p3fs_putc(self, c):
        if self.bufptr >= self.fs.blocksize:
            res = self.p3fs_flush()
            if res != DSK_ERR.OK:
                return res
        self.buf[self.bufptr] = c
        self.bufptr += 1
        return DSK_ERR.OK


################################################################################


def p3fs_error_check(err):
    return err == DSK_ERR.OK


def p3fs_strerror(err):
    if err == P3FS_ERR.DISKFULL:
        return "Disk full."
    elif err == P3FS_ERR.DIRFULL:
        return "Directory full."
    elif err == P3FS_ERR.EXISTS:
        return "File exists."
    elif err == P3FS_ERR.MISALIGN:
        return "DOS clusters don't align with CP/M blocks."
    else:
        return dsk_strerror(err)


def p3fs_label(label, fcbname):
    namebuf = "{:<11.11s}".format(label)
    str2fbcname(namebuf, fcbname)


def p3fs_83name(name, fcbname):
    filename, extension = os.path.splitext(name)
    filename = "{:<8.8s}".format(filename)
    extension = "{:<4.4s}".format(extension)
    namebuf = filename + extension[1:]  # Skip the point
    str2fbcname(namebuf, fcbname)


def str2fbcname(name, fcbname):
    for i in range(len(fcbname)):
        fcbname[i] = ord(" ")

    for n in range(len(name)):
        ch_val = ord(name[n]) & 0x7F
        ch = chr(ch_val)
        if ch < "!" or ch in ".:;<>[]":
            ch = " "
        ch = ch.upper()
        fcbname[n] = ord(ch)


def dec2bcd(v):
    return (v % 10) + 16 * (v // 10)


def bcd2dec(v):
    return (v % 10) + 10 * (v // 16)


def stamp2dos(cpmstamp, dosstamp):

    cpmdays = 256 * cpmstamp[1] + cpmstamp[0]
    secs = (cpmdays + 2921) * 86400
    secs += 3600 * bcd2dec(cpmstamp[2])
    secs += 60 * bcd2dec(cpmstamp[3])

    ptime = time.gmtime(secs)

    # In C, ptime->tm_year is years since 1900.
    # In Python, time.gmtime() returns tm_year as the full year.
    # We subtract 1900 to match the C behavior.
    tm_year = ptime.tm_year - 1900

    dosdate = (tm_year - 80) << 9
    # In C, tm_mon is 0-based; Python's tm_mon is 1-based, so the effect of (tm_mon + 1)
    # in C is equivalent to tm_mon in Python.
    dosdate |= (ptime.tm_mon & 0x0F) << 5
    dosdate |= ptime.tm_mday & 0x1F
    dostime = (ptime.tm_hour) << 11
    dostime |= (ptime.tm_min & 0x3F) << 5

    dosstamp[0] = dostime & 0xFF
    dosstamp[1] = dostime >> 8
    dosstamp[2] = dosdate & 0xFF
    dosstamp[3] = dosdate >> 8


def stamp_now(stamp):
    t = 0
    ptm = None
    days = 0
    leap = 0
    for i in range(4):
        stamp[i] = 0
    t = time.time()
    ptm = time.localtime(t)
    if not ptm:
        return
    # /* CP/M day count */
    # In C, ptm.tm_year is years since 1900.
    year = ptm.tm_year - 1900

    if year >= 78:
        leap = (year - 76) // 4
        leap *= 1461  # Days since 1 Jan 1976
        days = (year % 4) * 365
        if days != 0:
            days += 1
        days += ptm.tm_yday - 1  # tm_yday is 1-366 on python instead of 0-365
        days += leap
        days -= 730  # Rebase to 1 Jan 1978
        stamp[0] = days & 0xFF
        stamp[1] = days >> 8
    stamp[2] = dec2bcd(ptm.tm_hour)
    stamp[3] = dec2bcd(ptm.tm_min)


def dsk_strerror(err):
    if err == DSK_ERR.NOMEM:
        return "Out of memory."
    elif err == DSK_ERR.BADPTR:
        return "Bad pointer."
    elif err == DSK_ERR.SYSERR:
        return "SYSTEM ERROR"
    elif err == DSK_ERR.OK:
        return "No error."
    else:
        return "Unknown error."


def dsk_get_psh(secsize):
    psh = 0
    while secsize > 128:
        secsize //= 2
        psh += 1
    return psh


# Helper memory functions to mimic memset and memcpy on bytearray
def memset(buf, offset, length, value):
    for i in range(offset, offset + length):
        buf[i] = value


def memcpy(dest, d_offset, src, s_offset, length):
    for i in range(length):
        dest[d_offset + i] = src[s_offset + i]
