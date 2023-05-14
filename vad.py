"""Validate all user input"""

from os import path


# Define supported languages
# SUPPORTED_LANGS = {"python":".py", "java":".java", "c":".c", "cpp":".cpp"}


class Validate:

    def __init__(self, languages):
        self.lang_from = ""
        self.lang_to = ""
        self.in_file = ""
        self.out_file = ""
        self.languages = languages

    def validate_language(self, language):
        """Check if language is supported"""

        # If language is not supported, return error message, else return None
        language = language.lower()
        self.lang_to = language
        if language not in self.languages:
            return "Unsupported language {}".format(language)

    def recognize_language(self, file_path):
        """Recognize language from file extension"""

        # Get extension from the file path
        file_ext = file_path.rsplit(".", 1)
        if len(file_ext) != 2 or not file_ext[1]:
            return 2
        file_ext = file_ext[1]

        # Search for language of extension in supported_languages
        for lang, lang_dat in self.languages.items():
            if lang_dat["extension"] == file_ext:
                return lang.lower()
        return 3

    def validate_file_path(self, file_path):
        """Checks if file_path is valid"""

        # Check if file exists
        if not path.isfile(file_path):
            return "File - {} Does not exist".format(file_path)

        # Store infile path
        self.in_file = file_path

        # Get extension from file_path
        language = self.recognize_language(file_path)

        # Store input language
        if not self.lang_to:
            self.lang_from = language

        # Check if error encountered
        if language == 2:
            return "Please Add File Extension"
        elif language == 3:
            return "Unsupported File Type"

    def validate_file_name(self, file_path):
        """Checks if file_name matches specified language"""

        # Save outfile path
        self.out_file = file_path

        # Recognize file language from file path
        recognized_language = self.recognize_language(file_path)

        # Check if file_name is a valid
        file_name = path.splitext(path.split(file_path)[1])[0]
        special_characters = "\\/:*?\"<>|"
        for character in special_characters:
            if file_name.find(character) != -1:
                return "File name must not contain '%s'" % special_characters

        # Return validation result
        if self.lang_to != recognized_language:
            return "Extension and language don't match"


def main():
    py_dict = {"extension": "py"}
    java_dict = {"extension": "java"}
    languages = {"python": py_dict, "java": java_dict}
    vd = Validate(languages)
    print(vd.validate_language("java"))
    print(vd.validate_file_path("file/path.java"))
    print(vd.validate_file_name("file/path.java"))


if __name__ == "__main__":
    main()
