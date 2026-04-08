"""
╔══════════════════════════════════════════════════════════════════╗
║          PyStreamlit Converter Pro — Advanced Edition            ║
║     Python / Jupyter → Streamlit App Converter & Analyzer       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import nbformat
import ast
import re
import zipfile
import io
import hashlib
import time
import textwrap
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Set
from datetime import datetime
from collections import Counter
import difflib

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PyStreamlit Converter Pro",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "PyStreamlit Converter Pro — Transform Python & Jupyter code into Streamlit apps.",
    },
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
_DEFAULTS: Dict[str, Any] = {
    "conversion_results": {},
    "uploaded_files": [],
    "uploaded_zip": None,
    "theme": "dark",
    "conversion_mode": "Hybrid (Recommended)",
    "chart_library": "Auto-Detect",
    "app_layout": "wide",
    "sidebar_mode": "Auto (controls)",
    "add_caching": True,
    "add_error_handling": True,
    "add_download_button": True,
    "add_sidebar_controls": True,
    "add_session_state": False,
    "add_main_guard": False,
    "preserve_comments": True,
    "large_file_threshold": 200,
    "conversion_history": [],
    "stats": {
        "total_files": 0,
        "successful": 0,
        "failed": 0,
        "total_transformations": 0,
        "session_start": datetime.now().isoformat(),
    },
}

for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# THEME & STYLING
# ─────────────────────────────────────────────
def inject_css() -> None:
    dark = st.session_state.theme == "dark"
    bg0   = "#0a0c10" if dark else "#ffffff"
    bg1   = "#12151c" if dark else "#f7f8fa"
    bg2   = "#1a1e28" if dark else "#eef0f4"
    border= "#2a2e3d" if dark else "#dde1ea"
    txt0  = "#e8ecf4" if dark else "#12151c"
    txt1  = "#8892a4" if dark else "#505870"
    acc   = "#4f8ef7"
    acc2  = "#a78bfa"
    suc   = "#34d399"
    warn  = "#fbbf24"
    err   = "#f87171"

    st.markdown(f"""
<style>
.stApp {{ background: {bg0}; color: {txt0}; font-family: 'Inter', sans-serif; }}
[data-testid="stSidebar"] {{ background: {bg1} !important; border-right: 1px solid {border}; }}
h1,h2,h3,h4,h5,h6 {{ color: {txt0} !important; font-weight: 700; }}

.pc-card {{
    background: {bg1};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 20px 24px;
    margin: 10px 0;
    transition: box-shadow .2s;
}}
.pc-card:hover {{ box-shadow: 0 0 0 1px {acc}44; }}

.pc-metric {{
    background: {bg2};
    border-radius: 10px;
    padding: 16px 20px;
    border: 1px solid {border};
    text-align: center;
}}
.pc-metric .val {{ font-size: 2em; font-weight: 800; color: {acc}; line-height: 1.1; }}
.pc-metric .lbl {{ font-size: 0.78em; color: {txt1}; text-transform: uppercase; letter-spacing: .06em; margin-top: 4px; }}

.pc-hero {{
    background: linear-gradient(135deg, {acc}18 0%, {acc2}12 100%);
    border: 1px solid {acc}33;
    border-radius: 16px;
    padding: 36px 40px;
    text-align: center;
    margin: 8px 0 24px;
    position: relative;
    overflow: hidden;
}}
.pc-hero::before {{
    content: "";
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at top left, {acc}10, transparent 60%);
    pointer-events: none;
}}
.pc-hero h1 {{ font-size: 2.4em; margin: 0 0 10px; background: linear-gradient(90deg,{acc},{acc2}); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.pc-hero p  {{ color: {txt1}; font-size: 1.05em; margin: 0 0 18px; }}

.pc-badge {{
    display: inline-block;
    padding: 3px 11px; border-radius: 20px;
    font-size: .78em; font-weight: 600;
    background: {acc}1a; color: {acc};
    border: 1px solid {acc}44;
    margin: 2px;
}}
.pc-badge-green  {{ background: {suc}1a; color: {suc}; border-color: {suc}44; }}
.pc-badge-amber  {{ background: {warn}1a; color: {warn}; border-color: {warn}44; }}
.pc-badge-red    {{ background: {err}1a; color: {err}; border-color: {err}44; }}
.pc-badge-purple {{ background: {acc2}1a; color: {acc2}; border-color: {acc2}44; }}

.diff-add  {{ background: {suc}22; color: {suc}; border-left: 3px solid {suc}; padding: 1px 8px; display:block; }}
.diff-rem  {{ background: {err}22; color: {err}; border-left: 3px solid {err}; padding: 1px 8px; display:block; }}
.diff-same {{ color: {txt1}; padding: 1px 8px; display:block; }}
.diff-wrap {{ background: {bg2}; border: 1px solid {border}; border-radius: 8px; padding: 8px; font-family: monospace; font-size: .82em; max-height: 460px; overflow-y: auto; }}

.rep-item {{ display: flex; align-items: flex-start; gap: 8px; padding: 5px 0; font-size: .88em; }}
.rep-ok   {{ color: {suc}; }}
.rep-warn {{ color: {warn}; }}
.rep-err  {{ color: {err}; }}
.rep-info {{ color: {acc}; }}

.sidebar-logo {{ text-align:center; padding: 16px 0 8px; }}
.sidebar-logo .logo-icon {{ font-size: 2.8em; line-height: 1; }}
.sidebar-logo .logo-title {{ font-size: 1.1em; font-weight: 800; color: {acc}; margin-top: 4px; }}
.sidebar-logo .logo-sub {{ font-size: .7em; color: {txt1}; letter-spacing: .08em; }}

.stProgress > div > div > div {{ background: linear-gradient(90deg, {acc}, {acc2}) !important; }}
.stButton > button {{ border-radius: 8px !important; font-weight: 600 !important; transition: all .2s !important; }}
.stButton > button:hover {{ transform: translateY(-1px) !important; box-shadow: 0 4px 14px {acc}33 !important; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 8px 8px 0 0 !important; padding: 10px 20px !important; font-weight: 600 !important; }}
.stCodeBlock {{ border-radius: 10px !important; border: 1px solid {border} !important; }}
[data-testid="stMetricValue"] {{ color: {acc} !important; font-weight: 700 !important; }}
.streamlit-expanderHeader {{ background: {bg2} !important; border-radius: 8px !important; font-weight: 600 !important; }}

.timeline-item {{
    border-left: 2px solid {border};
    padding: 6px 0 6px 16px;
    margin-left: 8px;
    position: relative;
}}
.timeline-item::before {{
    content: "";
    width: 8px; height: 8px;
    background: {acc};
    border-radius: 50%;
    position: absolute; left: -5px; top: 10px;
}}
.timeline-item.ok::before  {{ background: {suc}; }}
.timeline-item.err::before {{ background: {err}; }}

.health-bar-bg {{ background: {bg2}; border-radius: 4px; height: 6px; margin-top: 4px; }}
.health-bar-fg {{ height: 6px; border-radius: 4px; background: linear-gradient(90deg,{acc},{acc2}); }}
</style>
""", unsafe_allow_html=True)


inject_css()


# ═══════════════════════════════════════════════════════════════════
# CONVERTER CORE
# ═══════════════════════════════════════════════════════════════════

class CodeAnalyzer:
    """
    Static analysis of Python source code — extracts imports, functions,
    classes, chart/ML/data libraries, transformable calls, and complexity metrics.
    """

    def __init__(self, source: str):
        self.source = source
        self.tree: Optional[ast.Module] = None
        try:
            self.tree = ast.parse(source)
        except SyntaxError:
            pass

    def get_imports(self) -> List[str]:
        if not self.tree:
            return []
        out = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    out.append(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                out.append(node.module)
        return out

    def get_functions(self) -> List[Dict]:
        if not self.tree:
            return []
        fns = []
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node) or ""
                fns.append({
                    "name": node.name,
                    "args": [a.arg for a in node.args.args],
                    "lineno": node.lineno,
                    "doc": (doc[:80] + "…") if len(doc) > 80 else doc,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "body_lines": (node.end_lineno - node.lineno + 1) if hasattr(node, "end_lineno") else 0,
                })
        return fns

    def get_classes(self) -> List[Dict]:
        if not self.tree:
            return []
        out = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                bases = []
                for b in node.bases:
                    try:
                        bases.append(ast.unparse(b))
                    except Exception:
                        bases.append("?")
                out.append({"name": node.name, "lineno": node.lineno, "methods": methods, "bases": bases})
        return out

    def detect_chart_libraries(self) -> List[str]:
        s = self.source
        libs = []
        if "matplotlib" in s or "plt." in s:         libs.append("matplotlib")
        if "seaborn" in s or "sns." in s:            libs.append("seaborn")
        if "plotly" in s or "px." in s or "go." in s:libs.append("plotly")
        if "altair" in s or "alt." in s:             libs.append("altair")
        if "bokeh" in s:                             libs.append("bokeh")
        if "folium" in s:                            libs.append("folium")
        return libs

    def detect_ml_libraries(self) -> List[str]:
        s = self.source
        libs = []
        if "sklearn" in s or "scikit" in s:  libs.append("scikit-learn")
        if "tensorflow" in s or "tf." in s:  libs.append("tensorflow")
        if "torch" in s:                     libs.append("pytorch")
        if "xgboost" in s or "xgb." in s:   libs.append("xgboost")
        if "lightgbm" in s or "lgbm" in s:  libs.append("lightgbm")
        if "catboost" in s:                  libs.append("catboost")
        if "transformers" in s:              libs.append("transformers")
        return libs

    def detect_data_libraries(self) -> List[str]:
        s = self.source
        libs = []
        if "pandas" in s or " pd." in s:  libs.append("pandas")
        if "numpy" in s or " np." in s:   libs.append("numpy")
        if "scipy" in s:                  libs.append("scipy")
        if "polars" in s:                 libs.append("polars")
        if "dask" in s:                   libs.append("dask")
        return libs

    def count_transformable_calls(self) -> Dict[str, int]:
        counts: Counter = Counter()
        for line in self.source.splitlines():
            s = line.strip()
            if re.match(r"print\s*\(", s):                          counts["print"] += 1
            if re.match(r"display\s*\(", s):                        counts["display"] += 1
            if re.match(r"plt\.show\s*\(", s):                      counts["plt.show"] += 1
            if re.match(r"[a-zA-Z_]\w*\.show\s*\(", s):             counts["fig.show"] += 1
            if re.match(r"[a-zA-Z_]\w*\.(?:head|tail)\s*\(", s):    counts["df.head/tail"] += 1
        return dict(counts)

    def compute_complexity(self) -> Dict[str, Any]:
        lines = self.source.splitlines()
        code_lines    = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        comment_lines = [l for l in lines if l.strip().startswith("#")]
        branch_kws = {"if", "elif", "for", "while", "try", "except", "with"}
        branches = sum(1 for l in lines for kw in branch_kws if re.search(rf"\b{kw}\b", l))
        return {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len(comment_lines),
            "blank_lines": len(lines) - len(code_lines) - len(comment_lines),
            "cyclomatic": branches,
            "functions": len(self.get_functions()),
            "classes": len(self.get_classes()),
        }

    def suggest_widgets(self) -> List[Dict]:
        """Suggest Streamlit widgets for hard-coded literals."""
        if not self.tree:
            return []
        out = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    try:
                        name = ast.unparse(target)
                    except Exception:
                        continue
                    val = node.value.value
                    if isinstance(val, bool):
                        out.append({"name": name, "widget": "st.checkbox",          "default": val, "lineno": node.lineno})
                    elif isinstance(val, int) and 0 < val <= 1000:
                        out.append({"name": name, "widget": "st.slider",            "default": val, "lineno": node.lineno})
                    elif isinstance(val, float) and 0.0 < val <= 1.0:
                        out.append({"name": name, "widget": "st.slider (float)",    "default": val, "lineno": node.lineno})
                    elif isinstance(val, str) and len(val) < 80 and "\n" not in val:
                        out.append({"name": name, "widget": "st.text_input",        "default": repr(val), "lineno": node.lineno})
        return out[:15]


# ─────────────────────────────────────────────────────────────────
# AST Transformer
# ─────────────────────────────────────────────────────────────────

class EnhancedTransformer(ast.NodeTransformer):
    """AST transformer: print→st.write, display→st.dataframe,
    plt.show→st.pyplot, fig.show→st.plotly_chart, df.head/tail→st.dataframe,
    plus optional @st.cache_data injection on loader functions."""

    def __init__(self, source_lines: List[str], chart_library: str = "auto",
                 add_caching: bool = True):
        self.source_lines = source_lines
        self.chart_library = chart_library.lower()
        self.add_caching = add_caching
        self.conversion_log: List[str] = []
        self.imports_needed: Set[str] = {"import streamlit as st"}

    def _st(self, attr: str) -> ast.Attribute:
        return ast.Attribute(value=ast.Name(id="st", ctx=ast.Load()), attr=attr, ctx=ast.Load())

    def _call(self, func, args=None, kw=None) -> ast.Call:
        return ast.Call(func=func, args=args or [], keywords=kw or [])

    def _expr(self, val) -> ast.Expr:
        return ast.Expr(value=val)

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if self.add_caching:
            n = node.name.lower()
            if any(kw in n for kw in ("load", "fetch", "read", "get_data", "query")):
                node.decorator_list.insert(
                    0, ast.Attribute(value=ast.Name(id="st", ctx=ast.Load()),
                                     attr="cache_data", ctx=ast.Load()))
                self.conversion_log.append(f"✅ Added @st.cache_data to {node.name}()")
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Expr(self, node):
        self.generic_visit(node)
        if not isinstance(node.value, ast.Call):
            return node
        call = node.value

        # print → st.write
        if isinstance(call.func, ast.Name) and call.func.id == "print":
            call.func = self._st("write")
            self.conversion_log.append("✅ print() → st.write()")
            return node

        # display → st.dataframe or st.write
        if isinstance(call.func, ast.Name) and call.func.id == "display":
            fn = "dataframe" if (call.args and isinstance(call.args[0], ast.Name)) else "write"
            call.func = self._st(fn)
            self.conversion_log.append(f"✅ display() → st.{fn}()")
            return node

        # plt.show() → st.pyplot(plt.gcf())
        if (isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "plt"
                and call.func.attr == "show"):
            self.imports_needed.add("import matplotlib.pyplot as plt")
            new = self._call(self._st("pyplot"), args=[
                self._call(ast.Attribute(value=ast.Name(id="plt", ctx=ast.Load()), attr="gcf", ctx=ast.Load()))
            ])
            self.conversion_log.append("✅ plt.show() → st.pyplot(plt.gcf())")
            return self._expr(new)

        # <var>.show() → st.plotly_chart / st.altair_chart
        if isinstance(call.func, ast.Attribute) and call.func.attr == "show":
            if isinstance(call.func.value, ast.Name):
                var = call.func.value.id
                fn = "altair_chart" if self.chart_library == "altair" else "plotly_chart"
                new = self._call(self._st(fn), args=[ast.Name(id=var, ctx=ast.Load())])
                self.conversion_log.append(f"✅ {var}.show() → st.{fn}()")
                return self._expr(new)

        # bokeh show(fig)
        if isinstance(call.func, ast.Name) and call.func.id == "show" and call.args:
            new = self._call(self._st("bokeh_chart"), args=call.args)
            self.conversion_log.append("✅ bokeh show() → st.bokeh_chart()")
            return self._expr(new)

        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ("head", "tail", "describe"):
                if getattr(node, "_parent", None) is None:
                    wrapped = self._call(self._st("dataframe"), args=[node])
                    self.conversion_log.append(f"✅ .{node.func.attr}() → st.dataframe()")
                    return wrapped
        return node


# ─────────────────────────────────────────────────────────────────
# Hybrid Converter
# ─────────────────────────────────────────────────────────────────

class HybridConverter:
    """
    Three-pass conversion engine:
      Pass 1 — AST transformation (structure-aware)
      Pass 2 — Regex post-processing (magic cmds, misc patterns)
      Pass 3 — Boilerplate injection (imports, page config, sidebar, error wrapping)
    """

    def __init__(self, source: str, filename: str = "script", *,
                 conversion_mode: str = "hybrid",
                 chart_library: str = "auto",
                 app_layout: str = "wide",
                 sidebar_mode: str = "auto",
                 add_caching: bool = True,
                 add_error_handling: bool = True,
                 add_download_button: bool = True,
                 add_sidebar_controls: bool = True,
                 add_session_state: bool = False,
                 add_main_guard: bool = False,
                 preserve_comments: bool = True,
                 large_file_threshold: int = 200):
        self.source = source
        self.filename = filename
        self.mode = conversion_mode.lower()
        self.chart_library = chart_library.lower()
        self.app_layout = app_layout
        self.add_caching = add_caching
        self.add_error_handling = add_error_handling
        self.add_download_button = add_download_button
        self.add_sidebar_controls = add_sidebar_controls
        self.add_session_state = add_session_state
        self.add_main_guard = add_main_guard
        self.preserve_comments = preserve_comments
        self.large_file_threshold = large_file_threshold * 1024
        self.report: List[str] = []
        self.imports_needed: Set[str] = set()
        self.analyzer = CodeAnalyzer(source)

    def convert(self) -> str:
        self.report.append(f"ℹ️  Source   : {self.filename}")
        self.report.append(f"ℹ️  Mode     : {self.mode}")
        self.report.append(f"ℹ️  Size     : {len(self.source.encode())/1024:.1f} KB")

        if "regex" in self.mode:
            return self._regex_pass(self.source)
        elif "ast" in self.mode:
            return self._ast_pass()
        else:
            return self._hybrid_pass()

    def get_report(self) -> List[str]:
        return self.report

    # ── Passes ─────────────────────────────────────────────────

    def _hybrid_pass(self) -> str:
        try:
            code = self._ast_core()
        except Exception as exc:
            self.report.append(f"⚠️  AST failed ({exc}), falling back to regex")
            return self._regex_pass(self.source)
        code = self._regex_cleanup(code)
        return self._assemble(code)

    def _ast_pass(self) -> str:
        try:
            return self._assemble(self._ast_core())
        except Exception as exc:
            self.report.append(f"⚠️  AST failed ({exc}), falling back to regex")
            return self._regex_pass(self.source)

    def _ast_core(self) -> str:
        tree = ast.parse(self.source, filename=self.filename)
        tx = EnhancedTransformer(
            self.source.splitlines(keepends=True),
            chart_library=self.chart_library,
            add_caching=self.add_caching,
        )
        new_tree = tx.visit(tree)
        ast.fix_missing_locations(new_tree)
        self.imports_needed.update(tx.imports_needed)
        self.report.extend(tx.conversion_log)

        if hasattr(ast, "unparse"):
            return ast.unparse(new_tree)
        try:
            import astor
            return astor.to_source(new_tree)
        except ImportError:
            self.report.append("⚠️  Python < 3.9 & no astor; using regex")
            return self._regex_pass(self.source)

    def _regex_cleanup(self, code: str) -> str:
        """Light regex pass after AST to catch remaining patterns."""
        out = []
        for line in code.splitlines(keepends=True):
            s = line.strip()
            if s.startswith("%") or s.startswith("!"):
                self.report.append(f"✅ Removed magic/shell: {s[:40]}")
                continue
            out.append(line)
        return "".join(out)

    def _regex_pass(self, code: str) -> str:
        """Full line-by-line regex transformation."""
        lines = code.splitlines(keepends=True)
        out = []
        in_mls = False

        for line in lines:
            s = line.strip()
            ind = len(line) - len(line.lstrip())
            sp = " " * ind

            if s.startswith("%") or s.startswith("!"):
                self.report.append(f"✅ Removed magic/shell: {s[:40]}")
                continue

            if '"""' in line or "'''" in line:
                tq = '"""' if '"""' in line else "'''"
                if line.count(tq) % 2 == 1:
                    in_mls = not in_mls
                out.append(line); continue

            if in_mls:
                out.append(line); continue

            if re.match(r"^\s*print\s*\(", s):
                out.append(re.sub(r"\bprint\s*\(", "st.write(", line, count=1))
                self.report.append("✅ print() → st.write()")
                self.imports_needed.add("import streamlit as st")
                continue

            if re.match(r"^\s*display\s*\(", s):
                out.append(re.sub(r"\bdisplay\s*\(", "st.dataframe(", line, count=1))
                self.report.append("✅ display() → st.dataframe()")
                self.imports_needed.add("import streamlit as st")
                continue

            if re.match(r"^\s*plt\.show\s*\(\s*\)", s):
                out.append(f"{sp}st.pyplot(plt.gcf())\n")
                self.report.append("✅ plt.show() → st.pyplot(plt.gcf())")
                self.imports_needed.add("import streamlit as st")
                continue

            m = re.match(r"^\s*([a-zA-Z_]\w*)\.show\s*\(\s*\)\s*$", s)
            if m and m.group(1) != "plt":
                var = m.group(1)
                out.append(f"{sp}st.plotly_chart({var})\n")
                self.report.append(f"✅ {var}.show() → st.plotly_chart({var})")
                self.imports_needed.add("import streamlit as st")
                continue

            m2 = re.match(r"^\s*([a-zA-Z_]\w*\.(?:head|tail|describe)\s*\([^)]*\))\s*$", s)
            if m2:
                out.append(f"{sp}st.dataframe({m2.group(1)})\n")
                self.report.append("✅ DataFrame view → st.dataframe()")
                self.imports_needed.add("import streamlit as st")
                continue

            out.append(line)

        result = "".join(out)
        self._detect_imports(self.source)
        return self._assemble(result)

    # ── Import Detection ───────────────────────────────────────

    def _detect_imports(self, code: str) -> None:
        self.imports_needed.add("import streamlit as st")
        checks = [
            (r"\bplt\.",         "import matplotlib.pyplot as plt"),
            ("matplotlib",       "import matplotlib.pyplot as plt"),
            (r"\bsns\.",         "import seaborn as sns"),
            ("seaborn",          "import seaborn as sns"),
            (r"\bpx\.",          "import plotly.express as px"),
            (r"\bgo\.",          "import plotly.graph_objects as go"),
            ("plotly",           "import plotly.express as px"),
            (r"\bpd\.",          "import pandas as pd"),
            ("pandas",           "import pandas as pd"),
            (r"\bnp\.",          "import numpy as np"),
            ("numpy",            "import numpy as np"),
            (r"\balt\.",         "import altair as alt"),
            ("altair",           "import altair as alt"),
        ]
        for pattern, imp in checks:
            if re.search(pattern, code):
                self.imports_needed.add(imp)

    # ── Sidebar Widgets ────────────────────────────────────────

    def _build_sidebar(self) -> str:
        suggestions = self.analyzer.suggest_widgets()
        if not suggestions or not self.add_sidebar_controls:
            return ""
        lines = [
            "\n# ── Auto-generated Sidebar Controls ──────────────────",
            "with st.sidebar:",
            '    st.markdown("### ⚙️ Parameters")',
        ]
        for s in suggestions[:8]:
            name = s["name"]
            w = s["widget"]
            d = s["default"]
            label = repr(name.replace("_", " ").title())
            if "checkbox" in w:
                lines.append(f"    {name} = st.checkbox({label}, value={d})")
            elif "float" in w:
                lines.append(f"    {name} = st.slider({label}, 0.0, 1.0, float({d}))")
            elif "slider" in w:
                mx = max(int(d) * 10, 100)
                lines.append(f"    {name} = st.slider({label}, 0, {mx}, {d})")
            else:
                lines.append(f"    {name} = st.text_input({label}, value={d})")
        return "\n".join(lines)

    # ── Assembly ─────────────────────────────────────────────

    def _assemble(self, body: str) -> str:
        self._detect_imports(self.source)

        stem = Path(self.filename).stem.replace("_", " ").title()
        chart_icon = "📊" if self.analyzer.detect_chart_libraries() else ""

        # separate out existing imports from body
        existing, clean_body = [], []
        for line in body.splitlines(keepends=True):
            if re.match(r"^\s*(import |from )", line):
                existing.append(line.strip())
            else:
                clean_body.append(line)
        body_clean = "".join(clean_body)

        all_imp = sorted(set(existing) | {
            imp for imp in self.imports_needed
            if not any(imp.split()[1].split(".")[0] in ex for ex in existing)
        })

        session_block = (
            "\n# ── Session State ────────────────────────────────────\n"
            "if 'initialized' not in st.session_state:\n"
            "    st.session_state.initialized = True\n"
        ) if self.add_session_state else ""

        sidebar_block = self._build_sidebar()

        dl_block = (
            "\n\n# ── Export ────────────────────────────────────────────\n"
            "st.divider()\n"
            "# Uncomment & replace `df` with your DataFrame:\n"
            "# st.download_button('⬇️ Download CSV', df.to_csv(index=False), 'output.csv', 'text/csv')\n"
        ) if self.add_download_button else ""

        header = textwrap.dedent(f"""\
# ══════════════════════════════════════════════════════════════
# AUTO-GENERATED STREAMLIT APP
# Source   : {self.filename}
# Converted: {datetime.now().strftime('%Y-%m-%d %H:%M')}
# Tool     : PyStreamlit Converter Pro
# ══════════════════════════════════════════════════════════════

{chr(10).join(all_imp)}

st.set_page_config(
    page_title="{stem}",
    page_icon="{chart_icon}",
    layout="{self.app_layout}",
)

st.title("{chart_icon} {stem}")
st.caption("_Converted from `{self.filename}` · PyStreamlit Converter Pro_")
st.divider()
""")

        if self.add_error_handling:
            # Enhanced error handling with more specific error messages
            indented = textwrap.indent(body_clean.strip(), "    ")
            main = (
                "\ntry:\n"
                f"{indented}\n"
                "except FileNotFoundError as _e:\n"
                "    st.error(f'❌ File not found: {_e}')\n"
                "    st.info('💡 Make sure all required data files are included in your app')\n"
                "    with st.expander('🔍 Full error details'):\n"
                "        import traceback\n"
                "        st.code(traceback.format_exc(), language='python')\n"
                "except ModuleNotFoundError as _e:\n"
                "    st.error(f'❌ Missing module: {_e.name}')\n"
                "    st.info('💡 Install missing packages with: pip install package_name')\n"
                "    with st.expander('🔍 Full error details'):\n"
                "        import traceback\n"
                "        st.code(traceback.format_exc(), language='python')\n"
                "except Exception as _e:\n"
                "    st.error(f'⚠️ Runtime error: {_e}')\n"
                "    with st.expander('🔍 Full error details'):\n"
                "        import traceback\n"
                "        st.code(traceback.format_exc(), language='python')\n"
            )
        else:
            main = "\n" + body_clean

        if self.add_main_guard:
            main = "\nif __name__ == '__main__':\n" + textwrap.indent(main, "    ")

        return header + session_block + sidebar_block + main + dl_block

# ─────────────────────────────────────────────────────────────────
# Notebook Extractor
# ─────────────────────────────────────────────────────────────────

def extract_notebook(content: bytes, preserve_markdown: bool = True) -> str:
    try:
        nb = nbformat.reads(content.decode("utf-8"), as_version=4)
    except Exception as exc:
        raise ValueError(f"Invalid notebook: {exc}") from exc

    parts = []
    for i, cell in enumerate(nb.cells, 1):
        if cell.cell_type == "markdown" and preserve_markdown:
            src = cell.source.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'\n# ── Markdown cell {i} ────────────────────────────────')
            parts.append(f'st.markdown("""\n{cell.source}\n""")')
        elif cell.cell_type == "code" and cell.source.strip():
            parts.append(f"\n# ── Code cell {i} ──────────────────────────────────")
            parts.append(cell.source.strip())

    return "\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────
# Cached File Processing
# ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def process_file(
    file_bytes: bytes, filename: str, file_hash: str,
    conversion_mode: str, chart_library: str, app_layout: str,
    sidebar_mode: str, add_caching: bool, add_error_handling: bool,
    add_download_button: bool, add_sidebar_controls: bool,
    add_session_state: bool, add_main_guard: bool,
    preserve_comments: bool, large_file_threshold: int,
) -> Tuple[str, str, List[str]]:
    ext = Path(filename).suffix.lower()
    try:
        original = (extract_notebook(file_bytes, preserve_markdown=preserve_comments)
                    if ext == ".ipynb" else file_bytes.decode("utf-8"))
    except Exception as exc:
        return f"# Decode error: {exc}", "", [f"❌ {exc}"]

    converter = HybridConverter(
        original, filename,
        conversion_mode=conversion_mode, chart_library=chart_library,
        app_layout=app_layout, sidebar_mode=sidebar_mode,
        add_caching=add_caching, add_error_handling=add_error_handling,
        add_download_button=add_download_button, add_sidebar_controls=add_sidebar_controls,
        add_session_state=add_session_state, add_main_guard=add_main_guard,
        preserve_comments=preserve_comments, large_file_threshold=large_file_threshold,
    )
    try:
        return converter.convert(), original, converter.get_report()
    except Exception as exc:
        return f"# Conversion error: {exc}", original, [f"❌ {exc}"]


def _conv_kwargs() -> Dict:
    return dict(
        conversion_mode=st.session_state.conversion_mode.lower(),
        chart_library=st.session_state.chart_library.lower(),
        app_layout=st.session_state.app_layout,
        sidebar_mode=st.session_state.sidebar_mode,
        add_caching=st.session_state.add_caching,
        add_error_handling=st.session_state.add_error_handling,
        add_download_button=st.session_state.add_download_button,
        add_sidebar_controls=st.session_state.add_sidebar_controls,
        add_session_state=st.session_state.add_session_state,
        add_main_guard=st.session_state.add_main_guard,
        preserve_comments=st.session_state.preserve_comments,
        large_file_threshold=st.session_state.large_file_threshold,
    )


def _process_uploaded(uf) -> Tuple[str, str, List[str]]:
    raw = uf.getvalue()
    fh = hashlib.md5(raw).hexdigest()[:8]
    return process_file(raw, uf.name, fh, **_conv_kwargs())


# ─────────────────────────────────────────────────────────────────
# Diff Builder
# ─────────────────────────────────────────────────────────────────

def build_diff_html(original: str, converted: str, context: int = 4) -> str:
    diff = list(difflib.unified_diff(
        original.splitlines(), converted.splitlines(), lineterm="", n=context))
    if not diff:
        return "<p>No differences found.</p>"
    rows = []
    for line in diff[2:]:
        if line.startswith("+"):
            rows.append(f'<span class="diff-add">+ {line[1:]}</span>')
        elif line.startswith("-"):
            rows.append(f'<span class="diff-rem">- {line[1:]}</span>')
        elif line.startswith("@@"):
            rows.append(f'<span style="color:#8892a4;padding:1px 8px;display:block">@@ {line[2:]} @@</span>')
        else:
            rows.append(f'<span class="diff-same">  {line}</span>')
    return f'<div class="diff-wrap">{"".join(rows)}</div>'


@st.cache_data
def get_sample_script() -> bytes:
    return b"""\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configuration
n_points = 500
random_seed = 42
show_grid = True
plot_title = "Time Series Analysis"

np.random.seed(random_seed)
dates  = pd.date_range('2023-01-01', periods=n_points, freq='D')
values = np.cumsum(np.random.randn(n_points)) + 100
df     = pd.DataFrame({'date': dates, 'value': values,
                        'volume': np.abs(np.random.randn(n_points)) * 1000})

print("Dataset overview:")
print(f"  Date range : {df['date'].min().date()} to {df['date'].max().date()}")
print(f"  Mean value : {df['value'].mean():.2f}")

display(df.head(10))
display(df.describe())

fig, axes = plt.subplots(2, 1, figsize=(12, 8))
axes[0].plot(df['date'], df['value'], linewidth=1.5, color='#4f8ef7')
axes[0].set_title(plot_title)
axes[0].grid(show_grid)
axes[1].bar(df['date'], df['volume'], color='#a78bfa', alpha=0.7)
axes[1].set_title('Volume')
plt.tight_layout()
plt.show()
"""


# ═══════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════

def metric_card(title: str, value: str, icon: str = "📊", subtitle: str = "") -> None:
    sub = f'<div style="font-size:.72em;opacity:.7;margin-top:2px">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
<div class="pc-metric">
  <div style="font-size:1.6em;line-height:1">{icon}</div>
  <div class="val">{value}</div>
  <div class="lbl">{title}</div>{sub}
</div>""", unsafe_allow_html=True)


def badge(text: str, variant: str = "") -> None:
    cls = f"pc-badge-{variant}" if variant else "pc-badge"
    st.markdown(f'<span class="pc-badge {cls}">{text}</span>', unsafe_allow_html=True)


def render_report(items: List[str]) -> None:
    for item in items:
        if "✅" in item:   icon, cls = "✓", "rep-ok"
        elif "⚠️" in item: icon, cls = "!", "rep-warn"
        elif "❌" in item:  icon, cls = "✗", "rep-err"
        else:               icon, cls = "i", "rep-info"
        st.markdown(
            f'<div class="rep-item"><span class="{cls}">[{icon}]</span>'
            f'<span>{item}</span></div>',
            unsafe_allow_html=True,
        )


def render_analysis(analyzer: CodeAnalyzer, filename: str) -> None:
    cmx = analyzer.compute_complexity()
    cols = st.columns(5)
    for col, (title, val, icon) in zip(cols, [
        ("Total Lines",  str(cmx["total_lines"]),  "📝"),
        ("Code Lines",   str(cmx["code_lines"]),   "💻"),
        ("Functions",    str(cmx["functions"]),    "⚡"),
        ("Classes",      str(cmx["classes"]),      "🏗️"),
        ("Branches",     str(cmx["cyclomatic"]),   "🔀"),
    ]):
        with col:
            metric_card(title, val, icon)

    st.markdown("")
    ca, cb = st.columns(2)

    with ca:
        st.markdown("**📦 Detected Libraries**")
        for cat, fn in [("Charts", analyzer.detect_chart_libraries),
                        ("ML/AI",  analyzer.detect_ml_libraries),
                        ("Data",   analyzer.detect_data_libraries)]:
            detected = fn()
            if detected:
                st.markdown(f"_{cat}_: " + "  ".join(f"`{l}`" for l in detected))

        st.markdown("**🔢 Transformable Calls**")
        counts = analyzer.count_transformable_calls()
        if counts:
            for name, n in counts.items():
                st.markdown(f"- `{name}` × {n}")
        else:
            st.caption("None detected.")

    with cb:
        st.markdown("**🧩 Functions**")
        fns = analyzer.get_functions()
        if fns:
            st.dataframe(
                [{"Name": f["name"], "Args": ", ".join(f["args"]) or "—",
                  "Lines": f["body_lines"], "Async": "✓" if f["is_async"] else ""}
                 for f in fns[:12]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.caption("No functions found.")

    st.markdown("**💡 Widget Suggestions**")
    sug = analyzer.suggest_widgets()
    if sug:
        st.dataframe(
            [{"Variable": s["name"], "Widget": s["widget"],
              "Default": str(s["default"]), "Line": s["lineno"]} for s in sug],
            use_container_width=True, hide_index=True,
        )
    else:
        st.caption("No hard-coded parameters found.")


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
<div class="sidebar-logo">
  <div class="logo-icon"></div>
  <div class="logo-title">PyStreamlit</div>
  <div class="logo-sub">CONVERTER PRO</div>
</div>""", unsafe_allow_html=True)
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        ti = "☀️" if st.session_state.theme == "dark" else "🌙"
        if st.button(ti, use_container_width=True, help="Toggle theme"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    with c2:
        if st.button("🔄", use_container_width=True, help="Reset"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.divider()
    st.markdown("### 📥 Upload")
    umode = st.radio("Type", ["📁 Files", "📦 ZIP"], label_visibility="collapsed")

    if umode == "📁 Files":
        files = st.file_uploader("Python / Notebook files",
                                 type=["py", "ipynb"], accept_multiple_files=True,
                                 label_visibility="collapsed")
        st.session_state.uploaded_files = files or []
        st.session_state.uploaded_zip = None
    else:
        zf = st.file_uploader("ZIP archive", type=["zip"], label_visibility="collapsed")
        st.session_state.uploaded_zip = zf
        st.session_state.uploaded_files = []

    st.divider()
    st.markdown("### ⚙️ Settings")

    mode_opts = ["Hybrid (Recommended)", "AST (Precise)", "Regex (Fast)"]
    st.session_state.conversion_mode = st.selectbox(
        "Strategy", mode_opts,
        index=mode_opts.index(st.session_state.conversion_mode)
              if st.session_state.conversion_mode in mode_opts else 0,
    )
    st.session_state.chart_library = st.selectbox(
        "Chart library", ["Auto-Detect", "Plotly", "Altair", "Matplotlib"])
    st.session_state.app_layout = st.selectbox("App layout", ["wide", "centered"])

    with st.expander("🔧 Advanced"):
        st.session_state.add_caching          = st.checkbox("@st.cache_data on loaders",  value=st.session_state.add_caching)
        st.session_state.add_error_handling   = st.checkbox("Error handling wrapper",      value=st.session_state.add_error_handling)
        st.session_state.add_sidebar_controls = st.checkbox("Auto sidebar widgets",        value=st.session_state.add_sidebar_controls)
        st.session_state.add_download_button  = st.checkbox("Download button stub",        value=st.session_state.add_download_button)
        st.session_state.add_session_state    = st.checkbox("Session state init",          value=st.session_state.add_session_state)
        st.session_state.add_main_guard       = st.checkbox("if __name__ == '__main__'",   value=st.session_state.add_main_guard)
        st.session_state.preserve_comments    = st.checkbox("Preserve comments",           value=st.session_state.preserve_comments)
        st.session_state.large_file_threshold = st.slider(
            "Large file threshold (KB)", 50, 5000,
            value=st.session_state.large_file_threshold, step=50)

    st.divider()
    st.markdown("### 🧪 Samples")
    sc1, sc2 = st.columns(2)
    with sc1:
        if st.button("📓 Notebook", use_container_width=True):
            raw = get_sample_notebook()
            buf = io.BytesIO(raw); buf.name = "sample_analysis.ipynb"
            st.session_state.uploaded_files = [buf]
            st.session_state.uploaded_zip = None
            st.rerun()
    with sc2:
        if st.button("📄 Script", use_container_width=True):
            raw = get_sample_script()
            buf = io.BytesIO(raw); buf.name = "sample_timeseries.py"
            st.session_state.uploaded_files = [buf]
            st.session_state.uploaded_zip = None
            st.rerun()

    s = st.session_state.stats
    if s["total_files"] > 0:
        st.divider()
        st.markdown("### 📊 Stats")
        st.metric("Files",        s["total_files"])
        st.metric("Successful",   s["successful"])
        if s["failed"]:
            st.metric("Failed",   s["failed"], delta_color="inverse")


# ═══════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════

import hashlib
import io
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import streamlit as st

# All necessary components are already defined in this file
# No relative imports needed


st.markdown("""
<div class="pc-hero">
  <h1> PyStreamlit Converter Pro</h1>
  <p>Transform <strong>Jupyter Notebooks</strong> &amp; <strong>Python scripts</strong>
     into polished, interactive <strong>Streamlit apps</strong> — in seconds.</p>
  <div>
    <span class="pc-badge">✨ AST + Regex engine</span>
    <span class="pc-badge pc-badge-green">📦 Batch &amp; ZIP</span>
    <span class="pc-badge pc-badge-purple">🔍 Deep Code Analysis</span>
    <span class="pc-badge pc-badge-amber">🔄 Diff Viewer</span>
    <span class="pc-badge">⚡ Auto Caching</span>
    <span class="pc-badge pc-badge-green">💡 Widget Suggester</span>
  </div>
</div>
""", unsafe_allow_html=True)


tab_convert, tab_analyze, tab_diff, tab_history, tab_dashboard, tab_help = st.tabs([
    "🚀 Convert", "🔍 Analyze", "🔄 Diff", "🕐 History", "📊 Dashboard", "📖 Help",
])


# ══════════════════════════════════════
# TAB 1 — CONVERT
# ══════════════════════════════════════
with tab_convert:
    if st.session_state.uploaded_files:
        ufs = st.session_state.uploaded_files
        st.markdown(f"### Processing **{len(ufs)}** file(s)")

        for idx, uf in enumerate(ufs):
            raw = uf.getvalue()
            ext = Path(uf.name).suffix.upper()
            st.markdown('<div class="pc-card">', unsafe_allow_html=True)

            hc1, hc2, hc3, hc4 = st.columns([4, 1, 1, 1])
            with hc1:
                st.markdown(f"#### 📑 `{uf.name}`")
                st.caption(f"{len(raw)/1024:.1f} KB · {ext[1:]}")
            with hc2: badge(ext, "green")
            with hc3: badge(st.session_state.conversion_mode.split()[0], "purple")
            with hc4: badge("Ready")

            try:
                with st.spinner(f"Converting `{uf.name}`…"):
                    t0 = time.time()
                    converted, original, report = _process_uploaded(uf)
                    elapsed = time.time() - t0

                s = st.session_state.stats
                s["total_files"] += 1
                s["successful"] += 1
                s["total_transformations"] += sum(1 for r in report if "✅" in r)

                st.session_state.conversion_history.append({
                    "filename": uf.name,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "elapsed": f"{elapsed:.2f}s",
                    "transformations": sum(1 for r in report if "✅" in r),
                    "lines_in": len(original.splitlines()),
                    "lines_out": len(converted.splitlines()),
                    "status": "ok",
                })

                st.success(f"✅ Done in **{elapsed:.2f}s** — "
                           f"{len(original.splitlines())} → {len(converted.splitlines())} lines, "
                           f"{sum(1 for r in report if '✅' in r)} transformations")

                view = st.radio(
                    "View", ["🔁 Side-by-Side", "📜 Original", "✨ Converted"],
                    horizontal=True, key=f"view_{idx}_{uf.name}",
                )
                lim = 25_000
                if "Side-by-Side" in view:
                    ca, cb = st.columns(2)
                    with ca:
                        st.markdown("##### 📜 Original Code")
                        st.code(original[:lim] + ("…" if len(original) > lim else ""),
                                language="python", line_numbers=True)
                    with cb:
                        st.markdown("##### ✨ Converted")
                        st.code(converted[:lim] + ("…" if len(converted) > lim else ""),
                                language="python", line_numbers=True)
                elif "Original" in view:
                    st.code(original[:lim*2], language="python", line_numbers=True)
                else:
                    st.code(converted[:lim*2], language="python", line_numbers=True)

                m1, m2, m3, m4, m5 = st.columns(5)
                with m1: st.metric("Original",   f"{len(original):,}", "chars")
                with m2: st.metric("Converted",  f"{len(converted):,}", "chars")
                with m3: st.metric("Delta",      f"{len(converted)-len(original):+,}", "chars")
                with m4: st.metric("Transforms", sum(1 for r in report if "✅" in r))
                with m5: st.metric("Time",       f"{elapsed:.2f}s")

                dl_col, rep_col = st.columns(2)
                with dl_col:
                    st.download_button(
                        f"⬇️ Download `{Path(uf.name).stem}_streamlit.py`",
                        converted,
                        file_name=f"{Path(uf.name).stem}_streamlit.py",
                        mime="text/plain",
                        key=f"dl_{idx}_{uf.name}",
                        use_container_width=True,
                        type="primary",
                    )
                with rep_col:
                    with st.expander("📋 Conversion Report"):
                        render_report(report)

            except Exception as exc:
                s = st.session_state.stats
                s["total_files"] += 1
                s["failed"] += 1
                st.session_state.conversion_history.append({
                    "filename": uf.name,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "status": "err", "error": str(exc),
                })
                st.error(f"❌ {exc}")
                with st.expander("🔍 Traceback"):
                    st.exception(exc)

            st.markdown("</div>", unsafe_allow_html=True)
            if idx < len(ufs) - 1:
                st.divider()

    elif st.session_state.uploaded_zip:
        st.markdown("### 📦 Batch ZIP Processing")
        try:
            results: Dict[str, Tuple] = {}
            with zipfile.ZipFile(st.session_state.uploaded_zip) as zr:
                py_files = [f for f in zr.namelist() if f.endswith((".py", ".ipynb"))]

            if not py_files:
                st.warning("No .py or .ipynb files in the ZIP.")
            else:
                prog = st.progress(0)
                status_ph = st.empty()
                for i, fname in enumerate(py_files):
                    status_ph.markdown(f"**{i+1}/{len(py_files)}** — `{fname}`")
                    with zipfile.ZipFile(st.session_state.uploaded_zip) as zr:
                        raw = zr.read(fname)
                    buf = io.BytesIO(raw); buf.name = fname
                    try:
                        conv, orig, rep = _process_uploaded(buf)
                        results[fname] = (conv, orig, rep, None)
                        st.session_state.stats["successful"] += 1
                    except Exception as exc:
                        results[fname] = (f"# Error: {exc}", "", [f"❌ {exc}"], str(exc))
                        st.session_state.stats["failed"] += 1
                    st.session_state.stats["total_files"] += 1
                    prog.progress((i + 1) / len(py_files))

                status_ph.empty(); prog.empty()
                ok = sum(1 for v in results.values() if v[3] is None)
                st.success(f"✅ Converted **{ok}/{len(py_files)}** files")

                out_zip = io.BytesIO()
                with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as ozf:
                    for fname, (conv, _, _, err) in results.items():
                        if err is None:
                            ozf.writestr(f"{Path(fname).stem}_streamlit.py", conv)
                st.download_button(
                    "⬇️ Download All (ZIP)",
                    out_zip.getvalue(),
                    "streamlit_converted_apps.zip",
                    "application/zip",
                    use_container_width=True, type="primary",
                )

                for fname, (conv, orig, rep, err) in results.items():
                    with st.expander(f"{'✅' if err is None else '❌'} {fname}"):
                        if err:
                            st.error(err)
                        else:
                            ca2, cb2 = st.columns(2)
                            with ca2:
                                st.markdown("**Original**")
                                st.code(orig[:5000], language="python")
                            with cb2:
                                st.markdown("**Converted**")
                                st.code(conv[:5000], language="python")
                            with st.expander("Report"):
                                render_report(rep)
        except Exception as exc:
            st.error(f"ZIP failed: {exc}")
            st.exception(exc)

    else:
        st.info("👈 Upload files or try a sample notebook/script using the sidebar.")


# ══════════════════════════════════════
# TAB 2 — ANALYZE
# ══════════════════════════════════════
with tab_analyze:
    st.markdown("### 🔍 Deep Code Analysis")

    if st.session_state.uploaded_files:
        names = [uf.name for uf in st.session_state.uploaded_files]
        sel = st.selectbox("Select file", names)
        uf = next(f for f in st.session_state.uploaded_files if f.name == sel)
        try:
            ext = Path(uf.name).suffix.lower()
            raw = uf.getvalue()
            src = extract_notebook(raw) if ext == ".ipynb" else raw.decode("utf-8")
            render_analysis(CodeAnalyzer(src), uf.name)
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
    else:
        st.info("Upload files to run analysis.")


# ══════════════════════════════════════
# TAB 3 — DIFF
# ══════════════════════════════════════
with tab_diff:
    st.markdown("### 🔄 Diff Viewer")
    st.caption("Line-by-line comparison: original vs converted code.")

    if st.session_state.uploaded_files:
        names = [uf.name for uf in st.session_state.uploaded_files]
        sel = st.selectbox("File to diff", names, key="diff_sel")
        uf = next(f for f in st.session_state.uploaded_files if f.name == sel)
        ctx = st.slider("Context lines", 1, 10, 4)

        try:
            converted, original, _ = _process_uploaded(uf)
            diff_html = build_diff_html(original, converted, ctx)
            dc1, dc2 = st.columns(2)
            with dc1: st.metric("Lines added",   diff_html.count('class="diff-add"'))
            with dc2: st.metric("Lines removed", diff_html.count('class="diff-rem"'))
            st.markdown(diff_html, unsafe_allow_html=True)
        except Exception as exc:
            st.error(f"Diff failed: {exc}")
    else:
        st.info("Upload a file to see the diff.")


# ══════════════════════════════════════
# TAB 4 — HISTORY
# ══════════════════════════════════════
with tab_history:
    st.markdown("### 🕐 Conversion History")
    hist = st.session_state.conversion_history

    if hist:
        if st.button("🗑️ Clear History"):
            st.session_state.conversion_history = []
            st.rerun()
        for entry in reversed(hist):
            ok = entry.get("status") == "ok"
            icon = "✅" if ok else "❌"
            extra = (
                f"  ·  {entry.get('lines_in','?')} → {entry.get('lines_out','?')} lines"
                f"  ·  {entry.get('transformations',0)} transforms  ·  ⏱ {entry.get('elapsed','—')}"
            ) if ok else f"  ·  {entry.get('error','')}"
            st.markdown(
                f'<div class="timeline-item {"ok" if ok else "err"}">'
                f'<strong>{icon} {entry["filename"]}</strong>'
                f'<span style="font-size:.8em;opacity:.6;margin-left:8px">{entry["timestamp"]}</span>'
                f'<div style="font-size:.82em;opacity:.7">{extra}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No conversions yet this session.")


# ══════════════════════════════════════
# TAB 5 — DASHBOARD
# ══════════════════════════════════════
with tab_dashboard:
    st.markdown("### 📊 Session Dashboard")
    s = st.session_state.stats

    if s["total_files"] > 0:
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1: metric_card("Total Files",   str(s["total_files"]),           "📁")
        with dc2: metric_card("Successful",    str(s["successful"]),            "✅")
        with dc3: metric_card("Failed",        str(s["failed"]),                "❌")
        with dc4: metric_card("Transforms",    str(s["total_transformations"]), "⚡")

        st.markdown("")
        rate = s["successful"] / s["total_files"] * 100
        st.markdown(f"**Success rate: {rate:.0f}%**")
        st.markdown(
            f'<div class="health-bar-bg">'
            f'<div class="health-bar-fg" style="width:{rate}%"></div></div>',
            unsafe_allow_html=True,
        )

        hist = st.session_state.conversion_history
        if hist:
            st.markdown("")
            st.markdown("**Recent conversions**")
            st.dataframe(
                [{"File": h["filename"], "Time": h["timestamp"],
                  "Status": "✅" if h.get("status") == "ok" else "❌",
                  "Lines in": h.get("lines_in", "—"), "Lines out": h.get("lines_out", "—"),
                  "Transforms": h.get("transformations", "—"), "Duration": h.get("elapsed", "—")}
                 for h in reversed(hist)],
                use_container_width=True, hide_index=True,
            )
    else:
        st.info("No conversions yet.")


# ══════════════════════════════════════
# TAB 6 — HELP
# ══════════════════════════════════════
with tab_help:
    st.markdown("### 📖 How It Works")
    ca, cb = st.columns(2)

    with ca:
        st.markdown("""
**🧠 Conversion Strategies**

| Strategy | Best For |
|---|---|
| **Hybrid** (default) | Any file — AST + regex |
| **AST Precise** | Clean Python 3.9+ |
| **Regex Fast** | Large / syntax-heavy files |

**🔄 Transformation Map**

| Original | Streamlit |
|---|---|
| `print(x)` | `st.write(x)` |
| `display(df)` | `st.dataframe(df)` |
| `df.head()` | `st.dataframe(df.head())` |
| `df.describe()` | `st.dataframe(df.describe())` |
| `plt.show()` | `st.pyplot(plt.gcf())` |
| `fig.show()` | `st.plotly_chart(fig)` |
| `show(bokeh_fig)` | `st.bokeh_chart(fig)` |
| Notebook markdown | `st.markdown(...)` |
| `%magic` / `!shell` | *(removed)* |
| `load_*(...)` fn | `@st.cache_data` added |
""")

    with cb:
        st.markdown("""
**✨ Advanced Features**

- **@st.cache_data auto-injection** — functions named `load_*`, `fetch_*`, `read_*`, `get_data_*` get cached automatically
- **Widget suggester** — scans hard-coded literals and proposes sidebar sliders, checkboxes, and text inputs
- **Error handling wrapper** — wraps the app body in `try/except` with `st.error()` + collapsible traceback
- **Diff viewer** — unified-diff comparison with configurable context lines
- **Deep code analysis** — complexity metrics, library detection, function inventory
- **Batch ZIP processing** — convert an entire folder, download all results as ZIP
- **Session history timeline** — timestamped record of every conversion
- **Light / Dark theme** — toggle from the sidebar

**💡 Tips**

1. Use the **🔍 Analyze** tab first to preview what will change
2. Enable **Auto sidebar widgets** to make hard-coded parameters interactive
3. **Hybrid** mode handles 99 % of notebooks and scripts reliably
4. The **Diff viewer** is great for code review before deploying
""")

    st.info("💡 Run the **Analyzer** before converting to see suggestions, then convert "
            "with **Auto Sidebar Widgets** enabled for a fully interactive app.")

# ═══════════════════════════════════════════════════════════════════
# CONVERTER CORE
# ═══════════════════════════════════════════════════════════════════

class CodeAnalyzer:
    def get_unique_report(self):
        seen = set()
        unique_report = []
        for item in self.conversion_report:
            if item not in seen:
                seen.add(item)
                unique_report.append(item)
        return unique_report


# ==============================
# NOTEBOOK PROCESSING
# ==============================

def extract_code_from_notebook(notebook_content: str, preserve_markdown: bool = True) -> str:
    """Convert notebook to Python script with enhanced markdown handling."""
    try:
        nb = nbformat.reads(notebook_content, as_version=4)
    except Exception as e:
        raise ValueError(f"Invalid notebook format: {e}")
    
    lines = []
    cell_num = 0
    
    for cell in nb.cells:
        cell_num += 1
        
        if cell.cell_type == "markdown" and preserve_markdown:
            md_content = cell.source
            lines.append(f"\n# {'='*60}")
            lines.append(f"# MARKDOWN CELL {cell_num}")
            lines.append(f"# {'='*60}")
            
            for md_line in md_content.split('\n'):
                if not md_line.strip():
                    lines.append("#")
                else:
                    clean_line = md_line.replace('"""', "'''").replace("'''", '"""')
                    if md_line.strip().startswith('#'):
                        lines.append(f"# {clean_line}")
                    else:
                        lines.append(f"# {clean_line}")
            lines.append("")
            
        elif cell.cell_type == "code":
            code_content = cell.source
            
            if lines and lines[-1].strip():
                lines.append("")
            
            if hasattr(cell, 'metadata') and cell.metadata:
                lines.append(f"# Cell {cell_num} metadata: {cell.metadata}")
            
            lines.append(code_content)
            
            if not code_content.endswith('\n'):
                lines.append("")
    
    result = "\n".join(lines)
    if not result.endswith('\n'):
        result += "\n"
    
    return result


# ==============================
# FILE PROCESSING UTILITIES
# ==============================

@st.cache_data(show_spinner=False)
def process_single_file_cached(file_bytes: bytes, filename: str, file_hash: str, 
                              conversion_mode: str, large_file_threshold: int, 
                              add_main_guard: bool, preserve_comments: bool):
    """Cached file processing function."""
    file_extension = Path(filename).suffix.lower()
    
    try:
        if file_extension == ".ipynb":
            original_code = extract_code_from_notebook(file_bytes.decode('utf-8'), 
                                                      preserve_markdown=preserve_comments)
        else:
            original_code = file_bytes.decode("utf-8")
        
        converter = HybridConverter(
            original_code, 
            filename, 
            conversion_mode=conversion_mode,
            large_file_threshold=large_file_threshold,
            add_main_guard=add_main_guard,
            preserve_comments=preserve_comments
        )
        streamlit_code = converter.convert()
        
        return streamlit_code, original_code, converter.get_conversion_report()
    
    except Exception as e:
        error_msg = f"Error processing {filename}: {str(e)}"
        return f"# {error_msg}\n# Original file could not be processed.", "", [f"❌ {error_msg}"]

def process_single_file(uploaded_file, **kwargs):
    """Process a single uploaded file."""
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()[:8]
    return process_single_file_cached(
        file_bytes, uploaded_file.name, file_hash, **kwargs
    )

