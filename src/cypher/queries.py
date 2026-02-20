"""Neo4j Cypher queries for retrieval"""

SEC_VECTOR_RETRIEVAL_CYPHER = """
MATCH (c:Company)-[:FILED]->(f:Filing)-[:HAS_SECTION]->(h:Heading)
      -[:HAS_CONTENT]->(p:ParentChunk)-[:HAS_CHILD]->(cand:ChildChunk)
WHERE
  ($company IS NULL OR toLower(c.name) CONTAINS toLower($company))
  AND (size($periods)=0 OR f.period IN $periods)
  AND (size($forms)=0 OR f.form IN $forms)
  AND (
        size($headings)=0 OR
        any(hint IN $headings WHERE toLower(h.name) CONTAINS toLower(hint))
      )
WITH collect({cand:cand, c:c, f:f, h:h, p:p}) AS allowed

CALL db.index.vector.queryNodes($index_name, $top_k * 30, $embedding)
YIELD node, score

WITH node, score, allowed
UNWIND allowed AS a
WITH node, score, a
WHERE a.cand = node

WITH a.c AS c, a.f AS f, a.h AS h, a.p AS p, node, score
MATCH path =
  (c)-[:FILED]->(f)
    -[:HAS_SECTION]->(h)
    -[:HAS_CONTENT]->(p)
    -[:HAS_CHILD]->(node)

RETURN
  {
    child_chunk_id: node.chunk_id,
    child_text: node.content,
    parent_chunk_id: p.chunk_id,
    parent_text: p.content,
    sub_heading: p.sub_heading_dict,
    heading: h.name,
    period: f.period,
    form: f.form,
    company: c.name,
    filing_id: f.accession,
    score: score
  } AS content,
  {
    nodes: [n IN nodes(path) | {labels: labels(n), props: properties(n)}],
    rels:  [r IN relationships(path) | {type: type(r), props: properties(r)}]
  } AS graph_ui
ORDER BY score DESC
LIMIT $top_k
"""

TRANSCRIPT_VECTOR_RETRIEVAL_CYPHER = """
MATCH (c:Company)-[:HAS_TRANSCRIPT]->(t:Transcript)
      -[:HAS_CHUNK]->(p:TranscriptParentChunk)-[:HAS_CHILD]->(cand:TranscriptChildChunk)
WHERE
  ($company IS NULL OR toLower(c.name) CONTAINS toLower($company))
  AND (size($periods)=0 OR t.period IN $periods)
WITH collect({cand:cand, c:c, t:t, p:p}) AS allowed

CALL db.index.vector.queryNodes($index_name, $top_k * 30, $embedding)
YIELD node, score

WITH node, score, allowed
UNWIND allowed AS a
WITH node, score, a
WHERE a.cand = node

WITH a.c AS c, a.t AS t, a.p AS p, node, score
OPTIONAL MATCH (s:Speaker)-[:HAS_SPEECH]->(p)
OPTIONAL MATCH (s)-[:HAS_TITLE]->(title:Title)

MATCH path =
  (c)-[:HAS_TRANSCRIPT]->(t)
    -[:HAS_CHUNK]->(p)
    -[:HAS_CHILD]->(node)

RETURN
  {
    child_chunk_id: node.chunk_id,
    child_text: node.content,
    parent_chunk_id: p.chunk_id,
    parent_text: p.content,
    period: t.period,
    company: c.name,
    speaker: s.name,
    title: title.title_name,
    transcript_id: t.id,
    score: score
  } AS content,
  {
    nodes: [n IN nodes(path) | {labels: labels(n), props: properties(n)}],
    rels:  [r IN relationships(path) | {type: type(r), props: properties(r)}]
  } AS graph_ui
ORDER BY score DESC
LIMIT $top_k
"""

CHANGE_DETECTION_CYPHER = """
MATCH (c:Company {name:$company})-[:FILED]->(start:Filing)
WHERE start.period = $start_period

MATCH path = (start)-[:NEXT*0..]->(end:Filing)
WHERE end.period = $end_period

UNWIND nodes(path) AS f

MATCH hierarchy_path = (f)-[:HAS_SECTION]->(h:Heading)-[:HAS_CONTENT]->(p:ParentChunk)
WHERE (size($headings)=0 OR any(hint IN $headings WHERE toLower(h.name) CONTAINS toLower(hint)))

WITH DISTINCT c, f, h, p, 
    (nodes(path) + nodes(hierarchy_path)) AS all_nodes,
    (relationships(path) + relationships(hierarchy_path)) AS all_rels

RETURN 
{
    company: c.name, 
    period: f.period,
    filing_id: f.accession,
    form: f.form,
    heading: h.name,
    parent_chunk_id: p.chunk_id, 
    parent_text: p.content, 
    sub_heading: p.sub_heading_dict
} AS content,
{
    nodes: [n IN all_nodes | {labels: labels(n), props: properties(n)}],
    rels:  [r IN all_rels | {type: type(r), props: properties(r)}]
} AS graph_ui
ORDER BY f.period
"""