# PDFerret

**An all-in-one converter to make your files LLM-understandable**

For example, [sample docx file](https://www2.hu-berlin.de/stadtlabor/wp-content/uploads/2021/12/sample3.docx) will be converted to:
<details>

<summary>convenient JSON data structure</summary>

```json
{
  "extracted": [
    {
      "metainfo": {
        "doi": "",
        "title": "Accessible Document Sample",
        "document_type": "Technical Guide",
        "search_description": "Accessible Document Sample, headings, lists, images, tables, columns, screen readers, web accessibility",
        "abstract": "This document demonstrates accessibility techniques for headings, lists, images, tables, and columns. It includes eight section headings, ordered and unordered lists, links to different locations and downloadable documents, and images with alternate text. The document also features simple and complex tables, including one with merged cells. Additionally, it showcases the use of columns and explains how to create them correctly for accessibility. The document is designed to be completely accessible using assistive technologies such as screen readers.",
        "authors": [],
        "pub_date": "",
        "mentioned_date": "",
        "language": "en",
        "detected_language": "en",
        "file_features": {
          "filename": "sample3.docx",
          "file": null,
          "is_scanned": null
        },
        "npages": null,
        "thumbnail": "<base64 encoded thumbnail>",
        "extra_metainfo": null,
        "ai_metadata": ""
      },
      "chunks": [
        {
          "page": null,
          "coordinates": null,
          "section": "",
          "prefix": "",
          "non_embeddable_content": "",
          "text": " # Sample Document\nThis document was created using accessibility techniques for headings, lists, image alternate text, tables, and columns. It should\nbe completely accessible using assistive technologies such as screen readers.\n## Headings\nThere are eight section headings in this document. At the beginning, \\\"Sample Document\\\" is a level 1 heading. The main section\nheadings, such as \\\"Headings\\\" and \\\"Lists\\\" are level 2 headings. The Tables section contains two sub-headings, \\\"Simple Table\\\"\nand \\\"Complex Table,\\\" which are both level 3 headings.\n## Lists\nThe following outline of the sections of this document is an ordered (numbered) list with six items. The fifth item, \\\"Tables,\\\"\ncontains a nested unordered (bulleted) list with two items.\n1.  Headings\n2.  Lists 3.  Links\n4.  Images\n5.  Tables\n-   Simple Tables\n-   Complex Tables\n6.  Columns\n## Links\nIn web documents, links can point different locations on the page, different pages, or even downloadable documents, such as Word\ndocuments or PDFs:\n[Top of this Page](#sample-document)\\\n[Sample Document](http://www.dhs.state.il.us/page.aspx?item=67072)\\\n[Sample Document (docx)](http://www.dhs.state.il.us/OneNetLibrary/27897/documents/Initiatives/IITAA/Sample-Document.docx) ## Images\nFor example, there is an image of the web accessibility symbol to the left of this paragraph. Its alternate text is \\\"Web Access\nSymbol\\\".\nAlt text should communicate what an image means, not how it looks.\ngraphs, require long descriptions, but not all document types allow that. In web pages, long descriptions may b",
          "suffix": "e provided in\nseveral ways: on the page below the image, via a link below the image, or via a link o",
          "locked": false,
          "chunk_type": "text"
        },
        {
          "page": null,
          "coordinates": null,
          "section": "",
          "prefix": "uire long descriptions, but not all document types allow that. In web pages, long descriptions may b",
          "non_embeddable_content": "",
          "text": "e provided in\nseveral ways: on the page below the image, via a link below the image, or via a link on the image.\n## Tables\n### Simple Tables\nSimple tables have a uniform number of columns and rows, without any merged cells:\n  ----------------------------------------------------------------------------------------------------------------------------------\n  **Screen Reader**                                       **Responses**                               **Share**\n  ------------------------------------------------------- ------------------------------------------- ------------------------------   JAWS                                                    853                                         49%\n  NVDA                                                    238                                         14%\n  Window-Eyes                                             214                                         12%\n  System Access                                           181                                         10%\n  VoiceOver                                               159                                         9%\n  ----------------------------------------------------------------------------------------------------------------------------------\n### Complex Tables\nThe following is a complex table, using merged cells as headers for sections within the table. This can\\'t be made accessible in\nall types of documents:\n  ----------------------------------------------------------------------------------------------------------------------------------",
          "suffix": "--\n                           **May 2012**                                          **September 2010",
          "locked": false,
          "chunk_type": "text"
        },
        {
          "page": null,
          "coordinates": null,
          "section": "",
          "prefix": "----------------------------------------------------------------------------------------------------",
          "non_embeddable_content": "",
          "text": "--\n                           **May 2012**                                          **September 2010**         \n  ------------------------ -------------------------- -------------------------- -------------------------- --------------------------   **Screen Reader**        **Responses**              **Share**                  **Responses**              **Share**\n  JAWS                     853                        49%                        727                        59%\n  NVDA                     238                        14%                        105                        9%\n  Window-Eyes              214                        12%                        138                        11%\n  System Access            181                        10%                        58                         5%\n  VoiceOver                159                        9%                         120                        10%\n  ------------------------------------------------------------------------------------------------------------------------------------\n## Columns\nThis is an example of columns. With columns, the page is split into two or more horizontal sections. Unlike tables, in which you\nusually read across a row and then down to the next, in columns, you read down a column and then across to the next.\\\nWhen columns are not created correctly, screen readers may run lines together, reading the first line of the first column, then\nthe first line of the second column, then the second line of the first column, and so on. Obviously, that is not accessible",
          "suffix": "",
          "locked": false,
          "chunk_type": "text"
        }
      ],
      "full_text": "# Sample Document\nThis document was created using accessibility techniques for headings, lists, image alternate text, tables, and columns. It should\nbe completely accessible using assistive technologies such as screen readers.\n## Headings\nThere are eight section headings in this document. At the beginning, \\\"Sample Document\\\" is a level 1 heading. The main section\nheadings, such as \\\"Headings\\\" and \\\"Lists\\\" are level 2 headings. The Tables section contains two sub-headings, \\\"Simple Table\\\"\nand \\\"Complex Table,\\\" which are both level 3 headings.\n## Lists\nThe following outline of the sections of this document is an ordered (numbered) list with six items. The fifth item, \\\"Tables,\\\"\ncontains a nested unordered (bulleted) list with two items.\n1.  Headings\n2.  Lists\n3.  Links\n4.  Images\n5.  Tables\n-   Simple Tables\n-   Complex Tables\n6.  Columns\n## Links\nIn web documents, links can point different locations on the page, different pages, or even downloadable documents, such as Word\ndocuments or PDFs:\n[Top of this Page](#sample-document)\\\n[Sample Document](http://www.dhs.state.il.us/page.aspx?item=67072)\\\n[Sample Document (docx)](http://www.dhs.state.il.us/OneNetLibrary/27897/documents/Initiatives/IITAA/Sample-Document.docx)\n## Images\nFor example, there is an image of the web accessibility symbol to the left of this paragraph. Its alternate text is \\\"Web Access\nSymbol\\\".\nAlt text should communicate what an image means, not how it looks.\ngraphs, require long descriptions, but not all document types allow that. In web pages, long descriptions may be provided in\nseveral ways: on the page below the image, via a link below the image, or via a link on the image.\n## Tables\n### Simple Tables\nSimple tables have a uniform number of columns and rows, without any merged cells:\n  ----------------------------------------------------------------------------------------------------------------------------------\n  **Screen Reader**                                       **Responses**                               **Share**\n  ------------------------------------------------------- ------------------------------------------- ------------------------------\n  JAWS                                                    853                                         49%\n  NVDA                                                    238                                         14%\n  Window-Eyes                                             214                                         12%\n  System Access                                           181                                         10%\n  VoiceOver                                               159                                         9%\n  ----------------------------------------------------------------------------------------------------------------------------------\n### Complex Tables\nThe following is a complex table, using merged cells as headers for sections within the table. This can\\'t be made accessible in\nall types of documents:\n  ------------------------------------------------------------------------------------------------------------------------------------\n                           **May 2012**                                          **September 2010**         \n  ------------------------ -------------------------- -------------------------- -------------------------- --------------------------\n  **Screen Reader**        **Responses**              **Share**                  **Responses**              **Share**\n  JAWS                     853                        49%                        727                        59%\n  NVDA                     238                        14%                        105                        9%\n  Window-Eyes              214                        12%                        138                        11%\n  System Access            181                        10%                        58                         5%\n  VoiceOver                159                        9%                         120                        10%\n  ------------------------------------------------------------------------------------------------------------------------------------\n## Columns\nThis is an example of columns. With columns, the page is split into two or more horizontal sections. Unlike tables, in which you\nusually read across a row and then down to the next, in columns, you read down a column and then across to the next.\\\nWhen columns are not created correctly, screen readers may run lines together, reading the first line of the first column, then\nthe first line of the second column, then the second line of the first column, and so on. Obviously, that is not accessible.\n"
    }
  ],
  "errors": []
}
```

</details>  
<br>
It works with office documents, scientific articles, technical drawings, images (e.g. scans) and many other file formats. It can be used to convert files to plain text, extract metadata, generate thumbnails and chunk the text into smaller pieces. The library is designed to be extensible, allowing for easy addition of new file formats and processing methods.

## Motivation

While there are multiple solutions for conversion of various file formats to plain text (e.g. unstructured), all of them are lacking some of the features, identified as "must have" for Quiddity AI:

1) Transformation of complex file formats, including tables, PDFs and scans into plain text
2) Handling of the metadata and not just file content (e.g. to make the files sortable by date)
3) Built-in chunking
4) Convenient extending to support more file formats
5) Generation of thumbnails

PDFerret satifies all these requirements, while also being efficient in terms of compute time and LLM tokens usage.


## Installation

Due to the numerous dependencies, a containerized installation is highly recommended. Use
```
docker compose up -d
```
to run the pre-built container. Alternatively, use
```
docker compose -f docker-compose-build.yml up -d
```
to build the container from scratch. Both container files will download the required dependencies. The container will be available at `localhost:58080`.`

The API provides an endpoint to process multiple document files and extract structured information. There are single endpoint available:   
`/process_files_by_stream`: This endpoint allows you to send multiple files in a single request and receive the processed results in a single response.
Additionally, see `localhost:58080/docs` for the Swagger UI, which provides an interactive interface for testing the API.

Below is an example of how to use the `/process_files_by_stream` endpoint:

#### Endpoint
`POST /process_files_by_stream`

#### Request Headers
- `accept: application/json`

#### Request Parameters
- `vision_model`: The name of the vision model in [LLMonkey](https://github.com/QuiddityAI/LLMonkey) to use for processing (e.g., `Mistral_Pixtral`).
- `text_model`: The name of the text model in in [LLMonkey](https://github.com/QuiddityAI/LLMonkey) to use for processing (e.g., `Nebius_Llama_3_1_70B_fast`).
- `lang`: The default language for processing (e.g., `en`). Optional.
- `return_images`: Whether to include thumbnails in the response (`true` or `false`) as base64 encoded image. Optional.
- `perfile_settings`: A dictionary of file-specific settings, such as language or additional metadata.

Tha `perfile_settings` should match following Pydantic model:
```python
class PerFileSettings(BaseModel):
    lang: Literal["", "en", "de"] = ""
    extra_metainfo: dict[str, str] = {}
```
It allows to specify language and additional metadata for each file. Additional metadata can include any important information as key-value pairs. For example, you can include author information, document type, or any other relevant details. It will be processed by LLM and included in the output if any relevant information is found in this field.

#### Request Body
The request body should include:
1. **Files**: A list of document files to process, sent as multipart form data.
2. **Params**: A JSON object containing the parameters described above.

Example `params` object:
```json
{
  "vision_model": "Mistral_Pixtral",
  "text_model": "Nebius_Llama_3_1_70B_fast",
  "lang": "en",
  "return_images": true,
  "perfile_settings": {
    "test_de.doc": {"lang": "de"},
    "test.doc": {
      "lang": "en",
      "extra_metainfo": {"Author information": "John Doe"}
    }
  }
}
```
see tests/test_api.py for an example of usage. Note that other tests besides test_api.py are obsolete.

### Return Value

The response will follow structure:
```json
{
  "extracted": [
    <list of extracted documents (PDFDoc objects) in the same order as they were sent>
  ],
  "errors": [
    <list of errors, if any occurred during processing>
  ]
}
```
See src/pdferret/datamodels.py for the definition of the PDFDoc object and other data models used in the library.

<details>

<summary>Example of a PDFDoc object</summary>

PDFDoc object will contain the following fields:
```json
{
  "metainfo": {
    "doi": "",
    "title": "",
    "document_type": "",
    "search_description": "",
    "abstract": "",
    "authors": [],
    "pub_date": "",
    "mentioned_date": "",
    "language": "",
    "detected_language": "",
    "file_features": {
      "filename": "",
      "file": null,
      "is_scanned": null
    },
    "npages": null,
    "thumbnail": "<base64 encoded thumbnail>",
    "extra_metainfo": null,
    "ai_metadata": ""
  },
  "chunks": [
    <list of chunks>
  ],
  "full_text": "<full text of the document>"
}
```
The `chunks` field will contain a list of chunks, each with the following fields:
```json
{
  "page": null, // page number of the chunk
  "coordinates": null, // coordinates of the chunk in the document, not implemented yet
  "section": "", // section name of the chunk, not implemented yet
  "prefix": "", // prefix of the chunk
  "non_embeddable_content": "", // non-embeddable content of the chunk e.g. images
  "text": "<chunk text>", // the text of the chunk
  "suffix": "<chunk suffix>", // the suffix of the chunk
  "locked": false, // shows if the chunk can be concatenated with the next chunk, only used under the hood
  "chunk_type": "<type of chunk>" 
}
```

The `chunk_type` field can be one of the following:
- `text`: Regular text chunk
- `figure`: Image or figure chunk
- `table`: Table chunk
- `equation`: Equation chunk
- `other`: Other type of chunk

</details>

## Manual installation

1. To install the package, use `pip install .` in the source folder, which will install package with all dependencies
2. On minimal Ubuntu systems (e.g. in a python Docker image), `sudo apt install libgl1` might be needed for opencv
3. PDFerret relies on Tika for processing general documents. This requries up to date Tika (tested on apache/tika:3.0.0.0-BETA2-full) up and running on localhost:9998. You can overwrite tika server address by setting env var `PDFERRET_TIKA_SERVER_URL`.
Please note that python tika package used as a client in this lib can download and run it's own version of Tika if the server is not found, which can lead to unpredictable results. In this case it might help to set `TIKA_CLIENT_ONLY=1` in docker-compose file.

## Configuration

Following env variables are supported to configure PDFerret:
- `PDFERRET_GROBID_URL` - sets url of GROBID, used by extractors
- `PDFERRET_NPROC` - sets number of processors used for parallel processing for both metainfo and text extractors
- `PDFERRET_BATCH_SIZE` - sets batch size for parallel processing, i.e. how many items are processed between fork and join. Must be at least `PDFERRET_NPROC`, but shouldn't have strong influence on performance otherwise
- `PDFERRET_MAX_PAGES` - all pdfs will be cropped to first MAX_PAGES WARNING! Currently not implemented
- `PDFERRET_TIKA_SERVER_URL` - address of the Tika
- `PDFERRET_TIKA_OCR_STRATEGY` - controls how Tika will handle pdfs without text. Must be one of 'AUTO', 'OCR_ONLY', 'NO_OCR', 'OCR_AND_TEXT_EXTRACTION', defaults to 'NO_OCR'
- `PDFERRET_VISUAL_MAX_PAGES` - sets how many pages will be used for extracting information with vision model. Defaults to 3.
- LLMonkey API keys are also required for some extractors, see llmonkey documentation for more information
- `PDFERRET_MAX_CHUNK_LEN` - maximum length of chunk for chunking algo
- `PDFERRET_CHUNK_OVERLAP` - overlap of chunks for chunking algo

### Using the Google API

Create a credentials file before building the Docker container using:
`gcloud auth application-default login`

It will then be mounted to the container.



# Development
Probably the most important part to update is the recipes in `pdferret/recipes`. They define how to extract information from different types of documents. Optionally, a new processors can be created, subclassing `pdferret.base.BaseProcessor` and implementing `process_single` method. The `process_single` method will be parallelized depending on the `parallel` attribute of the processor, which can be set to `thread`, `process` or `none`. Alternatively, if different parallelization is needed, the `_process_batch` method can be implemented.

## Testing

Most of the tests are not yet updated to v2, so they will not work with the current version of the library. However, the tests in `tests/test_api.py` should work. To run them, use `pytest tests/test_api.py`.

## Deprecated code

Library still contains a lot of not used code from the previous version, including Grobid and Unstructured extractors.
They are not used in the current version of the library and probably should be removed in the future.
