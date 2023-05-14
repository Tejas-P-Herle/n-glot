import unittest
from database import DataBase


class TestDataBase(unittest.TestCase):
    def __init__(self, test_method):
        self.db = DataBase()
        super().__init__(test_method)

    def test_get_languages(self):
        expected = {"python": {"extension": "py"},
                    "java": {"extension": "java"}}
        languages = {k: v for k, v in self.db.get_languages().items()
                     if k in expected}
        for language, lang_data in expected.items():
            self.assertTrue(language in languages,
                            "Missing Language in DB Read")
            for value_data in lang_data:
                self.assertTrue(
                    value_data in languages[language],
                    "Missing Property of Language {}".format(language))

    def test_setup(self):
        self.db.setup("python", "java")

        self.assertTrue(self.db.from_, "From Field of DB is uninitialized")
        self.assertTrue(self.db.to, "From Field of DB is uninitialized")

        self.assertTrue(self.db.from_reserved_kw,
                        "Reserved Keywords Field of DB is uninitialized")
        self.assertTrue(self.db.from_meta,
                        "From Meta Field of DB is uninitialized")
        self.assertTrue(self.db.to_meta,
                        "To Meta Field of DB is uninitialized")
        self.assertEqual(self.db.from_lang_name, "python",
                         "Chosen From Language not saved as db attribute")

        self.assertEqual(self.db.to_lang_name, "java",
                         "Chosen To Language not saved as db attribute")


if __name__ == '__main__':
    unittest.main()
