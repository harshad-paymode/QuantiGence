import re
import logging
from typing import List, Dict, Any
from .toc import get_table_of_contents
from edgar import Filing
from edgar.files.html_documents import TextBlock, TableBlock
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


def get_heading_dict(all_items: List[str], table_of_contents) -> Dict[str, str]:
    """
    Map items to headings using table_of_contents if present; otherwise return identity dict.
    """
    result = {}
    if table_of_contents.empty:
        for item in all_items:
            result[item] = item
        return result

    for item in all_items:
        for t_item in table_of_contents.index:
            try:
                if re.fullmatch(item.lower() + r"\W*", str(t_item).lower()):
                    result[item] = item + ": " + table_of_contents.loc[t_item, "Headings"]
                    break
            except re.error:
                continue
    return result


def chunk_document(chunk_obj, filing_date: str, company: str, item_heading_dictionary: Dict[str, str], form_type="10-K", min_words=20) -> List[Dict[str, Any]]:
    """
    Core chunking logic adapted from your notebook for 10-Ks.
    Returns list of {'Metadata': ..., 'Chunks': {'parent_chunk': ...}}
    """
    regex1 = re.compile(
        r"""
        \n*.*?\s\|\s.*?\d{4}\sForm\s10-K\s\|\s\d+\n*$
        """,
        re.VERBOSE,
    )
    regex2 = re.compile(r"\n*\d+\n*$")

    metadata_template = {
        "item_heading": None,
        "filing_date": filing_date,
        "company": company,
        "form": form_type,
        "is_table": False,
    }

    all_chunks = []
    # iterate items in TOC order
    items = chunk_obj.list_items()
    for item in items:
        metadata = metadata_template.copy()
        metadata["item_heading"] = item_heading_dictionary.get(item, item)
        chunks_for_item = chunk_obj.chunks_for_item(item)

        Headings = {}
        processed_chunk = []
        prev_content = False
        prev_heading = False
        metadata_chunk = metadata.copy()

        for chunk in chunks_for_item:
            for element in chunk:
                # prefer TextBlock-like types; if edgar not present these are generic objects
                if isinstance(element, TextBlock):
                    text_raw = element.get_text()
                    if element.is_header:
                        # skip page headers/footers
                        if regex1.fullmatch(text_raw) or regex2.fullmatch(text_raw):
                            Headings = {}
                            continue

                        text = text_raw.strip("\n").strip(" ")
                        if item.lower() in text.lower() or "part" in text.lower():
                            continue

                        if prev_content and processed_chunk:
                            chunk_text = " ".join(processed_chunk)
                            if len(chunk_text.split()) > min_words:
                                all_chunks.append({"Metadata": metadata_chunk.copy(), "Chunks": {"parent_chunk": chunk_text}})
                            processed_chunk = []
                            Headings = {}

                        if Headings:
                            max_level = max(list(Headings.keys()))
                            Headings[max_level + 1] = text
                        else:
                            Headings[1] = text

                        prev_content = False
                        prev_heading = True
                    else:
                        if prev_heading:
                            metadata_chunk = metadata.copy()
                            if len(Headings) > 3:
                                chunk_text = ""
                                for _, value in Headings.items():
                                    chunk_text += value + "\n"
                                all_chunks.append({"Metadata": metadata_chunk, "Chunks": {"parent_chunk": chunk_text}})
                            else:
                                metadata_chunk.setdefault("sub_headings", {})
                                for key, value in Headings.items():
                                    metadata_chunk["sub_headings"][f"level_{key}_heading"] = value

                        text = text_raw.strip("\n").strip(" ")
                        processed_chunk.append(text)
                        prev_content = True
                        prev_heading = False

                elif isinstance(element, TableBlock):
                    # treat table as separate chunk
                    metadata_chunk = metadata.copy()
                    if prev_heading:
                        if len(Headings) > 3:
                            chunk_text = ""
                            for _, value in Headings.items():
                                chunk_text += value + "\n"
                            all_chunks.append({"Metadata": metadata_chunk, "Chunks": {"parent_chunk": chunk_text}})
                        else:
                            metadata_chunk.setdefault("sub_headings", {})
                            for key, value in Headings.items():
                                metadata_chunk["sub_headings"][f"level_{key}_heading"] = value

                    chunk_text = ""
                    if prev_content:
                        text = "\n".join(processed_chunk)
                        if min_words > 5 and len(text.split()) < min_words:
                            chunk_text = text

                    chunk_text += element.get_text()
                    metadata_chunk["is_table"] = True
                    all_chunks.append({"Metadata": metadata_chunk, "Chunks": {"parent_chunk": chunk_text}})
                    prev_content = True
                    prev_heading = False
                else:
                    # Fallback: if the element provides get_text, use it
                    try:
                        raw = getattr(element, "get_text", lambda: "")()
                        if isinstance(raw, str) and raw.strip():
                            processed_chunk.append(raw.strip())
                            prev_content = True
                    except Exception:
                        continue

        if processed_chunk:
            chunk_text = "\n".join(processed_chunk)
            if len(chunk_text.split()) > min_words:
                all_chunks.append({"Metadata": metadata_chunk, "Chunks": {"parent_chunk": chunk_text}})
    return all_chunks


def get_chunks(filing_date: str, ticker: str, company: str, cik: int, accession_no: str, form="10-K"):
    """
    Wrapper to create a Filing object and chunk it. Caller is expected to handle exceptions.
    """

    filing = Filing(form=form, filing_date=filing_date, company=ticker, cik=cik, accession_no=accession_no)
    obj = filing.obj()
    chunk_obj = obj.chunked_document

    table_of_contents = get_table_of_contents(chunk_obj)
    item_heading_dictionary = get_heading_dict(sorted(chunk_obj.list_items()), table_of_contents)
    all_chunks = chunk_document(chunk_obj, filing_date, company, item_heading_dictionary, form_type=form)
    logger.info("Processed %s, %s", ticker, filing_date)
    return all_chunks