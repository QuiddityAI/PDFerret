import os
from typing import List

from llmonkey.llms import BaseLLMModel

from .datamodels import FileFeatures, MetaInfo, PDFDoc, PDFError, PDFFile
from .pipeline import Pipeline
from .recipes import get_recipes


class PDFerret:
    def __init__(self, text_model: BaseLLMModel | str, vision_model: BaseLLMModel | str, **kwargs):
        """
        Initialize the PdfFerret class with text and vision models.

        Args:
            text_model (BaseLLMModel | str): LLMonkey model instance or name for text processing.
            vision_model (BaseLLMModel | str): LLMonkey model instance or name for vision processing.
        """
        if isinstance(text_model, str):
            text_model = BaseLLMModel.load(text_model)
        if isinstance(vision_model, str):
            vision_model = BaseLLMModel.load(vision_model)
        self.recipes = get_recipes(text_model, vision_model)
        self.pipelines = self._create_pipelines(self.recipes)

    def _create_pipelines(self, recipes) -> dict[str, Pipeline]:
        pipelines = {}
        for file_type, steps_config in recipes.items():
            steps = [step.make_step() for step in steps_config]
            pipelines[file_type] = Pipeline(steps)
        return pipelines

    def extract_batch(self, files: List[PDFFile], lang=None) -> tuple[List[PDFDoc], List[PDFError]]:
        """
        Extracts text and metadata from a batch of PDF files.

        Args:
            files (List[PDFFile]): A list of PDFFile objects to be processed.
            lang (str, optional): The language to be used for extraction. Defaults to None.

        Returns:
            tuple[List[PDFDoc], List[PDFError]]: A tuple containing two lists:
            - List[PDFDoc]: A list of successfully processed PDFDoc objects.
            - List[PDFError]: A list of PDFError objects for files that failed to process.
        """
        failed_all = {}
        processed_all = {}

        files = {v: v for v in files}  # assign unique ids to every item, use filename as id
        pdfdocs = {}
        # create PDFDoc objects for each file
        for key, file in files.items():
            ffeatures = FileFeatures(filename=key, file=file)
            meta = MetaInfo(file_features=ffeatures, language=lang)
            doc = PDFDoc(metainfo=meta, chunks=[])
            pdfdocs[key] = doc

        file_groups = self._classify_docs(pdfdocs)
        # for every file type, run the corresponding pipeline
        for file_type, current_files in file_groups.items():
            pipeline = self.pipelines.get(file_type)
            if pipeline:
                pdfdocs, pdferrors = pipeline.extract_batch(current_files)
                failed_all.update(pdferrors)
                processed_all.update(pdfdocs)
            else:
                failed_all.update(
                    {k: PDFError(f"No pipeline defined for file type: {file_type}") for k in current_files}
                )
        return self._sort_results(processed_all, failed_all, files)

    def _classify_docs(self, file_list: dict[str, PDFDoc]) -> dict[str, dict[str, PDFDoc]]:
        # group docs by extension
        docs_groups = {}
        for key, doc in file_list.items():
            ext = os.path.splitext(key)[1][1:]  # remove the dot
            if ext not in docs_groups:
                docs_groups[ext] = {}
            docs_groups[ext][key] = doc
        return docs_groups

    def _sort_results(self, docs, failed_all, files):
        sorted_docs = []
        for key in files:
            if key in docs:
                sorted_docs.append(docs[key])
            else:
                file_features = FileFeatures(filename=files[key] if isinstance(files[key], str) else None)
                meta_info = MetaInfo(file_features=file_features)
                sorted_docs.append(PDFDoc(meta_info))

        sorted_failed = [failed_all[key] for key in files if key in failed_all]

        return sorted_docs, sorted_failed
