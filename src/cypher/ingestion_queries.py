# --- SEC Queries ---

SEC_INGESTION_BATCH = """
UNWIND $batch AS data
MERGE (company:Company {name: data.company_name})
MERGE (filing:Filing {accession: data.accession_no})
SET filing.form = data.form_type, filing.date = date(data.filing_date)
MERGE (company)-[:FILED]->(filing)

MERGE (heading:Heading {name: data.heading_name, accession: data.accession_no})
MERGE (filing)-[:HAS_SECTION]->(heading)

MERGE (parent:ParentChunk {chunk_id: data.parent_chunk_id})
SET parent.content = data.parent_chunk_content,
    parent.sub_heading_dict = data.sub_headings,
    parent.is_table = data.is_table
MERGE (heading)-[:HAS_CONTENT]->(parent)

WITH parent, data
UNWIND keys(data.child_chunks) AS child_id
MERGE (child:ChildChunk {chunk_id: child_id})
SET child.content = data.child_chunks[child_id]
MERGE (parent)-[:HAS_CHILD]->(child)

WITH child, data, child_id
CALL db.create.setNodeVectorProperty(child, "embedding", data.embeddings[child_id])
"""

SEC_INIT_VECTOR_INDEX = """
CREATE VECTOR INDEX childchunks IF NOT EXISTS
FOR (child:ChildChunk)
ON child.embedding
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}}
"""

SEC_10Q_PERIOD = """
MATCH (c:Company)-[:FILED]->(f:Filing {form: "10-Q"})
WITH c, f, f.date.year AS year ORDER BY c.name, year, f.date
WITH c, year, collect(f) AS filings
UNWIND range(0, size(filings)-1) AS i
WITH filings[i] AS f, i, year
SET f.period = "Q" + toString(i + 1) + "_" + toString(year)
"""

SEC_10K_PERIOD = """
MATCH (f:Filing {form: "10-K"})
SET f.period = "FY_" + toString(f.date.year)
"""

SEC_NEXT_REL = """
MATCH (c:Company)-[:FILED]->(f:Filing)
WITH c, f.form AS form, f ORDER BY c.name, form, f.date
WITH c, form, collect(f) AS filings
UNWIND range(0, size(filings)-2) AS i
WITH filings[i] AS f1, filings[i+1] AS f2
MERGE (f1)-[:NEXT]->(f2)
"""

# --- Transcript Queries ---

TRANSCRIPT_INGESTION_BATCH = """
UNWIND $batch AS data
MATCH (company:Company {name: data.company_name})
MATCH (company)-[:FILED]->(f:Filing)
WHERE f.form = "10-Q" AND f.period = data.period

MERGE (t:Transcript {
    company: data.company_name,
    period: data.period,
    id: data.company_name + '_' + data.period
})
MERGE (company)-[:HAS_TRANSCRIPT]->(t)
MERGE (t)-[:ASSOCIATED_WITH]->(f)

MERGE (s:Speaker {name: data.speaker_name})
MERGE (title:Title {title_name: data.speaker_title})
MERGE (s)-[:HAS_TITLE]->(title)

MERGE (p:TranscriptParentChunk {chunk_id: data.parent_chunk_id})
SET p.content = data.parent_chunk_content
MERGE (t)-[:HAS_CHUNK]->(p)
MERGE (s)-[:HAS_SPEECH]->(p)

WITH t, p, data
UNWIND keys(data.child_chunks) AS child_id
MERGE (tc:TranscriptChildChunk {chunk_id: child_id})
SET tc.content = data.child_chunks[child_id]
MERGE (p)-[:HAS_CHILD]->(tc)

WITH t, tc, data, child_id
CALL db.create.setNodeVectorProperty(tc, "embedding", data.embeddings[child_id])
"""

TRANSCRIPT_INIT_VECTOR_INDEX = """
CREATE VECTOR INDEX tc IF NOT EXISTS
FOR (tc:TranscriptChildChunk)
ON tc.embedding
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}}
"""

TRANSCRIPT_NEXT_REL = """
MATCH (c:Company)-[:HAS_TRANSCRIPT]->(t:Transcript)
WITH c, t ORDER BY c.name, t.period
WITH c, collect(t) AS transcripts
UNWIND range(0, size(transcripts)-2) AS i
WITH transcripts[i] AS t1, transcripts[i+1] AS t2
MERGE (t1)-[:NEXT]->(t2)
"""