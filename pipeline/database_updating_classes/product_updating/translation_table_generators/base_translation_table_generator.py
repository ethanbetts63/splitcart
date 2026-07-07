import abc
import json

class BaseTranslationTableGenerator(abc.ABC):
    """
    An abstract base class for generating translation table files.

    This class provides the core functionality to generate a JSON file
    containing a translation dictionary. Subclasses are expected to

    implement the `generate_translation_dict` method to provide the
    specific data to be written.
    """

    def __init__(self, output_path: str):
        """
        Initializes the generator with the output path.

        Args:
            output_path: The absolute path to the output .json file.
        """
        self.output_path = output_path

    @abc.abstractmethod
    def generate_translation_dict(self) -> dict:
        """
        Abstract method to be implemented by subclasses.

        This method should query the database and construct a dictionary
        representing the translation table.

        Returns:
            A dictionary containing the translation data.
        """
        pass

    def write_to_file(self, data: dict):
        """
        Writes the generated dictionary to the specified JSON file.
        """
        print(f"Writing translation table to {self.output_path}...")
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(',', ':'))
        print("Done.")

    def run(self):
        """
        Orchestrates the generation and writing of the translation table file.
        """
        print(f"Running {self.__class__.__name__}...")
        translation_dict = self.generate_translation_dict()
        self.write_to_file(translation_dict)
