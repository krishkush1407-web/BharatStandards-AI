
import io, json, re
from pathlib import Path
from datetime import datetime
import streamlit as st

BASE=Path(__file__).parent
STANDARDS=json.loads((BASE/"data"/"standards.json").read_text(encoding="utf-8"))

st.set_page_config(page_title="BharatStandards AI", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp{background:#f6f8fc;color:#15213b}.block-container{max-width:1400px;padding-top:.6rem}
.top{background:#0b1225;color:#fff;padding:12px 24px;border-radius:16px 16px 0 0}
.brand{font-size:21px;font-weight:850}.brand small{display:block;color:#aeb8cc;font-size:11px;font-weight:500}
.ps{background:#f6a400;color:#111827;border-radius:7px;padding:4px 9px;font-size:11px;font-weight:800}
.hero{background:linear-gradient(115deg,#0b1225,#111a31 65%,#202128);color:#fff;padding:42px 38px;border-radius:0 0 18px 18px;box-shadow:0 12px 28px #0b122525}
.badge{display:inline-block;border:1px solid #f6a40080;background:#f6a40018;color:#ffc34f;border-radius:20px;padding:8px 14px;font-size:12px;font-weight:800}
.hero h1{font-size:43px;line-height:1.08;letter-spacing:-1.5px;margin:20px 0 12px;max-width:900px}
.hero p{color:#c8d0df;font-size:16px;max-width:820px}
.card,.result{background:#fff;border:1px solid #dbe2ee;border-radius:14px;padding:18px;box-shadow:0 3px 12px #1e325a08}
.result{margin:10px 0}.score{font-size:29px;font-weight:900;color:#2144b5}
.small{font-size:12px;color:#64748b}.pill{display:inline-block;border:1px solid #d8dfeb;background:#f8fafc;border-radius:18px;padding:5px 9px;margin:3px;font-size:12px}
.metric{background:#2144b5;color:white;padding:18px}.metric b{font-size:24px}.metric span{display:block;font-size:11px;opacity:.85}
.node{background:#f8fafc;border:1px solid #dbe3ef;border-radius:10px;padding:12px;text-align:center}
div.stButton>button{border-radius:9px;font-weight:700}
</style>
""",unsafe_allow_html=True)

def norm(s):
    s=(s or "").lower()
    for a,b in {"एलईडी":"led","सड़क लाइट":"street light","सोलर":"solar","केबल":"cable","पानी":"water","मीटर":"meter","बैटरी":"battery","यूपीएस":"ups","पाइप":"pipe","स्टील":"steel"}.items(): s=s.replace(a,b)
    aliases={"street light":["streetlight","road light","lamp","luminaire","outdoor lighting"],
             "solar":["pv","photovoltaic","solar panel","module","mono perc"],
             "cable":["wire","xlpe","armoured","underground","power cable","ht"],
             "meter":["smart meter","electricity meter","energy meter"],
             "ups":["uninterruptible","online ups","backup power","double conversion"],
             "battery":["vrla","lead acid"],"water":["potable","drinking","water supply"],
             "pipe":["tube","plumbing"],"steel":["tmt","rebar","reinforcement"],
             "earthing":["grounding","earth pit","ground"]}
    for k,vs in aliases.items():
        if any(v in s for v in vs): s+=" "+k
    return re.sub(r"[^a-z0-9.+/#\-\s]"," ",s)

def toks(s): return set(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?",norm(s)))

def rank(query,s):
    q=toks(query)
    text=" ".join([s["id"],s["title"],s["category"],*s["keywords"],*s["aliases"],*s["requirements"]])
    overlap=q&toks(text)
    score=min(96,20+len(overlap)*10)
    nq=norm(query); joined=norm(text)
    for phrase in ["ip66","33kv","33 kv","540wp","mono perc","smart meter","vrla","double conversion","xlpe","water supply","fe500","fe550"]:
        if phrase in nq and phrase in joined: score=min(99,score+8)
    return score,sorted(overlap,key=lambda x:(-len(x),x))[:8]

def recommend(q,n=8):
    out=[]
    for s in STANDARDS:
        sc,r=rank(q,s)
        if sc>=30: out.append((sc,r,s))
    return sorted(out,key=lambda x:x[0],reverse=True)[:n]

def extract(file):
    if not file:return ""
    data=file.getvalue(); name=file.name.lower()
    if name.endswith(".txt"): return data.decode("utf-8","ignore")
    if name.endswith(".docx"):
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
        except Exception as e:return "DOCX extraction error: "+str(e)
    if name.endswith(".pdf"):
        try:
            import fitz
            doc=fitz.open(stream=data,filetype="pdf")
            return "\n".join(p.get_text() for p in doc)
        except Exception as e:return "PDF extraction error: "+str(e)
    return ""

def gaps(text,recs):
    q=norm(text)
    checks=[
    ("Product/service identity",any(x in q for x in ["product","system","equipment","supply","procure","tender","lamp","cable","meter","water","pipe","solar","ups"])),
    ("Technical parameters",any(x in q for x in ["watt","kw","kva","voltage","amp","ip66","ip65","grade","capacity","accuracy","class","wp","kv"])),
    ("Applicable Indian Standard",("is " in q or "is/" in q or "bis" in q)),
    ("Testing / inspection",any(x in q for x in ["test","inspection","acceptance","routine","type test"])),
    ("Marking / documentation",any(x in q for x in ["marking","label","certificate","documentation","manual"])),
    ("Warranty / support",any(x in q for x in ["warranty","guarantee","service","support"])),
    ("Compliance / certification",any(x in q for x in ["bis","certification","qco","conformity","registration"]))]
    cov=round(100*sum(v for _,v in checks)/len(checks))
    cov=min(100,cov+min(20,len(recs)*2))
    return checks,cov

def report(q,recs,g,cov):
    out=["# BharatStandards AI — Tender Analysis",f"Generated: {datetime.now():%d-%m-%Y %H:%M}","",f"## Input\n{q}",f"\n## Prototype coverage: {cov}%",""]
    out += [f"- [{'x' if ok else ' '}] {name}" for name,ok in g]
    out += ["","\n## Recommendations"]
    for sc,r,s in recs:
        out += [f"\n### {s['id']} — {s['title']}",f"Relevance: {sc}%",f"Matched signals: {', '.join(r)}",
                f"Requirements: {'; '.join(s['requirements'])}",f"Certification: {'; '.join(s['certification'])}",f"Related: {', '.join(s['related'])}"]
    out += ["","\n## Verification","Prototype local index only. Verify current BIS standard, amendment, QCO and certification route against authoritative sources before procurement."]
    return "\n".join(out)

if "page" not in st.session_state: st.session_state.page="Home / Dashboard"
if "query" not in st.session_state: st.session_state.query=""
if "history" not in st.session_state: st.session_state.history=[]
if "results" not in st.session_state: st.session_state.results=[]

st.markdown("""<div class="top"><div style="display:flex;align-items:center;justify-content:space-between">
<div style="display:flex;gap:14px;align-items:center"><div style="font-size:29px">🛡️</div>
<div class="brand">BharatStandards AI<small>National BIS Procurement & Tender Audit System</small></div><span class="ps">SIH26108</span></div>
<div style="color:#aeb8cc;font-size:12px">Prototype • Local Intelligence Index • Demo</div></div></div>""",unsafe_allow_html=True)

pages=["Home / Dashboard","Search & Recommendations","Gap Detector & Score","Standard Details","Relevance Graph","Tender Spec Editor"]
nav=st.columns(len(pages))
for i,p in enumerate(pages):
    if nav[i].button(p,key=f"nav{i}",use_container_width=True):
        st.session_state.page=p;st.rerun()

def go(q):
    st.session_state.query=q
    st.session_state.results=recommend(q)
    if q.strip() and q not in st.session_state.history:
        st.session_state.history.insert(0,q);st.session_state.history=st.session_state.history[:8]

if st.session_state.page=="Home / Dashboard":
    st.markdown("""<div class="hero"><span class="badge">✦ AI-POWERED INDIAN STANDARDS AUDIT ENGINE</span>
<h1>Find the right Indian Standards for your tender</h1>
<p>AI-powered recommendations for procurement specifications with explainable matching, compliance gap detection, standard relationships and tender drafting.</p></div>""",unsafe_allow_html=True)
    a,b=st.columns([5,1.6])
    with a:q=st.text_input("requirement",value=st.session_state.query,placeholder="Enter product/specification e.g. 100W LED street light, IP66, surge protection",label_visibility="collapsed")
    with b:
        if st.button("🔎 Search Standards",type="primary",use_container_width=True):
            go(q);st.session_state.page="Search & Recommendations";st.rerun()
    st.caption("Or upload an existing procurement RFP/tender document:")
    f=st.file_uploader("Tender PDF / DOCX / TXT",type=["pdf","docx","txt"],label_visibility="collapsed")
    if f:
        text=extract(f);st.session_state.query=text;st.session_state.results=recommend(text)
        st.success(f"Extracted {len(text.split())} words from {f.name}.")
        if st.button("Open extracted analysis →"):st.session_state.page="Search & Recommendations";st.rerun()
    st.markdown("### System Index")
    cols=st.columns(4)
    for c,v,l in zip(cols,["21","6","7","0 API keys"],["Demo standards indexed","Working modules","Gap checks","External AI dependency"]):
        c.markdown(f'<div class="metric"><b>{v}</b><span>{l}</span></div>',unsafe_allow_html=True)
    st.markdown("### Recent Searches")
    if st.session_state.history:
        for h in st.session_state.history:
            if st.button("⌕  "+h[:100],key="h"+str(hash(h))):
                go(h);st.session_state.page="Search & Recommendations";st.rerun()
    else:
        st.info("Try a live demo query:")
        for d in ["100W LED street light, IP66, surge protection","33kV HT XLPE underground armoured cable","540Wp Mono PERC solar PV module","Single Phase Smart Electricity Meter IS 16444","10 kVA double conversion UPS with VRLA battery"]:
            if st.button("⌕  "+d):go(d);st.session_state.page="Search & Recommendations";st.rerun()

elif st.session_state.page=="Search & Recommendations":
    st.title("Search & Recommendations")
    q=st.text_area("Tender / product requirement",value=st.session_state.query,height=130)
    c1,c2=st.columns([1,5])
    if c1.button("Run AI Scan",type="primary",use_container_width=True):go(q);st.rerun()
    recs=recommend(q,10) if q.strip() else []
    st.session_state.results=recs
    st.caption(f"{len(recs)} results • explainable local retrieval")
    for sc,r,s in recs:
        st.markdown(f"""<div class="result"><div style="display:flex;justify-content:space-between">
<div><h3 style="margin:0">{s['id']}</h3><div>{s['title']}</div><div class="small">{s['category']} • {s['status']}</div></div>
<div style="text-align:right"><div class="score">{sc}%</div><div class="small">relevance</div></div></div>
<div style="margin-top:10px"><b>Matched signals:</b> {''.join('<span class="pill">'+x+'</span>' for x in r)}</div></div>""",unsafe_allow_html=True)
        if st.button("View details →",key="d"+s["id"]):
            st.session_state.selected=s;st.session_state.page="Standard Details";st.rerun()
    if not recs:st.warning("Enter a product/specification to scan.")

elif st.session_state.page=="Gap Detector & Score":
    st.title("Gap Detector & Compliance Score")
    q=st.text_area("Paste tender specification",value=st.session_state.query,height=180)
    if st.button("Run Gap Detector",type="primary"):
        recs=recommend(q);st.session_state.gap=gaps(q,recs);st.session_state.gap_recs=recs
    if "gap" in st.session_state:
        rows,cov=st.session_state.gap
        x,y=st.columns([1,2]);x.metric("Prototype Coverage Score",f"{cov}%");x.progress(cov/100);x.caption("Heuristic demo score; not official certification.")
        for name,ok in rows:y.markdown(f"**{'✅' if ok else '⚠️'} {name}** — {'Present' if ok else 'Missing / review'}")
        st.subheader("Recommended standards")
        for sc,_,s in st.session_state.gap_recs[:6]:st.write(f"**{s['id']}** — {s['title']} ({sc}%)")

elif st.session_state.page=="Standard Details":
    st.title("Standard Details")
    opts=[s["id"]+" — "+s["title"] for s in STANDARDS]
    default=st.session_state.get("selected",STANDARDS[0])
    ix=next((i for i,x in enumerate(opts) if x.startswith(default["id"])),0)
    pick=st.selectbox("Select standard",opts,index=ix);s=STANDARDS[opts.index(pick)]
    st.session_state.selected=s
    st.markdown(f"### {s['id']}\n{s['title']}")
    a,b,c=st.columns(3);a.metric("Category",s["category"]);b.metric("Status","Verify latest");c.metric("Related",len(s["related"]))
    st.subheader("Requirements")
    for x in s["requirements"]:st.write("• "+x)
    st.subheader("Certification / regulatory signal")
    for x in s["certification"]:st.info(x)
    st.subheader("Related standards")
    for x in s["related"]:st.write("🔗 "+x)
    st.warning("Prototype index record. Verify current BIS catalogue/version before procurement.")

elif st.session_state.page=="Relevance Graph":
    st.title("Relevance Graph")
    q=st.text_input("Graph seed",value=st.session_state.query or "LED street light")
    recs=recommend(q,6)
    st.markdown(f'<div class="node"><b>USER REQUIREMENT</b><br>{q[:140]}</div>',unsafe_allow_html=True)
    st.write("↓")
    for sc,_,s in recs:
        st.markdown(f'<div class="card"><b>{s["id"]}</b> — {s["title"]}<br><span class="small">Relevance {sc}% • {s["category"]}</span><br><br><b>Related:</b> {" • ".join(s["related"])}</div>',unsafe_allow_html=True)

elif st.session_state.page=="Tender Spec Editor":
    st.title("Tender Specification Editor")
    q=st.text_area("Base requirement",value=st.session_state.query or "Supply and installation of 100W LED street lights for outdoor road lighting.",height=120)
    recs=recommend(q,6)
    ids=st.multiselect("Standards to include",[x[2]["id"] for x in recs],default=[x[2]["id"] for x in recs[:3]])
    lines=["TECHNICAL SPECIFICATION","",f"Scope: {q.strip()}","","Applicable Indian Standards:"]
    for _,_,s in recs:
        if s["id"] in ids:lines.append(f"- {s['id']} — {s['title']}")
    lines += ["","Minimum requirements:"]
    for _,_,s in recs:
        if s["id"] in ids:
            lines += [f"- {x}" for x in s["requirements"]]
    lines += ["","Compliance / documentation:","- Bidder shall provide applicable test reports and conformity evidence.","- Procuring entity shall verify the latest BIS standard, amendments and QCOs before issue."]
    draft="\n".join(lines)
    edited=st.text_area("Editable specification",value=draft,height=430)
    st.download_button("⬇ Download Specification",edited,file_name="tender_specification.txt")
    rr=recommend(q);gg,cov=gaps(edited,rr);rep=report(q,rr,gg,cov)
    st.download_button("⬇ Download Full Analysis Report",rep,file_name="bharatstandards_analysis.md")

st.divider()
st.caption("BharatStandards AI • SIH26108 prototype • Demo index only. Verify current BIS standards, amendments, QCOs and certification routes from authoritative sources before procurement.")
