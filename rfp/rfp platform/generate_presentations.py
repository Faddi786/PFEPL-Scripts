import html, json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "doslr_webgis_atlas.html"
SECTION_DIRS = {"A": ROOT/"A-System","B": ROOT/"B-Database","C": ROOT/"C-Data-Flow","D": ROOT/"D-Workflows","E": ROOT/"E-Lifecycle","F": ROOT/"F-Sequence"}
SECTION_LABELS = {"A":("System","How the whole thing fits together"),"B":("Database","The 28-table schema, entity by entity"),"C":("Data Flow","Where information travels"),"D":("Workflows","The step-by-step processes"),"E":("Lifecycle","How records change state"),"F":("Sequence","End-to-end interactions over time")}
SG_START = re.compile(r"^\s*subgraph\s+(\S+)(?:\[(.+?)\])?\s*$")
SG_END = re.compile(r"^\s*end\s*$")
NODE_DEF = re.compile(r"^(\s*)([A-Za-z_][\w]*)\s*(\[\[|\[\(|\(\(\(|\(\(|\[|\{|\()")
ER_REL = re.compile(r"^\s*([A-Z_][A-Z0-9_]*)\s+\|\|?--[o|]{1,2}\{\s*([A-Z_][A-Z0-9_]*)\s*:\s*(.+)$")
ER_ENT = re.compile(r"^\s*([A-Z_][A-Z0-9_]*)\s*\{\s*$")
ST_TR = re.compile(r"^\s*(\[\*\]|[A-Za-z_][\w]*)\s*-->\s*(\[\*\]|[A-Za-z_][\w]*)\s*:\s*(.+)$")
ST_NOTE = re.compile(r"^\s*note\s+(right|left)\s+of\s+(\S+)\s*$")
SEQ_P = re.compile(r"^\s*(participant|actor)\s+(\S+)(?:\s+as\s+(.+))?\s*$")
def node_id(line):
    m = re.match(r'^\s*([A-Za-z_][\w]*)', line.strip())
    return m.group(1) if m else line.strip().split()[0]

SEQ_M = re.compile(r"^\s*(\S+)\s*(-?>>|-->>|--x|->>|->>\+|-->>\+|-x)\s*(\S+)\s*:\s*(.+)$")

def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii","ignore").decode()
    t = re.sub(r"[^\w\s-]", "", t.lower())
    return re.sub(r"[-\s·]+", "-", t).strip("-") or "diagram"

def clean(raw):
    if not raw: return ""
    s = html.unescape(raw.strip())
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()

def note(kind, detail):
    detail = clean(detail)
    if not detail: return "Introduce this element and how it connects to the overall design."
    m = {"node": f"Introduce <strong>{detail}</strong> — explain its role.","edge": f"Describe the flow: <strong>{detail}</strong>.","relation": f"Explain the relationship: <strong>{detail}</strong>.","transition": f"State change: <strong>{detail}</strong>.","message": f"Interaction: <strong>{detail}</strong>."}
    return m.get(kind, f"Explain: <strong>{detail}</strong>.")

def strip_node_token(tok):
    tok = tok.strip()
    m = re.match(r"^([A-Za-z_][\w]*)", tok)
    return m.group(1) if m else tok.split()[0]

def parse_edge_rest(src, arrow, rest):
    rest = rest.strip()
    label, tgt_part = "", rest
    m = re.match(r'\|"([^"]*)"\|\s*(.+)$', rest)
    if m:
        label, tgt_part = m.group(1), m.group(2)
    else:
        m2 = re.match(r"\|([^|]+)\|\s*(.+)$", rest)
        if m2:
            label, tgt_part = m2.group(1).strip(), m2.group(2)
    src_id, tgt_id = strip_node_token(src), strip_node_token(tgt_part)
    return (src_id, arrow, label, tgt_id)

def split_edges(line):
    line = line.strip()
    if not line or line.startswith("subgraph") or line.startswith("end"):
        return []
    if "&" in line and re.search(r"-->|-.[^-]*?\.->|<-->", line):
        parts = re.split(r"\s+&\s+", line)
        m = re.match(r"^(.+?)\s*(<-->|<-->|-.[^-]*?\.->|-->)\s*(.*)$", parts[0])
        if not m:
            return split_chain(line)
        src, arrow, rest = m.groups()
        first = parse_edge_rest(src, arrow, rest)
        out = [first]
        for tgt in parts[1:]:
            out.append((first[0], first[1], first[2], strip_node_token(tgt)))
        return out
    return split_chain(line)

def split_chain(line):
    pattern = r"\s*(<-->|<-->|-.[^-]*?\.->|-->)\s*(?:\|\"([^\"]*)\"\||\|([^|]*)\|)?\s*"
    parts = re.split(pattern, line)
    if len(parts) < 4:
        return []
    out = []
    src = parts[0].strip()
    i = 1
    while i < len(parts) - 1:
        arrow = parts[i]
        qlabel = parts[i + 1] if i + 1 < len(parts) else ""
        ulabel = parts[i + 2] if i + 2 < len(parts) else ""
        rest = parts[i + 3] if i + 3 < len(parts) else ""
        label = (qlabel or ulabel or "").strip()
        if i + 3 < len(parts):
            tgt_part = parts[i + 3]
            i += 4
        else:
            break
        out.append((strip_node_token(src), arrow, label, strip_node_token(tgt_part)))
        src = tgt_part
    return out

def is_node(line):
    s = line.strip()
    return s and not s.startswith(("subgraph","end")) and not re.search(r"-->|-.[^-]*?\.->|<-->", s) and bool(NODE_DEF.match(s))

def parse_body(lines):
    flat, meta, stack = [], {}, []
    for line in lines[1:]:
        ms = SG_START.match(line)
        if ms:
            stack.append(ms.group(1)); meta[ms.group(1)] = {"nodes": set()}; flat.append(line); continue
        if SG_END.match(line):
            flat.append(line); stack.pop() if stack else None; continue
        flat.append(line)
        if stack and is_node(line): meta[stack[-1]]["nodes"].add(node_id(line))
    return flat, meta

def bfs_order(nodes, edges):
    if not edges:
        return []
    start = edges[0][0]
    ns = set(nodes)
    for s, _, _, tg in edges:
        ns.update((s, tg))
    adj = {n: [] for n in ns}
    for e in edges:
        adj.setdefault(e[0], []).append(e)
    q, seen, ord_, visited = [start], set(), [], {start}
    while q:
        c = q.pop(0)
        for e in adj.get(c, []):
            if e in seen:
                continue
            seen.add(e)
            ord_.append(e)
            if e[3] not in visited:
                visited.add(e[3])
                q.append(e[3])
    for e in edges:
        if e not in seen:
            ord_.append(e)
    return ord_

def render_fc(header, lines, vnodes, vedges, nsg, vdefs=None):
    need = {nsg[n] for n in vnodes if n in nsg}
    out, i = [header], 0
    while i < len(lines):
        line = lines[i]; ms = SG_START.match(line)
        if ms:
            sid = ms.group(1)
            if sid not in need:
                i += 1; d = 1
                while i < len(lines) and d:
                    if SG_START.match(lines[i]): d += 1
                    if SG_END.match(lines[i]): d -= 1
                    i += 1
                continue
            out.append(line); i += 1; d = 1
            while i < len(lines) and d:
                inner = lines[i]
                if SG_START.match(inner): d += 1
                if SG_END.match(inner):
                    d -= 1
                    if d == 0: out.append(inner); i += 1; break
                if is_node(inner):
                    if node_id(inner) in (vdefs or vnodes): out.append(inner)
                else:
                    p = split_edges(inner)
                    if p and all(e in vedges for e in p): out.append(inner)
                i += 1
            continue
        if SG_END.match(line): i += 1; continue
        if is_node(line):
            nid = node_id(line)
            if nid in (vdefs or vnodes) and nid not in nsg: out.append(line)
        else:
            p = split_edges(line)
            if p and all(e in vedges for e in p): out.append(line)
        i += 1
    return "\n".join(out)

def build_fc(text):
    lines = [html.unescape(ln.rstrip()) for ln in text.strip().splitlines() if ln.strip()]
    header, body, _ = lines[0], *parse_body(lines)
    nodes, nsg, edges, stack = {}, {}, [], []
    for line in body:
        if SG_START.match(line): stack.append(SG_START.match(line).group(1)); continue
        if SG_END.match(line): stack.pop() if stack else None; continue
        if is_node(line):
            nid = node_id(line); nodes[nid] = line.strip()
            if stack: nsg[nid] = stack[-1]
        else: edges.extend(split_edges(line))
    ord_ = bfs_order(nodes, edges)
    steps, vnodes, vedges, vdefs = [], set(), set(), set()
    start = edges[0][0] if edges else next(iter(nodes), "start")
    vnodes.add(start)
    if start in nodes: vdefs.add(start)
    first_mermaid = render_fc(header, body, vnodes, vedges, nsg, vdefs)
    first_add = [{"t": "node", "id": start}]
    ord_skip = 0
    if first_mermaid.strip() == header.strip() and ord_:
        e = ord_[0]
        vedges.add(e)
        vnodes.update({e[0], e[3]})
        first_mermaid = render_fc(header, body, vnodes, vedges, nsg, vdefs)
        first_add = [{"t": "node", "id": e[0]}]
        if e[3] != e[0]:
            first_add.append({"t": "node", "id": e[3]})
        first_add.append({"t": "edge", "from": e[0], "to": e[3]})
        ord_skip = 1
        seen_nodes = {e[0], e[3]}
    else:
        seen_nodes = {start}
    steps.append({"mermaid": first_mermaid, "note": note("node", clean(nodes.get(start, start))), "add": first_add})
    for e in ord_[ord_skip:]:
        src, arrow, label, tgt = e
        add = []
        for nid in (src, tgt):
            if nid not in seen_nodes:
                seen_nodes.add(nid)
                add.append({"t": "node", "id": nid})
            vnodes.add(nid)
            if nid in nodes: vdefs.add(nid)
        vedges.add(e)
        add.append({"t": "edge", "from": src, "to": tgt})
        lbl = clean(label) if label else f"{src} to {tgt}"
        steps.append({"mermaid": render_fc(header, body, vnodes, vedges, nsg, vdefs), "note": note("edge", lbl), "add": add})
    return steps
def build_er(text):
    lines = [html.unescape(ln.rstrip()) for ln in text.strip().splitlines()]
    rels, blocks, cur, steps = [], {}, None, []
    for line in lines[1:]:
        mr = ER_REL.match(line)
        if mr: rels.append((mr.group(1), mr.group(2), mr.group(3), line.strip())); continue
        me = ER_ENT.match(line)
        if me: cur = me.group(1); blocks[cur] = [line.strip()]; continue
        if cur and re.match(r"^\s*\}\s*$", line): blocks[cur].append(line.strip()); cur = None; continue
        if cur: blocks[cur].append(line.strip())
    vr, ve = [], set()
    for a,b,lbl,rl in rels:
        vr.append(rl); ve.update((a,b))
        blk = [lines[0]] + vr + [x for ent in sorted(ve) if ent in blocks for x in blocks[ent]]
        steps.append({"mermaid":"\n".join(blk), "note": note("relation", f"{a} → {b}: {lbl}"), "add": [{"t": "rel", "a": a, "b": b}]})
    return steps or [{"mermaid": text.strip(), "note": note("relation", "Schema overview")}]

def build_state(text):
    lines = [html.unescape(ln.rstrip()) for ln in text.strip().splitlines() if ln.strip()]
    hdr, trans, notes, steps, seen_states = [], [], [], [], set()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("stateDiagram") or line.startswith("direction "): hdr.append(line); i += 1; continue
        mn = ST_NOTE.match(line)
        if mn:
            st = mn.group(2); nl = [line]; i += 1
            while i < len(lines) and not re.match(r"^\s*end\s+note\s*$", lines[i]): nl.append(lines[i]); i += 1
            if i < len(lines): nl.append(lines[i])
            notes.append((st, nl)); i += 1; continue
        mt = ST_TR.match(line)
        if mt: trans.append((mt.group(1), mt.group(2), mt.group(3), line))
        i += 1
    vis = []
    for s,t,lbl,ln in trans:
        vis.append(ln)
        blk = hdr + vis
        for st,nl in notes:
            if st in (s,t) or any(st in v for v in vis): blk.extend(nl)
        add = []
        if s not in seen_states:
            seen_states.add(s); add.append({"t": "state", "id": s})
        if t not in seen_states:
            seen_states.add(t); add.append({"t": "state", "id": t})
        add.append({"t": "trans", "from": s, "to": t})
        steps.append({"mermaid":"\n".join(blk), "note": note("transition", f"{s} → {t}: {lbl}"), "add": add})
    return steps or [{"mermaid": text.strip(), "note": note("transition", "Lifecycle overview")}]

def build_seq(text):
    lines = [html.unescape(ln.rstrip()) for ln in text.strip().splitlines() if ln.strip()]
    hdr = lines[0]; parts, plines, msgs = [], {}, []
    for line in lines[1:]:
        mp = SEQ_P.match(line)
        if mp: pid = mp.group(2); parts.append(pid); plines[pid] = line; continue
        mm = SEQ_M.match(line)
        if mm: msgs.append((line, clean(mm.group(4))))
    dec, vis, steps, seen_actors, msg_n = [], [], [], set(), 0
    for line, lbl in msgs:
        mm = SEQ_M.match(line)
        if mm:
            for pid in (mm.group(1), mm.group(3)):
                if pid in plines and pid not in dec: dec.append(pid)
        vis.append(line)
        blk = [hdr] + [plines[p] for p in parts if p in dec] + vis
        frm, to = strip_node_token(mm.group(1)), strip_node_token(mm.group(3))
        add = []
        for p in (frm, to):
            if p not in seen_actors:
                seen_actors.add(p); add.append({"t": "actor", "id": p})
        add.append({"t": "msg", "from": frm, "to": to, "n": msg_n})
        msg_n += 1
        steps.append({"mermaid":"\n".join(blk), "note": note("message", lbl), "add": add})
    return steps or [{"mermaid": text.strip(), "note": note("message", "Sequence overview")}]

def build_steps(m):
    t = m.strip()
    k = t.splitlines()[0].split()[0]
    return {"flowchart": build_fc, "erDiagram": build_er, "stateDiagram-v2": build_state, "sequenceDiagram": build_seq}.get(
        k, lambda x: [{"mermaid": html.unescape(x), "note": note("node", "Overview")}]
    )(t)

def extract(html_src):
    out = []
    pp = re.compile(r'<section id="part-([A-F])" class="part">.*?<h2 class="part-title">([^<]+)</h2>\s*<p class="part-tag">([^<]+)</p>.*?</section>', re.S)
    cp = re.compile(r'<figure class="card"[^>]*>.*?<span class="eyebrow">([^<]+)</span>\s*<h3 class="card-title">([^<]+)</h3>\s*<p class="caption">([^<]+)</p>.*?<div class="mermaid">(.*?)</div>', re.S)
    for part in pp.finditer(html_src):
        letter, stitle, stag = part.group(1), html.unescape(part.group(2).strip()), html.unescape(part.group(3).strip())
        for card in cp.finditer(part.group(0)):
            out.append({"section_letter":letter,"section_title":stitle,"section_tag":stag,"eyebrow":html.unescape(card.group(1).strip()),"title":html.unescape(card.group(2).strip()),"caption":html.unescape(card.group(3).strip()),"mermaid":re.sub(r"\s*\n\s*","\n",card.group(4).strip()),"slug":slugify(card.group(2).strip())})
    return out

def build_nav_catalog(diags):
    by = {}
    for d in diags:
        by.setdefault(d["section_letter"], []).append({"slug": d["slug"], "title": d["title"]})
    return by

def nav_href(from_letter, to_letter, slug):
    from_dir = SECTION_DIRS[from_letter].name
    to_dir = SECTION_DIRS[to_letter].name
    target = f"{slug}.html"
    return target if from_dir == to_dir else f"../{to_dir}/{target}"

def render_nav(from_letter, current_slug, catalog):
    current_title = None
    sections = []
    for letter in "ABCDEF":
        diags_in = catalog.get(letter, [])
        if not diags_in:
            continue
        section_title = SECTION_LABELS[letter][0]
        links = []
        for d in diags_in:
            href = nav_href(from_letter, letter, d["slug"])
            is_current = letter == from_letter and d["slug"] == current_slug
            if is_current:
                current_title = d["title"]
            cls = " is-current" if is_current else ""
            links.append(
                f'<a class="nav-link{cls}" href="{html.escape(href)}">{html.escape(d["title"])}</a>'
            )
        sections.append(
            f'<li class="nav-section-item">'
            f'<span class="nav-section-label" tabindex="0">{html.escape(section_title)}</span>'
            f'<div class="nav-flyout" role="menu">{"".join(links)}</div></li>'
        )
    trigger = current_title or "Jump to diagram"
    return (
        '<nav class="pres-nav" aria-label="Diagram navigation">'
        '<div class="nav-dropdown">'
        f'<button class="nav-trigger" type="button" aria-haspopup="true">{html.escape(trigger)} '
        '<span class="nav-caret" aria-hidden="true">&#9662;</span></button>'
        f'<div class="nav-panel"><ul class="nav-sections">{"".join(sections)}</ul></div>'
        '</div></nav>'
    )


PRES = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>__TITLE__ — DoSLR Presentation</title><style>
:root{--paper:#EEF1F5;--panel:#FFF;--ink:#13213B;--ink2:#46546F;--line:#CBD4E1;--sans:ui-sans-serif,system-ui,sans-serif;--mono:ui-monospace,Consolas,monospace;--step-ms:320}
html{scroll-behavior:smooth}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);overflow-anchor:none}
main{max-width:1100px;margin:0 auto;padding:22px}
.page-head{margin:0 0 14px}
.page-title{margin:0;font-size:clamp(18px,2.6vw,26px);font-weight:650;letter-spacing:-.01em}
.page-desc{margin:6px 0 0;font-size:14px;color:var(--ink2);line-height:1.45}
.nav-row{margin:0 0 12px;display:flex;align-items:center;justify-content:space-between;gap:0}
.back{color:var(--ink);flex:0 0 auto;text-decoration:none;font-family:var(--mono);font-size:12px;opacity:.75;display:inline-block}
.back:hover{opacity:1}
.pres-nav{position:relative;font-size:13px;flex:0 0 auto;margin-left:auto}
.nav-dropdown{position:relative}
.nav-trigger{display:flex;align-items:center;gap:6px;padding:8px 14px;background:var(--panel);border:1px solid var(--line);border-radius:7px;color:var(--ink);font-size:13px;font-weight:550;cursor:pointer;font-family:var(--sans)}
.nav-trigger:hover,.nav-dropdown:hover .nav-trigger,.nav-dropdown:focus-within .nav-trigger,.nav-dropdown.is-open .nav-trigger{background:#E9EEF6;border-color:#B8C5D8}
.nav-caret{font-size:10px;opacity:.7}
.nav-panel{display:none;position:absolute;top:100%;right:0;margin-top:0;padding-top:8px;min-width:200px;background:transparent;border:none;border-radius:0;box-shadow:none;z-index:40;pointer-events:none}
.nav-panel::before{content:"";position:absolute;top:0;left:0;right:0;height:8px;pointer-events:auto}
.nav-panel>.nav-sections{pointer-events:auto;background:var(--panel);border:1px solid var(--line);border-radius:7px;box-shadow:0 10px 28px rgba(19,33,59,.14)}
.nav-dropdown:hover .nav-panel,.nav-dropdown:focus-within .nav-panel,.nav-dropdown.is-open .nav-panel{display:block}
.nav-sections{list-style:none;margin:0;padding:6px 0}
.nav-section-item{position:relative}
.nav-section-label{display:block;padding:8px 14px;color:var(--ink);font-weight:550;cursor:default;white-space:nowrap;user-select:none}
.nav-section-item:hover>.nav-section-label,.nav-section-item:focus-within>.nav-section-label{background:var(--paper)}
.nav-flyout{display:none;position:absolute;left:100%;top:0;margin-left:0;padding:8px 0;min-width:248px;background:var(--panel);border:1px solid var(--line);border-radius:7px;box-shadow:0 10px 28px rgba(19,33,59,.14);z-index:50}
.nav-flyout::before{content:"";position:absolute;top:0;left:-8px;width:8px;height:100%;pointer-events:auto}
.nav-section-item:hover .nav-flyout,.nav-section-item:focus-within .nav-flyout{display:block}
.nav-link{display:block;padding:8px 14px;color:var(--ink2);text-decoration:none;font-size:13px;line-height:1.35;border-left:3px solid transparent}
.nav-link:hover{background:var(--paper);color:var(--ink)}
.nav-link.is-current{color:#D9542B;font-weight:650;border-left-color:#D9542B;background:#F4E6DC}
.canvas{background:var(--panel);border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 24px rgba(19,33,59,.06);overflow:hidden}
.diagram-area{padding:10px 18px 18px;min-height:300px;display:flex;justify-content:center;align-items:flex-start;overflow:hidden}
.diagram-area .mermaid{width:100%;display:flex;justify-content:center;position:relative}
.diagram-area svg{max-width:100%;height:auto;display:block}
.diagram-area svg.pres-enter{animation:presFadeIn var(--step-ms) ease-out both}
@keyframes presFadeIn{from{opacity:.2}to{opacity:1}}
</style></head><body><main><div class="page-head"><h1 class="page-title">__SECTION_TITLE__ - __TITLE__</h1><p class="page-desc">__CAPTION__</p></div><div class="nav-row"><a class="back" href="../index.html">← All presentations</a>__NAV_HTML__</div><div class="canvas"><div class="diagram-area" id="diagramArea"><div class="mermaid" id="diagram"></div></div></div></main><script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.3/mermaid.min.js"></script><script>
const STEPS=__STEPS_JSON__;
const STEP_MS=320;
let stepIndex=0,busy=false,renderSeq=0,prevBottom=0;
mermaid.initialize({startOnLoad:false,securityLevel:"loose",theme:"base",fontFamily:"ui-sans-serif,system-ui,sans-serif",themeVariables:{background:"transparent",primaryColor:"#E9EEF6",primaryBorderColor:"#13213B",primaryTextColor:"#13213B",lineColor:"#7C8BA6",secondaryColor:"#F4E6DC",tertiaryColor:"#FFFFFF",mainBkg:"#E9EEF6",nodeBorder:"#33425E",clusterBkg:"#F7F9FC",clusterBorder:"#C2CCDC",titleColor:"#13213B",edgeLabelBackground:"#EEF1F5",actorBkg:"#E9EEF6",actorBorder:"#33425E",actorTextColor:"#13213B",signalColor:"#46546F",signalTextColor:"#13213B",labelBoxBkgColor:"#F4E6DC",labelBoxBorderColor:"#D9542B",noteBkgColor:"#F4E6DC",noteBorderColor:"#D9542B",noteTextColor:"#13213B",attributeBackgroundColorPeach:"#F4E6DC",attributeBackgroundColorOdd:"#FFFFFF",attributeBackgroundColorEven:"#F2F5F9"},flowchart:{curve:"basis",useMaxWidth:true,htmlLabels:true,padding:14},er:{useMaxWidth:true},sequence:{useMaxWidth:true,actorMargin:42,boxMargin:8}});
const diagramArea=document.getElementById("diagramArea"),diagramEl=document.getElementById("diagram");
function wait(ms){return new Promise(r=>setTimeout(r,ms))}
function svgDocBottom(svg){if(!svg)return 0;return svg.getBoundingClientRect().bottom+window.scrollY}
function ensureVisible(el,forward){if(!el)return;const pad=72,r=el.getBoundingClientRect?.()||diagramArea.getBoundingClientRect(),vh=window.innerHeight;if(r.top<pad){window.scrollBy({top:r.top-pad,behavior:"smooth"});return}if(r.bottom>vh-pad){window.scrollBy({top:r.bottom-(vh-pad),behavior:"smooth"});return}if(forward&&prevBottom){const svg=diagramEl.querySelector("svg");const growth=svgDocBottom(svg)-prevBottom;if(growth>40)window.scrollBy({top:Math.min(growth*.55,240),behavior:"smooth"})}}
async function renderStep(forward=true,initial=false){if(busy)return;busy=true;const seq=++renderSeq;const step=STEPS[stepIndex];diagramEl.removeAttribute("data-processed");diagramEl.textContent=step.mermaid;try{await mermaid.run({nodes:[diagramEl]})}catch(err){if(seq===renderSeq)diagramEl.innerHTML='<pre style="color:#D9542B">'+err.message+"</pre>";busy=false;return}if(seq!==renderSeq){busy=false;return}const svg=diagramEl.querySelector("svg");if(svg&&!initial){svg.classList.add("pres-enter");void svg.offsetWidth;svg.classList.remove("pres-enter")}if(!initial)ensureVisible(svg||diagramArea,forward);prevBottom=svgDocBottom(svg);busy=false}
async function goStep(delta){const next=stepIndex+delta;if(next<0||next>=STEPS.length||busy)return;stepIndex=next;await renderStep(delta>0,false)}
document.addEventListener("keydown",e=>{if(e.key==="ArrowLeft"){e.preventDefault();goStep(-1)}if(e.key==="ArrowRight"){e.preventDefault();goStep(1)}});

(function(){
  document.querySelectorAll(".nav-dropdown").forEach(function(dd){
    var btn=dd.querySelector(".nav-trigger");
    if(!btn)return;
    btn.setAttribute("aria-expanded","false");
    btn.addEventListener("click",function(e){
      e.stopPropagation();
      var open=dd.classList.toggle("is-open");
      btn.setAttribute("aria-expanded",open?"true":"false");
    });
    document.addEventListener("click",function(e){
      if(!dd.contains(e.target)){
        dd.classList.remove("is-open");
        btn.setAttribute("aria-expanded","false");
      }
    });
  });
})();

stepIndex=0;renderStep(true,true);
</script></body></html>
"""

IDX = """<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>DoSLR WebGIS — Step-by-Step Presentations</title><style>:root{{--paper:#EEF1F5;--panel:#FFF;--ink:#13213B;--ink2:#46546F;--line:#CBD4E1;--accent:#D9542B;--accent2:#1F6F8B;--sans:ui-sans-serif,system-ui,sans-serif;--mono:ui-monospace,Consolas,monospace}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.5}}header{{background:var(--ink);color:#fff;padding:34px 22px}}.inner{{max-width:1100px;margin:0 auto}}.kicker{{font-family:var(--mono);font-size:11px;letter-spacing:.28em;text-transform:uppercase;color:#9fb0c9;margin:0 0 10px}}h1{{margin:0;font-size:clamp(24px,4vw,40px)}}h1 b{{color:var(--accent)}}.sub{{margin:10px 0 0;color:#c5d0e0;max-width:65ch}}main{{max-width:1100px;margin:0 auto;padding:24px 22px 48px}}section{{margin-bottom:32px}}.part-head{{display:flex;align-items:center;gap:12px;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--line)}}.mark{{width:36px;height:36px;display:grid;place-items:center;border:1.5px solid var(--accent);color:var(--accent);border-radius:7px;font-family:var(--mono);font-weight:700}}.part-title{{margin:0;font-size:20px}}.part-tag{{margin:2px 0 0;font-size:13px;color:var(--ink2)}}.grid{{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}}a.card{{display:block;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px 18px;text-decoration:none;color:inherit}}a.card:hover{{border-color:var(--accent2);transform:translateY(-1px)}}.eyebrow{{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);font-weight:600}}.card-title{{margin:6px 0 4px;font-size:16px;font-weight:650}}.caption{{margin:0;font-size:13px;color:var(--ink2)}}.meta{{margin-top:8px;font-family:var(--mono);font-size:11px;color:var(--ink2)}}footer{{max-width:1100px;margin:0 auto;padding:20px 22px;border-top:1px solid var(--line);font-family:var(--mono);font-size:11px;color:var(--ink2)}}</style></head><body><header><div class=\"inner\"><p class=\"kicker\">RFP M-13/1237/2025 · DoSLR Puducherry</p><h1>WebGIS Platform<br><b>Step-by-Step Presentations</b></h1><p class=\"sub\">Interactive cumulative reveal for all 22 atlas diagrams — use Previous/Next or arrow keys during walkthroughs.</p></div></header><main>{sections_html}</main><footer>Generated from doslr_webgis_atlas.html · Mermaid 10.9.3 · DoSLR color palette</footer></body></html>"""

def render_index(diags):
    parts = []
    by = {}
    for d in diags: by.setdefault(d["section_letter"], []).append(d)
    for letter in "ABCDEF":
        items = by.get(letter, [])
        if not items: continue
        title, tag = SECTION_LABELS[letter]
        cards = []
        for d in items:
            href = f"{SECTION_DIRS[letter].name}/{d['slug']}.html"
            cards.append(f'<a class="card" href="{html.escape(href)}"><span class="eyebrow">{html.escape(d["eyebrow"])}</span><div class="card-title">{html.escape(d["title"])}</div><p class="caption">{html.escape(d["caption"])}</p><p class="meta">{len(build_steps(d["mermaid"]))} steps</p></a>')
        parts.append(f'<section id="part-{letter}"><div class="part-head"><span class="mark">{letter}</span><div><h2 class="part-title">{title}</h2><p class="part-tag">{tag}</p></div></div><div class="grid">{"".join(cards)}</div></section>')
    (ROOT/"index.html").write_text(IDX.format(sections_html="\n".join(parts)), encoding="utf-8")

def main():
    if not SOURCE.exists(): raise SystemExit(f"Source not found: {SOURCE}")
    diags = extract(SOURCE.read_text(encoding="utf-8"))
    if len(diags) != 22: print(f"Warning: expected 22 diagrams, found {len(diags)}")
    for f in SECTION_DIRS.values(): f.mkdir(parents=True, exist_ok=True)
    (ROOT/"shared").mkdir(exist_ok=True)
    created = []
    nav_catalog = build_nav_catalog(diags)
    for d in diags:
        steps = build_steps(d["mermaid"])
        out = SECTION_DIRS[d["section_letter"]] / f"{d['slug']}.html"
        nav_html = render_nav(d["section_letter"], d["slug"], nav_catalog)
        html_out = (
            PRES.replace("__TITLE__", html.escape(d["title"]))
            .replace("__SECTION_TITLE__", html.escape(d["section_title"]))
            .replace("__CAPTION__", html.escape(d["caption"]))
            .replace("__NAV_HTML__", nav_html)
            .replace("__STEPS_JSON__", json.dumps(steps, ensure_ascii=False))
        )
        out.write_text(html_out, encoding="utf-8")
        created.append(str(out.relative_to(ROOT)))
    render_index(diags); created.append("index.html")
    print(f"Generated {len(diags)} presentations + index.html")
    for p in created: print(" ", p)

if __name__ == "__main__":
    main()