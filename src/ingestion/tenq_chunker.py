import re
import logging
from typing import List, Dict, Any
from edgar.files.html_documents import TextBlock, TableBlock 
from .toc import get_table_of_contents
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)



def get_correct_item(item: str, all_items: List[str]) -> str:
    """
    Try to match the item string to an actual table-of-contents item; fallback to a simple transformation.
    """
    for actual_item in all_items:
        if re.fullmatch(item + r"[^a-zA-Z0-9]*", actual_item):
            return actual_item
    parts = item.strip(". ").split()
    if len(parts) >= 2:
        return parts[0].capitalize() + " " + parts[1]
    return item


def get_heading_dict(all_items: List[str], table_of_contents) -> Dict[str, Any]:
    """
    Build a dictionary mapping 'Part I' and 'Part II' to their item headings.
    Structure: { 'Part I': {'Heading': '...', 'Items': {item: heading}} , 'Part II': {...} }
    """
    headings = {"Part I": {"Heading": "Financial Information", "Items": {}}, "Part II": {"Heading": "Other Information", "Items": {}}}
    if table_of_contents.empty:
        return headings

    part_1 = False
    part_2 = False
    for _, row in table_of_contents.iterrows():
        try:
            idx = str(row.name) if hasattr(row, "name") else str(row["Index"])
            if re.fullmatch(r"part i[^a-zA-Z0-9]*", idx.lower()) or "financial information" in idx.lower() and not part_1:
                headings["Part I"] = {"Heading": "Part I: Financial Information", "Items": {}}
                part_1, part_2 = True, False
            elif re.fullmatch(r"part ii[^a-zA-Z0-9]*", idx.lower()) or "other information" in idx.lower() and not part_2:
                headings["Part II"] = {"Heading": "Part II: Other Information", "Items": {}}
                part_1, part_2 = False, True

            if part_1:
                item = str(row.name).strip(".")
                heading = row["Headings"]
                if "item" in item.lower():
                    actual_item = get_correct_item(item, all_items)
                    headings["Part I"]["Items"][actual_item] = actual_item + ": " + str(heading).strip(":. \n")
            elif part_2:
                item = str(row.name).strip(".")
                heading = row["Headings"]
                if "item" in item.lower():
                    actual_item = get_correct_item(item, all_items)
                    headings["Part II"]["Items"][actual_item] = actual_item + ": " + str(heading).strip(":. \n")
        except Exception:
            logger.exception("Error parsing TOC row; skipping row.")
    return headings


def chunk_document(chunk_obj, filing_date: str, company: str, heading_dictionary: Dict[str, Any], form_type="10-Q", min_words=20) -> List[Dict[str, Any]]:
    """
    Chunking logic for 10-Q adapted from notebook. Similar structure as 10-K chunker with Parts.
    """
    regex1 = re.compile(
        r"""
        \n*.*?\s\|\s.*?\d{4}\sForm\s10-Q\s\|\s\d+\n*$
        """,
        re.VERBOSE,
    )
    regex2 = re.compile(r"^\n*\d+\n*$")

    metadata_template = {
        "part_heading": None,
        "item_heading": None,
        "filing_date": filing_date,
        "company": company,
        "form": form_type,
        "is_table": False,
    }

    all_chunks = []
    for part in ["Part I", "Part II"]:
        metadata_template["part_heading"] = heading_dictionary.get(part, {}).get("Heading")
        part_items = list(heading_dictionary.get(part, {}).get("Items", {}).keys())
        chunk_for_part = chunk_obj.chunks_for_part(part)

        Headings = {}
        processed_chunk = []
        prev_content = False
        prev_heading = False
        metadata_chunk = metadata_template.copy()

        for chunk in chunk_for_part:
            for element in chunk:
                if isinstance(element, TextBlock):
                    text_raw = element.get_text()
                    if element.is_header:
                        if regex1.fullmatch(text_raw) or regex2.fullmatch(text_raw):
                            Headings = {}
                            continue

                        # detect if header indicates an item and switch metadata
                        for item in part_items:
                            item_heading = re.sub(r"item\s*\d*\W*:\s*", "", heading_dictionary[part]["Items"][item].lower())
                            if item_heading in text_raw.lower():
                                if processed_chunk:
                                    chunk_text = "\n".join(processed_chunk)
                                    if len(chunk_text.split()) > min_words:
                                        all_chunks.append({"Metadata": metadata_chunk, "Chunks": {"parent_chunk": chunk_text}})
                                        processed_chunk = []
                                metadata_template["item_heading"] = heading_dictionary[part]["Items"][item]

                        text = text_raw.strip("\n").strip(" ")
                        if "item" in text.lower() or "part" in text.lower():
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
                            metadata_chunk = metadata_template.copy()
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
                    for item in part_items:
                        item_heading = re.sub(r"item\s*\d*\W*:\s*", "", heading_dictionary[part]["Items"][item].lower())
                        if item_heading in element.get_text().lower():
                            if processed_chunk:
                                chunk_text = "\n".join(processed_chunk)
                                if len(chunk_text.split()) > min_words:
                                    all_chunks.append({"Metadata": metadata_chunk, "Chunks": {"parent_chunk": chunk_text}})
                                processed_chunk = []
                            metadata_template["item_heading"] = heading_dictionary[part]["Items"][item]

                    if element.get_text().lower().count("item") < 6:
                        metadata_chunk = metadata_template.copy()
                        if prev_heading or prev_content:
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
                            if len(text.split()) < min_words and len(text.split()) > 5:
                                chunk_text = text

                        chunk_text += element.get_text()
                        metadata_chunk["is_table"] = True
                        all_chunks.append({"Metadata": metadata_chunk, "Chunks": {"parent_chunk": chunk_text}})
                        prev_content = True
                        prev_heading = False
                else:
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


def get_chunks(filing_date: str, ticker: str, company: str, cik: int, accession_no: str, form="10-Q"):
    """
    Wrapper to create Filing and chunk a 10-Q.
    """
    from edgar import Filing  # local import to raise helpful error if edgar missing

    filing = Filing(form=form, filing_date=filing_date, company=ticker, cik=cik, accession_no=accession_no)
    obj = filing.obj()
    chunk_obj = obj.chunked_document

    table_of_contents = get_table_of_contents(chunk_obj)
    heading_dictionary = get_heading_dict(sorted(chunk_obj.list_items()), table_of_contents)
    all_chunks = chunk_document(chunk_obj, filing_date, company, heading_dictionary, form_type=form)
    logger.info("Processed %s, %s", ticker, filing_date)
    return all_chunks