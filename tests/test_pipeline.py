import unittest
from src.pipeline import run_pipeline

class TestPipeline(unittest.TestCase):
    def test_run_pipeline(self):
        result = run_pipeline()
        self.assertIsInstance(result, dict)

if __name__ == "__main__":
    unittest.main()
