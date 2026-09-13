# Knowledge-graph schema (paper-radar)

Store: `data/<channel>/graph.json` — incremental, hand additions preserved.

## Node types

| type | id convention | key fields |
|---|---|---|
| paper | `doi:<doi>` / `arxiv:<id>` / `title:<normalized>` | label, year, citations, venue, source |
| author | `author:<lowercased name>` | label, openalex |
| group | `group:<lowercased institution>` | label (课题组 = institution lab/school level) |
| venue | `venue:<lowercased name>` | label |
| claim | `claim:<slug>:<n>` | label = 论点 (one sentence, authored during episode production from full text) |
| evidence | `evidence:<slug>:<n>` | label = 论据 (number/experiment + condition + source location) |

## Edge relations

| rel | from → to | meaning |
|---|---|---|
| cites | paper → paper | 引用（来自 OpenAlex references，图内闭合） |
| authored | author → paper | 著文 |
| member_of | author → group | 作者所属课题组（取第一机构，OpenAlex affiliations） |
| published_in | paper → venue | 刊于 |
| claims | paper → claim | 论文提出论点（episode 精读时人工添加） |
| supports | evidence → claim | 论据支撑论点 |

## Provenance rules

1. `cites` edges only exist between papers present in the graph (closed
   world); raw references to outside works are kept in the raw snapshots.
2. `claim`/`evidence` nodes are added only after close-reading the full text
   during an episode; each carries the source location in its label.
3. `group` is inferred from OpenAlex first affiliation — it approximates
   课题组 (institution level). Refinements (e.g. lab-level grouping) are
   appended as extra `member_of` edges, never by deleting originals.
4. Rankings (`group-rankings.json`) are derived artifacts; delete and
   regenerate at will.

## Rendering contract

Episode visuals must be exported by `scripts/render_graph.py`:
- `--mode global`: top-groups map with inter-group citation flow (领域格局).
- `--mode local --focus <id> --hops 2 [--highlight ...]`: ego network with
  focus glow and dimmed context (论文地位 / 课题组局部关系).
Spoken graph numbers must match the store, not memory.
