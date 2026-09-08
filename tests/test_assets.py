"""Assets resolution must work from a source checkout and a frozen bundle."""
import unittest

from PySide6.QtWidgets import QApplication


class TestAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Rendering a QIcon pixmap (SVG) requires a GUI application instance.
        cls.app = QApplication.instance() or QApplication([])

    def test_asset_path_resolves_at_project_root(self) -> None:
        from src.gui.assets import asset_path
        p = asset_path("skull-icon.svg")
        self.assertTrue(str(p).replace("\\", "/").endswith("/AXIS/assets/skull-icon.svg"), p)

    def test_skull_icon_exists_and_loads(self) -> None:
        from src.gui.assets import load_icon, asset_path
        self.assertTrue(asset_path("skull-icon.svg").is_file())
        icon = load_icon("skull-icon.svg")
        self.assertIsNotNone(icon)
        self.assertFalse(icon.isNull())
        px = icon.pixmap(24, 24)
        self.assertFalse(px.isNull())
        self.assertGreater(px.width(), 0)


if __name__ == "__main__":
    unittest.main()