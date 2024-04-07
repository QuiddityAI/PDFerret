import numpy as np
import pandas as pd


PRESENT_TENSE_VERB_LIST = ["VB", "VBP", "VBZ", "VBG"]
VERB_LIST = ["VB", "VBP", "VBZ", "VBG", "VBN", "VBD"]
NOUN_LIST = ["NNP", "NNPS"]


SECTIONS_MAPS = {
    "Authors": "Authors",
    "AUTHORS": "AUTHORS",
    "Abstract": "Abstract",
    "ABSTRACT": "Abstract",
    "Date": "Date",
    "DATE": "DATE",
    "INTRODUCTION": "Introduction",
    "MATERIALS AND METHODS": "Methods",
    "Materials and methods": "Methods",
    "METHODS": "Methods",
    "RESULTS": "Results",
    "CONCLUSIONS": "Conclusions",
    "CONCLUSIONS AND FUTURE APPLICATIONS": "Conclusions",
    "DISCUSSION": "Discussion",
    "ACKNOWLEDGMENTS": "Acknowledgement",
    "TABLES": "Tables",
    "Tabnles": "Tables",
    "DISCLOSURE": "Disclosure",
    "CONFLICT OF INTEREST": "Disclosure",
    "Acknowledgement": "Acknowledgements",
}


def compute_journal_features(article):
    """
    Parse features about journal references from a given dictionary of parsed article e.g.
    number of reference made, number of unique journal refered, minimum year of references,
    maximum year of references, ...

    Parameters
    ==========
    article: dict, article dictionary parsed from GROBID and converted to dictionary
        see ``pdf/parse_pdf.py`` for the detail of the output dictionary

    Output
    ======
    reference_dict: dict, dictionary of
    """
    try:
        n_reference = len(article["references"])
        n_unique_journals = len(
            pd.unique([a["journal"] for a in article["references"]])
        )
        reference_years = []
        for reference in article["references"]:
            year = reference["year"]
            if year.isdigit():
                # filter outliers
                if int(year) in range(1800, 2100):
                    reference_years.append(int(year))
        avg_ref_year = np.mean(reference_years)
        median_ref_year = np.median(reference_years)
        min_ref_year = np.min(reference_years)
        max_ref_year = np.max(reference_years)
        journal_features_dict = {
            "n_reference": n_reference,
            "n_unique_journals": n_unique_journals,
            "avg_ref_year": avg_ref_year,
            "median_ref_year": median_ref_year,
            "min_ref_year": min_ref_year,
            "max_ref_year": max_ref_year,
        }
    except:
        journal_features_dict = {
            "n_reference": None,
            "n_unique_journals": None,
            "avg_ref_year": None,
            "median_ref_year": None,
            "min_ref_year": None,
            "max_ref_year": None,
        }
    return journal_features_dict


def merge_section_list(section_list, section_maps=SECTIONS_MAPS, section_start=""):
    """
    Merge a list of sections into a normalized list of sections,
    you can get the list of sections from parsed article JSON in ``parse_pdf.py`` e.g.

    >> section_list = [s['heading'] for s in article_json['sections']]
    >> section_list_merged = merge_section_list(section_list)

    Parameters
    ==========
    section_list: list, list of sections

    Output
    ======
    section_list_merged: list,  sections
    """
    sect_map = section_start  # text for starting section e.g. ``Introduction``
    section_list_merged = []
    for section in section_list:
        if any([(s.lower() in section.lower()) for s in section_maps.keys()]):
            sect = [s for s in section_maps.keys() if s.lower()
                    in section.lower()][0]
            sect_map = section_maps.get(sect, "")  #
            section_list_merged.append(sect_map)
        else:
            section_list_merged.append(sect_map)
    return section_list_merged
