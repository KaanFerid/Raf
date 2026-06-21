# Packaging and Standardization Documentation

The Raf application is distributed as a standard `.deb` package suitable for Debian-based operating systems (Pardus, Debian, Ubuntu).

## 1. Package Policy & Lintian Compliance

In compliance with the Debian package checker **Lintian** and general Debian packaging standards, the package integrates the following compliance features:

- **MD5 Checksums (`md5sums`)**: MD5 hashes of all packed files are calculated and written to the `md5sums` configuration file under `control.tar.gz` to verify integrity during installation.
- **Copyright Declaration (`copyright`)**: Per Debian standards, licensing and copyright summaries are located in `/usr/share/doc/<package-name>/copyright`. This file is bundled with strict `0o644` read-only permissions during package compilation.

## 2. Compilation Channels

The project can be packaged using two alternative channels:

### Standard Channel (`scripts/build_deb.sh`)
If the packaging utility `dpkg-deb` is installed on the host system, this script:
1. Allocates the temporary directory `build/raf-pkg`.
2. Copies codebase source directories and configuration targets to this path.
3. Automatically computes file MD5 sums to generate `DEBIAN/md5sums`.
4. Enforces strict directory and file permissions (`0o755` and `0o644`).
5. Invokes `dpkg-deb --build` to compile the final `.deb` archive.

### Pure-Python Channel (`scripts/build_deb.py`)
Useful in developer environments lacking standard `dpkg` utilities (e.g. Arch Linux, Windows). This script:
1. Utilizes the standard library `tarfile` module to construct `control.tar.gz` and `data.tar.gz` dynamically in-memory.
2. Computes file MD5 checksums on-the-fly during file reads.
3. Generates the binary structure of `ar` archive headers to output a fully compliant `.deb` package file format directly.
