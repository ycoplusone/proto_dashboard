"""앱 테마 15종과 차트 색 맞추기.

테마는 .streamlit/config.toml의 [theme] 부분을 다시 써서 바꾼다. Streamlit은 config.toml이 바뀌면
서버를 다시 켜지 않아도 열려 있는 화면에 바로 반영한다. 설정 파일 하나를 바꾸므로 같은 서버에 접속한
모든 사람의 화면이 함께 바뀐다.

Plotly 차트는 Streamlit 테마를 따르지 않으므로(theme=None) palette()와 themed()로 색을 맞춘다.
"""

import json
import re
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

CONFIG = Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml"

PRETENDARD = "'Pretendard Variable':https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
NOTO_SANS = "'Noto Sans KR':https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap"
NOTO_SERIF = "'Noto Serif KR':https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&display=swap"
PLEX = "'IBM Plex Sans KR':https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap"
NANUM = "'Nanum Gothic':https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap"
GOWUN = "'Gowun Dodum':https://fonts.googleapis.com/css2?family=Gowun+Dodum&display=swap"

# 테마마다: 이름, 설명, 밝기, 강조색, 배경, 카드·입력 배경, 글자, 테두리, 사이드바(배경, 보조 배경, 글자, 테두리), 폰트, 모서리
THEMES: dict[str, dict] = {
    "modern": dict(name="모던 블루", desc="기본 테마 · 흰 바탕에 파랑 강조, Pretendard 폰트", base="light",
                   primary="#2a78d6", bg="#FFFFFF", secondary="#F4F6F9", text="#1F2937", border="#E6E8EC",
                   sidebar=("#F8F9FB", "#EEF1F5", "#1F2937", "#E6E8EC"), font=PRETENDARD, radius="12px"),
    "minimal": dict(name="미니멀 흑백", desc="색을 거의 쓰지 않는 단정한 화면 · IBM Plex Sans KR", base="light",
                    primary="#18181B", bg="#FFFFFF", secondary="#F4F4F5", text="#09090B", border="#E4E4E7",
                    sidebar=("#FAFAFA", "#F4F4F5", "#09090B", "#E4E4E7"), font=PLEX, radius="6px"),
    "corporate": dict(name="기업 네이비", desc="짙은 남색 메뉴 · 보고서다운 무게감, Noto Sans KR", base="light",
                      primary="#1D4ED8", bg="#FFFFFF", secondary="#F1F5F9", text="#0F172A", border="#E2E8F0",
                      sidebar=("#0F172A", "#1E293B", "#F8FAFC", "#334155"), font=NOTO_SANS, radius="6px"),
    "forest": dict(name="포레스트 그린", desc="초록 강조 · 편안하고 차분한 느낌", base="light",
                   primary="#15803D", bg="#FFFFFF", secondary="#F0F7F2", text="#14261B", border="#DCE9E0",
                   sidebar=("#F3F8F4", "#E3EFE6", "#14261B", "#DCE9E0"), font=PRETENDARD, radius="12px"),
    "sunset": dict(name="선셋 오렌지", desc="주황 강조 · 밝고 활기찬 느낌", base="light",
                   primary="#C2410C", bg="#FFFFFF", secondary="#FFF4ED", text="#2B1A10", border="#F3E1D5",
                   sidebar=("#FFF8F3", "#FDEBDF", "#2B1A10", "#F3E1D5"), font=PRETENDARD, radius="14px"),
    "violet": dict(name="바이올렛", desc="보라 강조 · 요즘 SaaS 서비스 느낌", base="light",
                   primary="#7C3AED", bg="#FFFFFF", secondary="#F5F3FF", text="#1E1B2E", border="#E7E3F7",
                   sidebar=("#FAF9FF", "#EFEBFD", "#1E1B2E", "#E7E3F7"), font=PRETENDARD, radius="16px"),
    "paper": dict(name="클래식 명조", desc="종이 같은 미색 바탕 · 인쇄 보고서 느낌, Noto Serif KR", base="light",
                  primary="#9A3412", bg="#FBF8F3", secondary="#F2ECE2", text="#33291F", border="#E4DACB",
                  sidebar=("#F5F0E7", "#EAE2D4", "#33291F", "#E4DACB"), font=NOTO_SERIF, radius="4px"),
    "nord": dict(name="노르드", desc="차가운 회청색 · 어두운 메뉴와 밝은 본문", base="light",
                 primary="#5E81AC", bg="#ECEFF4", secondary="#E5E9F0", text="#2E3440", border="#D8DEE9",
                 sidebar=("#2E3440", "#3B4252", "#ECEFF4", "#434C5E"), font=PRETENDARD, radius="8px"),
    "dark": dict(name="다크", desc="어두운 화면 · 눈이 편하고 대형 화면 발표에 좋음", base="dark",
                 primary="#4C9AFF", bg="#0E1117", secondary="#1A1F29", text="#E6E8EB", border="#2A303C",
                 sidebar=("#090C10", "#161B22", "#E6E8EB", "#2A303C"), font=PRETENDARD, radius="12px"),
    "dracula": dict(name="드라큘라", desc="보랏빛 다크 테마 · 개발자 도구 느낌, 고운돋움", base="dark",
                    primary="#BD93F9", bg="#282A36", secondary="#343746", text="#F8F8F2", border="#44475A",
                    sidebar=("#21222C", "#2C2E3A", "#F8F8F2", "#44475A"), font=GOWUN, radius="10px"),
    "ocean": dict(name="오션 틸", desc="청록 강조 · 시원하고 깔끔한 느낌, IBM Plex Sans KR", base="light",
                  primary="#0F766E", bg="#FFFFFF", secondary="#EFF7F6", text="#102A2A", border="#D6E9E6",
                  sidebar=("#F2F9F8", "#E0F0EE", "#102A2A", "#D6E9E6"), font=PLEX, radius="10px"),
    "rose": dict(name="로즈", desc="장밋빛 강조 · 부드럽고 화사한 느낌, 나눔고딕", base="light",
                 primary="#BE185D", bg="#FFFFFF", secondary="#FDF2F6", text="#2A1520", border="#F3DCE6",
                 sidebar=("#FEF6F9", "#FBE6EE", "#2A1520", "#F3DCE6"), font=NANUM, radius="16px"),
    "solarized": dict(name="솔라라이즈드", desc="따뜻한 크림색 바탕 · 오래 봐도 눈이 덜 피로함", base="light",
                      primary="#1F6FB2", bg="#FDF6E3", secondary="#EEE8D5", text="#073642", border="#E0D8C0",
                      sidebar=("#EEE8D5", "#E4DCC4", "#073642", "#D8CFB4"), font=PRETENDARD, radius="8px"),
    "contrast": dict(name="고대비", desc="검은 글자와 진한 테두리 · 잘 안 보이는 환경이나 인쇄용", base="light",
                     primary="#0040C1", bg="#FFFFFF", secondary="#F2F2F2", text="#000000", border="#8A8A8A",
                     sidebar=("#000000", "#1F1F1F", "#FFFFFF", "#5C5C5C"), font=NOTO_SANS, radius="4px"),
    "midnight": dict(name="미드나잇", desc="짙은 남색 다크 테마 · 하늘색 강조, 상황판 느낌", base="dark",
                     primary="#38BDF8", bg="#0B1220", secondary="#131C2E", text="#E2E8F0", border="#22304A",
                     sidebar=("#070C16", "#111A2B", "#E2E8F0", "#22304A"), font=PRETENDARD, radius="12px"),
}
DEFAULT = "modern"


# ---------------------------------------------------------------- 테마 적용 (config.toml 다시 쓰기)
def active() -> str:
    """config.toml 맨 위 표시(# active-theme: key)로 지금 테마를 알아낸다."""
    m = re.search(r"^# active-theme: (\w+)", CONFIG.read_text(encoding="utf-8"), re.M) if CONFIG.exists() else None
    return m.group(1) if m and m.group(1) in THEMES else DEFAULT


def _q(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def theme_toml(key: str) -> str:
    t = THEMES[key]
    sb_bg, sb_sec, sb_text, sb_border = t["sidebar"]
    lines = [
        "[theme]",
        f"base = {_q(t['base'])}",
        f"primaryColor = {_q(t['primary'])}",
        f"backgroundColor = {_q(t['bg'])}",
        f"secondaryBackgroundColor = {_q(t['secondary'])}",
        f"textColor = {_q(t['text'])}",
        f"borderColor = {_q(t['border'])}",
        f"linkColor = {_q(t['primary'])}",
        "showWidgetBorder = true",
        "showSidebarBorder = true",
        f"baseRadius = {_q(t['radius'])}",
        f"buttonRadius = {_q(t['radius'])}",
        f"font = {_q(t['font'])}",
        "baseFontSize = 15",
        '''headingFontSizes = ["30px", "22px", "18px", "16px", "15px", "14px"]''',
        "headingFontWeights = [700, 700, 600, 600, 600, 600]",
        '''metricValueFontSize = "2rem"''',
        "metricValueFontWeight = 700",
        "linkUnderline = false",
        f"dataframeHeaderBackgroundColor = {_q(t['secondary'])}",
        f"dataframeBorderColor = {_q(t['border'])}",
        "",
        "[theme.sidebar]",
        f"backgroundColor = {_q(sb_bg)}",
        f"secondaryBackgroundColor = {_q(sb_sec)}",
        f"textColor = {_q(sb_text)}",
        f"borderColor = {_q(sb_border)}",
        f"primaryColor = {_q(t['primary'])}",
        f"linkColor = {_q(t['primary'] if sb_text == t['text'] else sb_text)}",
    ]
    return "\n".join(lines) + "\n"


def apply_theme(key: str) -> None:
    """config.toml에서 [theme] 이후를 새 테마로 바꾼다. [server] 등 앞부분은 그대로 둔다."""
    text = CONFIG.read_text(encoding="utf-8")
    head = re.sub(r"^# active-theme: \w+\n", "", text.split("[theme]")[0].split("# 테마:")[0], flags=re.M).rstrip() + "\n\n"
    CONFIG.write_text(f"# active-theme: {key}\n" + head
                      + f"# 테마: {THEMES[key]['name']} — '도구 > 테마 바꾸기' 화면에서 바꾸면 아래가 다시 써진다 (utils/theme.py)\n"
                      + theme_toml(key), encoding="utf-8")


# ---------------------------------------------------------------- 차트 색
def _mix(a: str, b: str, w: float) -> str:
    """두 색을 섞는다. w = a의 비율."""
    ca = [int(a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x * w + y * (1 - w)):02x}" for x, y in zip(ca, cb))


def palette() -> dict[str, str]:
    """지금 테마에 맞는 차트 색: 강조·연한 강조·글자·흐린 글자·회색 막대·격자·배경."""
    t = THEMES[active()]
    return dict(
        accent=t["primary"], soft=_mix(t["primary"], t["bg"], 0.25), ink=t["text"],
        muted=_mix(t["text"], t["bg"], 0.6), neutral=_mix(t["text"], t["bg"], 0.25),
        grid=_mix(t["text"], t["bg"], 0.12), bg=t["bg"], card=t["secondary"], dark=t["base"] == "dark",
        font=t["font"].split(":")[0].strip("'") + ", sans-serif",
    )


# 갤러리 차트에 박혀 있는 밝은 테마용 색 → 지금 테마 색
_LIGHT = {"#fcfcfb": "bg", "#0b0b0b": "ink", "#52514e": "muted", "#898781": "muted",
          "#c3c2b7": "neutral", "#e1e0d9": "grid", "white": "bg", "#ffffff": "bg"}


def themed(fig: go.Figure) -> go.Figure:
    """밝은 바탕 기준으로 만든 차트의 배경·글자·회색을 지금 테마 색으로 바꾼다. 범주 색은 그대로 둔다."""
    p = palette()
    fig.update_layout(font_family=p["font"])  # 차트 글꼴도 테마 글꼴로
    if active() == DEFAULT:
        return fig
    spec = fig.to_json()  # plotly 인코더라 numpy 배열도 그대로 옮겨진다
    for old, role in _LIGHT.items():
        spec = re.sub(re.escape(f'"{old}"'), f'"{p[role]}"', spec, flags=re.I)
    return pio.from_json(spec)
