import logging
from dataclasses import replace as dc_replace
from typing import List

from llmonkey.llms import BaseLLMModel
from pydantic import BaseModel

from pdferret.utils.tokens import count_tokens_rough

from ..base import BaseProcessor
from ..datamodels import ChunkType, PDFDoc

system_prompt_table = {
    "en": """You are a librarian, performing indexing of the library.
You will be provided with a table encoded as HTML. Write a very short summary
(3-4 sentences) for it. Only include semantic information useful to find this table.
If no information is found, return empty string.
Return output as raw json without any extra characters, according to schema {"description": description you extracted}""",
    "de": """Sie sind Bibliothekar und führen eine Indexierung der Bibliothek durch.
Sie erhalten eine als HTML kodierte Tabelle. Schreiben Sie eine sehr kurze Zusammenfassung
(3-4 Sätze) dazu. Fügen Sie nur semantische Informationen ein, die zum Auffinden dieser Tabelle nützlich sind.
Wenn keine Informationen gefunden werden, geben Sie eine leere Zeichenfolge zurück.
Gibt die Ausgabe als reines JSON ohne zusätzliche Zeichen zurück, gemäß dem Schema {"description": Beschreibung, die Sie extrahiert haben}""",
}


system_prompt_summary = {
    "en": """You are a librarian, performing indexing of the library.
For every provided entry, you have different information available. Write a short summary
(up to 6-7 sentences) for it. Only include semantic information useful to search this document.
If abstract is found in the information provided, return it instead of writing summary.
Do not include information about article structure, number of pages, etc.
If no information is found, return empty string.
Return output as raw json without any extra characters, according to schema {"summary": summary you extracted}""",
    "de": """Sie sind Bibliothekar und führen die Indizierung der Bibliothek durch.
Für jeden bereitgestellten Eintrag stehen Ihnen unterschiedliche Informationen zur Verfügung. Schreiben Sie eine sehr kurze Zusammenfassung
(bis zu 6-7 Sätze) dazu. Fügen Sie nur semantische Informationen ein, die für die Suche in diesem Dokument nützlich sind.
Wenn in den bereitgestellten Informationen eine Zusammenfassung gefunden wird, geben Sie diese zurück, anstatt eine Zusammenfassung zu schreiben.
Fügen Sie keine Informationen über Artikelstruktur, Seitenzahl usw. ein.
Wenn keine Informationen gefunden werden, geben Sie eine leere Zeichenfolge zurück.
Geben Sie die Ausgabe als Roh-JSON ohne zusätzliche Zeichen zurück, gemäß dem Schema {"summary": Zusammenfassung, die Sie extrahiert haben}""",
}

system_prompt_metadata = {
    "en": """You are a librarian, performing indexing of the library.
For every provided entry, you have different information available. Your task is to extract metadata from the document.
Metadata includes: title, authors, last modification date, DOI.
If title is not present, create it, the title should consist of at least 8-10 words to describe the document.
If any of authors, date, DOI are not present, exclude them from response.
Make authors a list of strings, each string is a full name of an author.
For modification date use the format YYYY-MM-DD.
If extra metadata such as company names / people names, participants, location, prices, amounts, etc is present
include it in the response as string of text in "ai_metadata" field, but keep it below 50 words.
Return output as raw json without any extra characters, according to schema
{"title": title, "authors": authors, "pub_date": modification_date, "doi": doi, "ai_metadata": ai_metadata}""",
    "de": """Sie sind Bibliothekar und führen die Indizierung der Bibliothek durch.
Für jeden bereitgestellten Eintrag stehen Ihnen unterschiedliche Informationen zur Verfügung. Ihre Aufgabe besteht darin, Metadaten aus dem Dokument zu extrahieren.
Zu den Metadaten gehören: Titel, Autoren, letztes Änderungsdatum, DOI.
Wenn kein Titel vorhanden ist, erstellen Sie ihn. Der Titel sollte aus mindestens 8-10 Wörtern bestehen, um das Dokument zu beschreiben.
Wenn Autoren, Datum oder DOI nicht vorhanden sind, schließen Sie sie von der Antwort aus.
Erstellen Sie für die Autoren eine Liste von Zeichenfolgen, wobei jede Zeichenfolge der vollständige Name eines Autors ist.
Verwenden Sie für das Änderungsdatum das Format JJJJ-MM-TT.
Wenn zusätzliche Metadaten wie Firmennamen/Personennamen, Teilnehmer, Standort, Preise, Beträge usw. vorhanden sind,
fügen Sie diese in die Antwort als Textzeichenfolge im Feld „ai_metadata“ ein, aber halten Sie sie unter 50 Wörtern.
Gibt die Ausgabe gemäß Schema als reines JSON ohne zusätzliche Zeichen zurück
{"title": Titel, "authors": Autoren, "pub_date": Änderungsdatum, "doi": doi, "ai_metadata": ai_metadata}""",
}


class LLMMetaInfoResponse(BaseModel):
    title: str
    authors: List[str] | None = []
    pub_date: str | None = ""
    doi: str | None = ""
    ai_metadata: str | None = ""


class LLMTableResponse(BaseModel):
    description: str


class LLMSummaryResponse(BaseModel):
    summary: str


class LLMPostprocessor(BaseProcessor):
    parallel = "thread"
    operates_on = PDFDoc

    def __init__(
        self,
        llm_model: BaseLLMModel = None,
        llm_table_description=False,
        llm_summary=True,
        llm_metainfo=True,
        llm_overwrite_abstract=False,
        summary_max_chunks=5,
        n_proc=None,
        batch_size=None,
    ):
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.llm_table_description = llm_table_description
        self.llm_summary = llm_summary
        self.llm_metainfo = llm_metainfo
        self.llm_model = llm_model
        self.summary_max_chunks = summary_max_chunks
        self.llm_overwrite_abstract = llm_overwrite_abstract

    def process_single(self, pdfdoc: PDFDoc) -> PDFDoc:

        lang = pdfdoc.metainfo.language or "en"
        if lang not in system_prompt_summary:
            lang = "en"
            logging.warning(f"Language {lang} is not supported, using English instead")

        for chunk in pdfdoc.chunks:
            if self.llm_table_description and chunk.chunk_type == ChunkType.TABLE:
                try:
                    chunk.text = self._llm_table_descr(chunk.non_embeddable_content, lang)
                except Exception as e:
                    logging.error(f"Failed to generate LLM table description: {e}")

        try:
            pdfdoc = self._generate_llm_abstract_metadata(pdfdoc, lang)
        except Exception as e:
            logging.error(f"Failed to generate LLM summary: {e}")
        return pdfdoc

    def _generate_llm_abstract_metadata(self, pdfdoc: PDFDoc, lang="en"):
        useful_info = f"Filename: {pdfdoc.metainfo.file_features.filename}\n"

        if pdfdoc.metainfo.title:
            useful_info += f"Title: {pdfdoc.metainfo.title}\n"

        if pdfdoc.metainfo.extra_metainfo:
            useful_info += "Extra metadata: "
            for key, value in pdfdoc.metainfo.extra_metainfo.items():
                useful_info += f"{key}: {value}\n"
        metainfo = useful_info  # save for metadata extraction
        # append first 2 chunks to metainfo
        metainfo += "\nDocument content: "
        idx = 0
        for chunk in pdfdoc.chunks:
            if idx >= 2:
                break
            if chunk.chunk_type == ChunkType.TEXT:
                metainfo += "\n" + chunk.text
                idx += 1

        if pdfdoc.chunks:
            useful_info += "Content: "
            idx = 0
            for chunk in pdfdoc.chunks:
                if idx >= self.summary_max_chunks:
                    break
                # take up to summary_max_chunks text chunks
                if chunk.chunk_type == ChunkType.TEXT:
                    useful_info += chunk.text + "\n"
                    idx += 1
                # always take all visual pages if present
                # otherwise why would we have them?
                if chunk.chunk_type == ChunkType.VISUAL_PAGE:
                    useful_info += chunk.text + "\n"
        current_tokens = count_tokens_rough(useful_info)
        if current_tokens > self.llm_model.config.max_input_tokens:
            max_input_tokens = self.llm_model.config.max_input_tokens
            logging.warning(
                f"Input to LLM is too long ({len(useful_info)} tokens), truncating to {max_input_tokens} tokens"
            )
            end = int(0.95 * len(useful_info) * max_input_tokens / current_tokens)
            useful_info = useful_info[:end]

        if self.llm_summary and (not pdfdoc.metainfo.abstract or self.llm_overwrite_abstract):
            summary_resp, raw_resp = self.llm_model.generate_structured_response(
                data_model=LLMSummaryResponse,
                user_prompt=useful_info,
                system_prompt=system_prompt_summary[lang],
                temperature=0.4,
                max_tokens=1000,
            )
            if not summary_resp:
                raise ValueError("No summary was returned by LLM")
            pdfdoc.metainfo.abstract = summary_resp.summary
        if self.llm_metainfo:
            metadata_resp, raw_resp = self.llm_model.generate_structured_response(
                data_model=LLMMetaInfoResponse,
                user_prompt=metainfo,
                system_prompt=system_prompt_metadata[lang],
                temperature=0.2,
                max_tokens=500,
            )
            if not metadata_resp:
                raise ValueError("No metadata was returned by LLM")
            # only update metadata which is not empty
            for key, value in metadata_resp.model_dump().items():
                if value:
                    pdfdoc.metainfo.__dict__[key] = value
        return pdfdoc

    def _llm_table_descr(self, table_as_html, lang="en"):

        descr_resp, raw_resp = self.llm_model.generate_structured_response(
            system_prompt=system_prompt_table[lang],
            data_model=LLMTableResponse,
            user_prompt=table_as_html,
            temperature=0.2,
            max_tokens=None,
        )
        if descr_resp:
            return descr_resp.description
        else:
            raise ValueError("No table description was returned by LLM")

    def _llm_image_descr(self, image):
        # TODO: Implement image description
        raise NotImplementedError("Image description is not implemented yet")
