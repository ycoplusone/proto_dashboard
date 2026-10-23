"""인사이트 화면 공통: 인사이트 카드 후보 계산, 분해 트리 그리기, 100명 그림 그리기.

인사이트는 모두 데이터에서 계산한다. 카드마다 '몇 배 차이'(score)를 붙여, 차이가 큰 순으로 보여 준다.
  - 두 묶음 비교: 큰 쪽 ÷ 작은 쪽
  - 비중: 실제 비중 ÷ 고르게 나눴을 때 비중 (예: 상위 10% 고객이 매출 28% → 2.8배)
"""

from dataclasses import dataclass, field
from html import escape

import streamlit as st

from utils import arpu, ctrt, daily, period
from utils.daily import josa, signed
from utils.theme import palette


@dataclass
class Insight:
    score: float          # 몇 배 차이 (정렬용)
    big: str              # 큰 숫자 (예: "12배")
    title: str            # 한 문장
    sub: str              # 근거 숫자
    page: str             # 자세히 볼 페이지 파일
    source: str           # 자료 이름
    query: dict = field(default_factory=dict)


@st.cache_data(show_spinner="인사이트를 계산하고 있어요…")
def insights() -> list[Insight]:
    out: list[Insight] = []

    # ---------------------------------------------------------------- 계약현황 (z98)
    df = ctrt.load()
    cu = ctrt.customers()
    m = cu[cu["고객유형"] == "MASS"].groupby("사용")["해지대기"].mean()
    r = m["인터넷만"] / m["TV + 인터넷"]
    out.append(Insight(r, f"{r:.0f}배", f"인터넷만 쓰는 개인 고객은 TV와 함께 쓰는 고객보다 해지 대기가 {r:.0f}배 많아요",
                       f"고객 1,000명 중 해지 대기: 인터넷만 {m['인터넷만'] * 1000:.0f}명 · TV + 인터넷 {m['TV + 인터넷'] * 1000:.0f}명",
                       "app_pages/contract/risk.py", "계약현황"))

    u = arpu.users()
    a = u[u["고객유형"] == "MASS"].groupby("사용")["청구금액"].mean()
    r = a["TV + 인터넷"] / a["TV만"]
    out.append(Insight(r, f"{r:.1f}배", f"TV와 인터넷을 함께 쓰는 개인 고객은 TV만 쓰는 고객보다 한 달에 {r:.1f}배를 내요",
                       f"ARPU: TV + 인터넷 {a['TV + 인터넷']:,.0f}원 · TV만 {a['TV만']:,.0f}원", "app_pages/arpu/bundle.py", "계약현황"))

    g = df.groupby("상품군", observed=True)["해지대기"].agg(["mean", "size"])
    g = g[g["size"] >= 20000]
    hi, avg = g["mean"].idxmax(), df["해지대기"].mean()
    r = g.loc[hi, "mean"] / avg
    out.append(Insight(r, f"{r:.1f}배", f"{josa(hi, '은는')} 해지 대기가 전체 평균의 {r:.1f}배예요",
                       f"1,000건 중 {g.loc[hi, 'mean'] * 1000:.0f}건 · 전체 평균 {avg * 1000:.0f}건", "app_pages/contract/product.py", "계약현황"))

    old, new = df[df["가입연도"] <= 2014]["해지대기"].mean(), df[df["가입연도"] >= 2024]["해지대기"].mean()
    r = old / new
    out.append(Insight(r, f"{r:.1f}배", f"2014년 이전에 가입한 계약은 2024년 이후 가입한 계약보다 해지 대기가 {r:.1f}배 많아요",
                       f"1,000건 중 {old * 1000:.0f}건 · {new * 1000:.0f}건", "app_pages/contract/tenure.py", "계약현황"))

    s = df.groupby("SO", observed=True)["해지대기"].mean()
    r = s.max() / s.min()
    out.append(Insight(r, f"{r:.1f}배", f"해지 대기가 가장 많은 SO({s.idxmax()})는 가장 적은 SO({s.idxmin()})의 {r:.1f}배예요",
                       f"1,000건 중 {s.max() * 1000:.0f}건 · {s.min() * 1000:.0f}건", "app_pages/contract/region.py", "계약현황"))

    bill = u["청구금액"].sort_values(ascending=False)
    share = bill.head(len(bill) // 10).sum() / bill.sum()
    out.append(Insight(share / 0.10, f"{share:.0%}", f"상위 10% 고객이 한 달 매출의 {share:.0%}를 내요",
                       f"고객 {len(bill) // 10:,}명 · 모두 같은 금액을 낸다면 10%", "app_pages/arpu/top.py", "계약현황"))

    # ---------------------------------------------------------------- 일별실적 (z99)
    z = daily.load()
    seg = z.groupby(["사업", "고객유형"])["순증건"].sum()
    worst = seg.idxmin()
    share = seg[worst] / seg.sum()  # 전체 순증 대비 (다른 화면의 '순감의 89%'와 같은 기준)
    out.append(Insight(share / (1 / len(seg)), f"{share:.0%}", f"2025년 순감의 {share:.0%}가 {worst[0]} {worst[1]}에서 나왔어요",
                       f"{worst[0]} {worst[1]} {signed(seg[worst])} · 사업 × 고객유형 {len(seg)}개 묶음 중 하나", "app_pages/daily/business.py",
                       "일별실적"))

    dd = period.daily()
    have = dd[~dd["자료없음"]]
    for col, name in [("해지건", "해지"), ("설치건", "설치")]:
        usual = have.groupby("요일")[col].transform("median")
        ratio = have[col] / usual
        d = ratio.idxmax()
        out.append(Insight(ratio[d], f"{ratio[d]:.1f}배", f"{period.label(d)} {name}가 평소 {period.DAYS[d.dayofweek]}요일의 {ratio[d]:.1f}배였어요",
                           f"그날 {have.loc[d, col]:,}건 · 평소(같은 요일 중앙값) {usual[d]:,.0f}건", "app_pages/period/briefing.py",
                           "일별실적", {"date": f"{d:%Y-%m-%d}"}))

    mon = dd.groupby("월")["순증건"].sum()
    h1, h2 = mon.loc[1:6].sum(), mon.loc[7:12].sum()
    if h1 < 0 and h2 < 0:
        r = min(h1, h2) / max(h1, h2)  # 둘 다 음수라 더 많이 줄어든 쪽 ÷ 덜 줄어든 쪽
        out.append(Insight(r, f"{r:.1f}배", f"{'하반기' if h2 < h1 else '상반기'} 순감이 {'상반기' if h2 < h1 else '하반기'}의 {r:.1f}배예요",
                           f"상반기 {signed(h1)} · 하반기 {signed(h2)}", "app_pages/period/timeline.py", "일별실적"))

    cut = have["순증건"].quantile(0.10)
    hot = have[have["순증건"] <= cut]
    end5 = (hot.index.day > hot.index.days_in_month - 5).mean()
    base = (have.index.day > have.index.days_in_month - 5).mean()
    out.append(Insight(end5 / base, f"{end5:.0%}", f"순감이 가장 컸던 날(하위 10%)의 {end5:.0%}가 월말 5일이에요",
                       f"{len(hot)}일 중 {int(round(end5 * len(hot)))}일 · 1년 중 월말 5일의 비중은 {base:.0%}", "app_pages/period/month_calendar.py",
                       "일별실적"))

    return sorted(out, key=lambda i: i.score, reverse=True)


# ---------------------------------------------------------------- 분해 트리
@dataclass
class Node:
    name: str
    value: float
    children: list["Node"] = field(default_factory=list)
    note: str = ""


def tree_html(root: Node, fmt, hot_sign: int = -1, tag_text: str = "원인") -> str:
    """root를 들여쓴 줄로 그린다. 각 단계에서 hot_sign 방향(−1 = 가장 작은 값)으로 가장 큰 가지를 '원인'으로 파랑 표시한다.
    막대 길이는 |값| ÷ |root 값|이다."""
    P = palette()
    scale = max(abs(root.value), 1)
    rows = []

    def walk(n: Node, depth: int, hot: bool, share: float | None):
        width = min(abs(n.value) / scale * 100, 100)
        color = P["accent"] if hot else P["neutral"]
        weight = 700 if hot else 400
        pre = "" if depth == 0 else "&nbsp;" * 4 * (depth - 1) + "└&nbsp;"
        tag = f' <span style="color:{P["accent"]};font-size:12px">◀ {tag_text}{f" ({share:.0%})" if share is not None else ""}</span>' if hot and depth else ""
        note = f'<div style="font-size:12px;color:{P["muted"]};padding-left:{4 + 16 * depth}px">{escape(n.note)}</div>' if n.note else ""
        rows.append(
            f'<div style="display:grid;grid-template-columns:minmax(150px,38%) 110px 1fr;gap:10px;align-items:center;padding:5px 0;'
            f'border-bottom:1px solid {P["grid"]}">'
            f'<div style="color:{P["ink"]};font-weight:{weight};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{pre}{escape(n.name)}{tag}</div>'
            f'<div style="text-align:right;font-variant-numeric:tabular-nums;font-weight:{weight};color:{P["ink"]}">{fmt(n.value)}</div>'
            f'<div style="background:{P["grid"]}55;border-radius:4px;height:14px"><div style="width:{width:.1f}%;height:14px;'
            f'background:{color};border-radius:4px"></div></div></div>{note}')
        if not n.children:
            return
        pick = min(n.children, key=lambda c: c.value * -hot_sign) if hot_sign else None
        for c in n.children:
            is_hot = hot and c is pick and (c.value * hot_sign > 0)
            walk(c, depth + 1, is_hot, (c.value / n.value) if is_hot and n.value else None)

    walk(root, 0, True, None)
    return f'<div style="font-size:14px">{"".join(rows)}</div>'


# ---------------------------------------------------------------- 100명 그림
# st.html은 <svg>를 걸러 내서, 아이콘은 div 모양으로 그린다.
PERSON = ('<div style="width:13px;height:18px;display:flex;flex-direction:column;align-items:center;gap:1px">'
          '<div style="width:6px;height:6px;border-radius:50%;background:{c}"></div>'
          '<div style="width:12px;height:10px;border-radius:6px 6px 2px 2px;background:{c}"></div></div>')
SQUARE = '<div style="width:13px;height:13px;border-radius:3px;background:{c}"></div>'


def people_html(n: int, total: int = 100, shape: str = "person") -> str:
    """아이콘 total개 중 n개를 파랑으로 칠한다 (10개씩 한 줄). shape = person(사람) | square(계약·돈)."""
    P = palette()
    icon = PERSON if shape == "person" else SQUARE
    on, off = icon.format(c=P["accent"]), icon.format(c=P["grid"])
    cells = "".join(f"<div>{on if i < n else off}</div>" for i in range(total))
    return f'<div style="display:grid;grid-template-columns:repeat(10,13px);gap:4px 5px;justify-content:start">{cells}</div>'


def per100(rate: float) -> int:
    return int(round(rate * 100))

