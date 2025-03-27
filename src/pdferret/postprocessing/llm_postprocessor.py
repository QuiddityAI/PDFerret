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
    "en": """
You are a librarian and are conducting the indexing of documents.

Create two summaries for the document listed below:

1. search_description:
    A very brief description of the document with all the information someone might search for.
    The following should be included in two to three sentences (if applicable): main topic, involved persons, projects, locations, included spreadsheets, important dates, etc.
    No results or conclusions should be included. The structure of the document should not be described.
    Don't use fill words, short sentences are fine.

2. content_summary:
    A summary of the document's content that condenses the most important points into a maximum of 6–7 sentences.
    This should include the most important information, conclusions, and results of the document.
    The structure of the document should not be described.
    The wording should stay close to the original text. Bullet points may be used.

If no information is found, provide an empty string for each.
Format the response in the following schema as raw JSON without additional characters:
{
    "search_description": search_description,
    "content_summary": content_summary
}""",
    "de": """
Sie sind Bibliothekar und führen die Indizierung von Dokumenten durch.

Erstellen sie zwei Teile einer Zusammenfassung für das unten aufgeführte Dokument:
1. search_description:
    Eine sehr kurze Beschreibung des Dokuments mit allen Informationen, nach denen man möglicherweise suchen würde.
    Folgendes soll in drei bis vier Sätzen enthalten sein (falls im Dokument enthalten): Hauptthema, beteiligte Personen, Projekte, Standorte, enthaltene Tabellenblätter, wichtige Zeitpunkte, Kennnummern etc.
    Es sollen keine Ergebnisse oder Schlussfolgerungen enthalten sein. Es soll nicht die Struktur des Dokuments beschrieben werden.
    Verwenden Sie keine Füllwörter, kurze Sätze sind in Ordnung. Wiederhole nicht den Titel des Dokuments.
    Nenne keine Informationen, die nicht im Dokument enthalten sind.

2. content_summary:
    Eine Zusammenfassung des Inhalts des Dokuments, die in maximal 6-7 Sätzen die wichtigsten Punkte zusammenfasst.
    Hierbei sollen die wichtigsten Informationen, Schlussfolgerungen und Ergebnisse des Dokuments enthalten sein.
    Es soll keine Struktur des Dokuments beschrieben werden.
    Die Wortwahl sollte nah am Originaltext sein. Es können Stichpunkte verwendet und Markdown-Formatierungen angewendet werden.

Wenn keine Informationen gefunden werden, geben Sie jeweils eine leere Zeichenfolge an.
Formatieren sie die Antwort in folgendem Schema als Roh-JSON ohne zusätzliche Zeichen:
{
    "search_description": search_description,
    "content_summary": content_summary
}"""
}

# If extra metadata such as company names / people names, participants, location, prices, amounts, etc is present
# include it in the response as string of text in "ai_metadata" field, but keep it below 50 words.
# Return output as raw json without any extra characters, according to schema

system_prompt_metadata = {
    "en": """You are a librarian, performing indexing of the library.
Your task is to extract metadata from the document for which different information is provided.
The extracted metadata should include:
including:
- title
- document type
- people involved
- main date mentioned in the document or filename, such as date of the event or meeting date
- language of the document as code, e.g. "en", "de", "fr"

Follow the instructions below:
If filename is provided and gives good information about the document, format it as title and return.
Generate the title if it is not found in the text. Title should communicate the main topic directly,
be concise, informative and contain relevant keywords present in the document.
Examples of good titles: "Supply Chain Optimization Strategy Proposal" or "Q1 2024 Financial Performance Summary".

Assign document type, briefly describing the type of document, e.g. "Research Paper", "Technical Report", "Meeting notes", etc.

Involved people (authors, participants, etc.) should be listed as a list of names, e.g. ["John Doe", "Jane Smith"].

Use the date format YYYY-MM-DD.
If month or day is not provided, please use the first day of the month / year.

If any information is not found in the document, return empty strings.
Format your response as raw json without any extra characters, according to the schema:

{"title": title,
"document_type": document type,
"people": list of involved people,
"mentioned_date": main date mentioned in the document or filename,
"detected_language": language code}""",
    "de": """Sie sind Bibliothekar und führen die Indizierung der Bibliothek durch.
Ihre Aufgabe besteht darin, Metadaten aus dem Dokument zu extrahieren, für das verschiedene Informationen bereitgestellt werden.
Die extrahierten Metadaten sollten Folgendes umfassen:
- Titel
- Dokumenttyp
- beteiligte Personen
- Hauptdatum, das im Dokument oder Dateinamen erwähnt wird, z. B. Datum der Veranstaltung oder Datum der Besprechung
- Sprache des Dokuments als Code, z. B. „en“, „de“, „fr“

Folgen Sie den Anweisungen unten:

Erstellen Sie einen kurzen, informativen Titel. Der Titel sollte zwischen 3 bis 7 Wörter lang sein.
Falls ein aussagekräftiger Dateinname verfügbar ist oder im Dokument ein Titel genannt wird, sollte sich die Wortwahl möglichst nah daran orientieren.
Es sollte jedoch in jedem Fall das Hauptthema des Dokuments genannt werden und nicht nur die Art des Dokuments (z. B. „Bericht über Projekt X“ statt "Bericht").
Beispiele für gute Titel: „Vorschlag zur Optimierung der Lieferkettenstrategie“ oder „Zusammenfassung der finanziellen Leistung Q1 2024“.

Weisen Sie dem Dokumenttyp eine sehr kurze Beschreibung der Art des Dokuments zu, z. B. „Forschungsartikel“, „Technischer Bericht“, „Besprechungsnotizen“ usw.
Falls das Dokument eine Vorlage oder kommentierte Version ist, geben Sie dies auch an.

Beteiligte Personen (Autoren, Teilnehmer etc.) sollen als Liste von Namen angegeben werden, z. B. ["John Doe", "Jane Smith"].

Als Datumsformat soll JJJJ-MM-TT verwendet werden.
Wenn kein Monat oder Tag angegeben ist, geben Sie bitte den 01. an.

Formatieren Sie Ihre Antwort gemäß des Schemas als Roh-JSON ohne zusätzliche Zeichen.
Sollten Informationen nicht im Dokument gefunden werden, geben Sie leere Zeichenfolgen zurück.

{"title": Titel,
"document_type": Dokumenttyp,
"people": Liste der beteiligten Personen,
"mentioned_date": Hauptdatum, das im Dokument oder Dateinamen erwähnt wird,
"detected_language": Sprachcode}""",
}


class LLMMetaInfoResponse(BaseModel):
    title: str
    people: List[str] | None = []
    document_type: str | None = ""
    mentioned_date: str | None = ""
    detected_language: str | None = ""


class LLMTableResponse(BaseModel):
    description: str


class LLMSummaryResponse(BaseModel):
    search_description: str
    content_summary: str


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

        remaining_table_descriptions = 5
        for chunk in pdfdoc.chunks:
            if remaining_table_descriptions <= 0:
                break
            if self.llm_table_description and chunk.chunk_type == ChunkType.TABLE:
                try:
                    chunk.text = self._llm_table_descr(chunk.non_embeddable_content, lang)
                    remaining_table_descriptions -= 1
                except Exception as e:
                    logging.error(f"Failed to generate LLM table description: {e}")

        try:
            pdfdoc = self._generate_llm_abstract_metadata(pdfdoc, lang)
        except Exception as e:
            logging.error(f"Failed to generate LLM summary: {e}")
        return pdfdoc

    def _generate_llm_abstract_metadata(self, pdfdoc: PDFDoc, lang="en"):
        useful_info = f"Filename: {pdfdoc.metainfo.file_features.filename}\n"

        # if pdfdoc.metainfo.extra_metainfo:
        #     useful_info += "Extra metadata: "
        #     for key, value in pdfdoc.metainfo.extra_metainfo.items():
        #         useful_info += f"{key}: {value}\n"
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
            remaining_text_chunks = self.summary_max_chunks
            remaining_visual_pages = 10
            for chunk in pdfdoc.chunks:
                # take up to summary_max_chunks text chunks
                if chunk.chunk_type == ChunkType.TEXT and remaining_text_chunks > 0:
                    useful_info += chunk.text + "\n"
                    remaining_text_chunks -= 1
                # always take all (up to 10) visual pages if present
                # otherwise why would we have them?
                if chunk.chunk_type == ChunkType.VISUAL_PAGE and remaining_visual_pages > 0:
                    useful_info += chunk.text + "\n"
                    remaining_visual_pages -= 1
        current_tokens = count_tokens_rough(useful_info)
        if current_tokens > self.llm_model.config.max_input_tokens:
            max_input_tokens = self.llm_model.config.max_input_tokens
            logging.warning(
                f"Input to LLM is too long ({len(useful_info)} tokens), truncating to {max_input_tokens} tokens"
            )
            end = int(0.95 * len(useful_info) * max_input_tokens / current_tokens)
            useful_info = useful_info[:end]

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
                if key == "people":
                    # "people" is more adequate for non-scientific documents, but the rest of the code uses "authors"
                    key = "authors"
                if value:
                    pdfdoc.metainfo.__dict__[key] = value
        if self.llm_summary and (not pdfdoc.metainfo.abstract or self.llm_overwrite_abstract):
            useful_info += f"\nTitle: {pdfdoc.metainfo.title}\n"
            summary_resp, raw_resp = self.llm_model.generate_structured_response(
                data_model=LLMSummaryResponse,
                user_prompt=useful_info,
                system_prompt=system_prompt_summary[lang],
                temperature=0.4,
                max_tokens=1000,
            )
            if not summary_resp:
                raise ValueError("No summary was returned by LLM")
            pdfdoc.metainfo.abstract = summary_resp.content_summary
            pdfdoc.metainfo.search_description = summary_resp.search_description
        return pdfdoc

    def _llm_table_descr(self, table_as_html, lang="en"):

        descr_resp, raw_resp = self.llm_model.generate_structured_response(
            system_prompt=system_prompt_table[lang],
            data_model=LLMTableResponse,
            user_prompt=table_as_html,
            temperature=0.2,
            max_tokens=1000,
        )
        if descr_resp:
            return descr_resp.description
        else:
            raise ValueError("No table description was returned by LLM")

    def _llm_image_descr(self, image):
        # TODO: Implement image description
        raise NotImplementedError("Image description is not implemented yet")
