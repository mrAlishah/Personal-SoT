from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from system.validation import validate_v1


class CoreValidationTests(unittest.TestCase):
    def test_ignores_python_bytecode_cache(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("workspace", "system", "guides"):
                (root / name).mkdir()
            cache = root / "system" / "validation" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "validator.cpython-314.pyc").write_bytes(b"generated")

            self.assertEqual([], validate_v1.run(root, "core"))


if __name__ == "__main__":
    unittest.main()
