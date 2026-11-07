"""
Where Is My Train APK Patcher & Dynamic ML Engine Injector
Injects GATI-SETU Dynamic Machine Learning Prediction Server into Where Is My Train APK.

Actions:
1. Disassembles APK archive.
2. Patches classes.dex in-place to redirect backend telemetry to GATI-SETU (http://10.0.2.2:8000/wimt_relay).
3. Recalculates Adler32 checksum and SHA-1 signature in the DEX header.
4. Strips obsolete Google signatures (META-INF/*.RSA, *.SF, *.MF).
5. Recompiles and signs the modified APK with jarsigner using an Android debug keystore.
6. Outputs: com.whereismytrain.android_gatisetu_ml.apk
"""

import os
import sys
import zlib
import hashlib
import struct
import zipfile
import subprocess
import shutil
import tempfile


class WIMTAPKPatcher:
    DEFAULT_IN_APK = os.path.expanduser("~/Downloads/com.whereismytrain.android_7.1.5.974952539.apk")
    DEFAULT_OUT_APK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "com.whereismytrain.android_gatisetu_ml.apk")
    KEYSTORE_PATH = os.path.join(tempfile.gettempdir(), "gatisetu_debug.keystore")

    TARGET_URL = b"https://puraa.whereismytrain.in"
    REPLACEMENT_URL = b"http://10.0.2.2:8000/wimt_relay"

    def __init__(self, in_apk: str = None, out_apk: str = None):
        self.in_apk = in_apk or self.DEFAULT_IN_APK
        self.out_apk = out_apk or self.DEFAULT_OUT_APK

        if not os.path.exists(self.in_apk):
            raise FileNotFoundError(f"Input APK not found: {self.in_apk}")

        assert len(self.TARGET_URL) == len(self.REPLACEMENT_URL) == 31, "URL length mismatch (must be 31 bytes)"

    def _ensure_keystore(self):
        """Generates Android debug keystore if not already created."""
        if os.path.exists(self.KEYSTORE_PATH):
            return
        cmd = [
            "keytool", "-genkeypair", "-v",
            "-keystore", self.KEYSTORE_PATH,
            "-alias", "gatisetu_debug",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "android",
            "-keypass", "android",
            "-dname", "CN=GatiSetu,OU=RailwayAI,O=IndianRailways,C=IN"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise RuntimeError(f"Keystore generation failed: {res.stderr.decode()}")

    BUILD_TOOLS_DIR = "/opt/homebrew/share/android-commandlinetools/build-tools/34.0.0"

    def patch(self) -> str:
        print(f"[1/5] Reading input APK: {self.in_apk}")
        self._ensure_keystore()

        zipalign_bin = os.path.join(self.BUILD_TOOLS_DIR, "zipalign")
        apksigner_bin = os.path.join(self.BUILD_TOOLS_DIR, "apksigner")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_apk = os.path.join(tmpdir, "unsigned.apk")
            aligned_apk = os.path.join(tmpdir, "aligned.apk")

            with zipfile.ZipFile(self.in_apk, "r") as z_in, zipfile.ZipFile(temp_apk, "w") as z_out:
                for item in z_in.infolist():
                    data = z_in.read(item.filename)

                    # Strip original Google signatures
                    if item.filename.startswith("META-INF/") and item.filename.endswith((".RSA", ".SF", ".MF")):
                        continue

                    # Patch classes.dex
                    if item.filename == "classes.dex":
                        print("[2/5] Patching classes.dex byte table...")
                        dex_bytes = bytearray(data)
                        pos = dex_bytes.find(self.TARGET_URL)
                        if pos != -1:
                            print(f"  Located '{self.TARGET_URL.decode()}' at offset {pos}")
                            dex_bytes[pos : pos + len(self.REPLACEMENT_URL)] = self.REPLACEMENT_URL

                            # Recompute SHA-1 (bytes 32 to EOF)
                            new_sha1 = hashlib.sha1(dex_bytes[32:]).digest()
                            dex_bytes[12:32] = new_sha1

                            # Recompute Adler-32 (bytes 12 to EOF)
                            new_adler = zlib.adler32(dex_bytes[12:]) & 0xFFFFFFFF
                            dex_bytes[8:12] = struct.pack("<I", new_adler)

                            print(f"  Fixed SHA-1: {new_sha1.hex()}")
                            print(f"  Fixed Adler32 Checksum: {hex(new_adler)}")
                            data = bytes(dex_bytes)
                        else:
                            print("  Warning: Target URL not found in classes.dex")

                    # Keep compression type (crucial: resources.arsc must remain uncompressed ZIP_STORED)
                    zinfo = zipfile.ZipInfo(item.filename)
                    zinfo.compress_type = item.compress_type
                    zinfo.external_attr = item.external_attr
                    z_out.writestr(zinfo, data)

            print("[3/5] Aligning APK with zipalign (4-byte page-align)...")
            zipalign_cmd = [zipalign_bin, "-p", "-f", "4", temp_apk, aligned_apk]
            za_res = subprocess.run(zipalign_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if za_res.returncode != 0:
                raise RuntimeError(f"zipalign failed: {za_res.stderr.decode()}")

            print(f"[4/5] Signing aligned APK with apksigner (v1 + v2 + v3 scheme)...")
            sign_cmd = [
                apksigner_bin, "sign",
                "--ks", self.KEYSTORE_PATH,
                "--ks-pass", "pass:android",
                "--ks-key-alias", "gatisetu_debug",
                "--key-pass", "pass:android",
                "--out", self.out_apk,
                aligned_apk
            ]
            sign_res = subprocess.run(sign_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if sign_res.returncode != 0:
                raise RuntimeError(f"apksigner failed: {sign_res.stderr.decode()}")

            print("[5/5] Verifying APK signature...")
            verify_cmd = [apksigner_bin, "verify", "--verbose", self.out_apk]
            verify_res = subprocess.run(verify_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if verify_res.returncode != 0:
                raise RuntimeError(f"APK verification failed: {verify_res.stderr.decode()}")

            print(f"Success! Patched Where Is My Train APK created at:")
            print(f"      {self.out_apk}")
            print(f"      File size: {os.path.getsize(self.out_apk) / (1024*1024):.2f} MB")
            return self.out_apk


if __name__ == "__main__":
    patcher = WIMTAPKPatcher()
    out = patcher.patch()

