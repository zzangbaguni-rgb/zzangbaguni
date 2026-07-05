#!/usr/bin/env python3
# KAMIS 소매가격 수집 -> 저장소 루트 data.json/data.js
# 지역(시/도)별 + 시장별(전통시장 개별/대형마트 평균). 고기/과일은 부위·품종별.
# 산지/도매 등 비소매 제외. "새로 나온 것"(지난주 없다가 이번주 등장) 판정 포함.
# 실행: python3 scripts/collect.py   (표준 파이썬만)
import json, os, re, urllib.parse, urllib.request, datetime
HERE=os.path.dirname(os.path.abspath(__file__)); PROJ=os.path.dirname(HERE)
KEY=os.environ.get("KAMIS_KEY") or open(os.path.join(HERE,".serviceKey")).read().strip()
OUT=os.path.join(PROJ,"data.json")
_t=datetime.date.today(); _d=datetime.timedelta
def _y(x): return x.strftime("%Y%m%d")
TW=(_y(_t-_d(days=8)), _y(_t-_d(days=1)))    # 최근 8일 -> 가장 최근 조사일(시장이 잘 안 사라지게)
BL=(_y(_t-_d(days=15)), _y(_t-_d(days=9)))   # 그 전 주 (등락 비교 기준)
ITEMS=[
  ('111','쌀','100'),
  ('112','찹쌀','100'),
  ('113','혼합곡','100'),
  ('114','기장','100'),
  ('121','보리쌀','100'),
  ('141','콩','100'),
  ('142','팥','100'),
  ('143','녹두','100'),
  ('144','메밀','100'),
  ('151','고구마','100'),
  ('152','감자','100'),
  ('161','귀리','100'),
  ('162','보리','100'),
  ('163','수수','100'),
  ('164','율무','100'),
  ('211','배추','200'),
  ('212','양배추','200'),
  ('213','시금치','200'),
  ('214','상추','200'),
  ('215','얼갈이배추','200'),
  ('216','갓','200'),
  ('217','연근','200'),
  ('218','우엉','200'),
  ('221','수박','200'),
  ('222','참외','200'),
  ('223','오이','200'),
  ('224','호박','200'),
  ('225','토마토','200'),
  ('226','딸기','200'),
  ('231','무','200'),
  ('232','당근','200'),
  ('233','열무','200'),
  ('241','건고추','200'),
  ('242','풋고추','200'),
  ('243','붉은고추','200'),
  ('244','피마늘','200'),
  ('245','양파','200'),
  ('246','파','200'),
  ('247','생강','200'),
  ('248','고춧가루','200'),
  ('251','가지','200'),
  ('252','미나리','200'),
  ('253','깻잎','200'),
  ('254','부추','200'),
  ('255','피망','200'),
  ('256','파프리카','200'),
  ('257','멜론','200'),
  ('258','깐마늘(국산)','200'),
  ('259','깐마늘(수입)','200'),
  ('261','브로콜리','200'),
  ('262','양상추','200'),
  ('263','청경채','200'),
  ('264','케일','200'),
  ('265','콩나물','200'),
  ('266','절임배추','200'),
  ('279','알배기배추','200'),
  ('280','브로콜리','200'),
  ('422','방울토마토','200'),
  ('411','사과','400'),
  ('412','배','400'),
  ('413','복숭아','400'),
  ('414','포도','400'),
  ('415','감귤','400'),
  ('416','단감','400'),
  ('418','바나나','400'),
  ('419','참다래','400'),
  ('420','파인애플','400'),
  ('421','오렌지','400'),
  ('423','자몽','400'),
  ('424','레몬','400'),
  ('425','체리','400'),
  ('426','건포도','400'),
  ('427','건블루베리','400'),
  ('428','망고','400'),
  ('429','블루베리','400'),
  ('430','아보카도','400'),
  ('4301','소고기','500'),
  ('4304','돼지고기','500'),
  ('4401','수입 소고기','500'),
  ('4402','수입 돼지고기','500'),
  ('9901','닭고기','500'),
  ('9903','계란','500'),
  ('9908','우유','500'),
  ('520','오리고기','500'),
  ('611','고등어','600'),
  ('612','꽁치','600'),
  ('613','갈치','600'),
  ('614','조기','600'),
  ('615','명태','600'),
  ('616','삼치','600'),
  ('619','물오징어','600'),
  ('638','마른멸치','600'),
  ('639','북어','600'),
  ('640','마른오징어','600'),
  ('641','김','600'),
  ('642','마른미역','600'),
  ('643','염장미역','600'),
  ('644','굴','600'),
  ('647','넙치','600'),
  ('648','우럭','600'),
  ('649','수입조기','600'),
  ('650','새우젓','600'),
  ('651','멸치액젓','600'),
  ('652','천일염','600'),
  ('653','전복','600'),
  ('654','새우','600'),
  ('656','꽃게','600'),
  ('658','홍합','600'),
  ('659','가리비','600'),
  ('660','건다시마','600'),
  ('661','바지락','600'),
  ('662','고등어필렛','600'),
  ('663','전어','600'),
]
EXCLUDE=set()                                          # (진단 결과) 국산 축산 소매는 4301/4304/9901/9903/9908 로만 들어옴 — 제외하면 안 됨
VARIETY={"4301","4304","4401","4402","411","412","414","415"}  # 부위/품종 분리(국산 소·돼지 포함)
MART_RE=re.compile(r'(유통|SSM|백화점|전문점|생협|대형마트|슈퍼|아울렛|마트)')
URL="https://apis.data.go.kr/B552845/perDay/price"
def fetch(item,ctgry,s,e):
    q={"serviceKey":KEY,"returnType":"JSON","numOfRows":"3000","cond[se_cd::EQ]":"01",
       "cond[ctgry_cd::EQ]":ctgry,"cond[item_cd::EQ]":item,
       "cond[exmn_ymd::GTE]":s,"cond[exmn_ymd::LTE]":e}
    try:
        with urllib.request.urlopen(URL+"?"+urllib.parse.urlencode(q),timeout=15) as r:
            return json.load(r)
    except Exception:
        return {}
def rows(js):
    try: return js["response"]["body"]["items"]["item"] or []
    except Exception: return []
def avg(a): return int(sum(a)/len(a)) if a else None
def mkey_of(it):
    nm=it.get("mrkt_nm") or ""
    if MART_RE.search(nm): return ("_mart","대형마트 평균")
    return (it.get("mrkt_cd") or nm, nm)
def add_vrty(store, it, p, dt):
    vc=it.get("vrty_cd")
    e=store.setdefault(vc,{"vn":it.get("vrty_nm") or "","cnt":0,"latest":"","p":[],"unit":""})
    e["cnt"]+=1; e["unit"]=(str(it.get("unit_sz") or "")+str(it.get("unit") or ""))
    if dt> e["latest"]: e["latest"]=dt; e["p"]=[p]
    elif dt==e["latest"]: e["p"].append(p)
def organize(rws):
    o={}
    for it in rws:
        sgg=it.get("sgg_cd")
        if not sgg: continue
        try: p=float(it.get("exmn_dd_prc"))
        except Exception: continue
        dt=str(it.get("exmn_ymd") or "")
        reg=o.setdefault(sgg,{"name":it.get("sgg_nm") or sgg,"all":{},"mk":{}})
        add_vrty(reg["all"], it, p, dt)
        mk,mn=mkey_of(it)
        if not mk: continue          # 시장코드·이름 없는 레코드: 전체평균엔 이미 반영, 개별 시장 칩은 만들지 않음
        m=reg["mk"].setdefault(mk,{"name":mn,"v":{}})
        add_vrty(m["v"], it, p, dt)
    return o
def entries(vmap, blv, code, name, is_var, item_new):
    out=[]
    keys=list(vmap.keys()) if is_var else ([max(vmap,key=lambda k:vmap[k]["cnt"])] if vmap else [])
    for vc in keys:
        e=vmap[vc]; now=avg(e["p"])
        if now is None: continue
        bv=blv.get(vc); base=avg(bv["p"]) if bv else None
        pct=int((now-base)/base*100) if base else None
        vn=e["vn"]
        label=(vn if name in vn else f"{name} {vn}") if (is_var and vn and vn!=name) else name
        d={"code":f"{code}-{vc}","name":label,"price":now,"unit":e["unit"],"base":base,"pct":pct,"asof":e["latest"]}
        if item_new: d["isNew"]=True
        out.append(d)
    return out

byRegion={}; region_names={}; markets={}; byMarket={}
for code,name,ctgry in ITEMS:
    if code in EXCLUDE: continue
    is_var = code in VARIETY
    tw=organize(rows(fetch(code,ctgry,*TW)))
    bl=organize(rows(fetch(code,ctgry,*BL)))
    for sgg,reg in tw.items():
        region_names[sgg]=reg["name"]
        blreg=bl.get(sgg,{}); blall=blreg.get("all",{})
        item_new = (len(blall)==0)
        for e in entries(reg["all"], blall, code, name, is_var, item_new):
            byRegion.setdefault(sgg,[]).append(e)
        for mk,m in reg["mk"].items():
            blmk=blreg.get("mk",{}).get(mk,{}).get("v",{})
            ent=entries(m["v"], blmk, code, name, is_var, item_new)
            if ent:
                markets.setdefault(sgg,{})[mk]=m["name"]
                byMarket.setdefault(f"{sgg}|{mk}",[]).extend(ent)
    print(f"{name}{' [부위별]' if is_var else ''}: 지역 {len(tw)}")

regions=sorted(region_names.keys(), key=lambda s:-len(byRegion.get(s,[])))
markets_out={}
for sgg,mm in markets.items():
    named=[(k,v) for k,v in mm.items() if k and v and k!="_mart"]
    named.sort(key=lambda kv:-len(byMarket.get(f"{sgg}|{kv[0]}",[])))
    lst=[{"key":"_all","name":"전체 평균"}]+[{"key":k,"name":v} for k,v in named]
    if "_mart" in mm: lst.append({"key":"_mart","name":"대형마트 평균"})
    if len(lst)>1: markets_out[sgg]=lst
data={"updated":_t.isoformat(),
      "regions":[{"code":s,"name":region_names[s]} for s in regions],
      "byRegion":byRegion,"markets":markets_out,"byMarket":byMarket}

# ── 외생 이벤트 알림 ───────────────────────────────────────────────
# 기상청 기상특보(특보현황) → 작황 영향 알림. 실패해도 수집은 절대 안 깨지게 방어적.
def weather_alerts():
    key=os.environ.get("KMA_KEY") or os.environ.get("KAMIS_KEY")   # 같은 data.go.kr 계정이면 KAMIS_KEY로도 됨
    if not key: return []
    url="https://apis.data.go.kr/1360000/WthrWrnInfoService/getPwnStatus"
    q={"serviceKey":key,"dataType":"JSON","numOfRows":"10","pageNo":"1"}
    try:
        with urllib.request.urlopen(url+"?"+urllib.parse.urlencode(q),timeout=15) as r:
            js=json.load(r)
        items=js.get("response",{}).get("body",{}).get("items",{})
        items=items.get("item",[]) if isinstance(items,dict) else []
        if isinstance(items,dict): items=[items]
        items=[it for it in items if isinstance(it,dict) and it.get("t6")]
        if not items: return []
        latest=max(items,key=lambda it:str(it.get("tmFc") or ""))
        t6=str(latest.get("t6") or "")
        # 작황에 영향 주는 육상 특보만 (해상 풍랑·강풍 등은 제외)
        RULES=[("태풍","🌀","태풍 특보 발효 중 — 채소·과일 작황에 영향 줄 수 있어요"),
               ("호우","🌧️","호우 특보 발효 중 — 잎채소·과일 침수·작황 영향 가능"),
               ("폭염","🔥","폭염 특보 발효 중 — 채소 생육·물가에 영향 줄 수 있어요"),
               ("대설","❄️","대설 특보 발효 중 — 시설채소·출하에 영향 가능"),
               ("한파","🥶","한파 특보 발효 중 — 시설채소·과일에 영향 가능")]
        out=[]
        for kw,icon,msg in RULES:
            if kw in t6: out.append({"icon":icon,"msg":msg,"src":"기상청 특보현황"})
        return out
    except Exception as e:
        print("기상특보 스킵:", e); return []

# scripts/alerts.json(수기, until 만료일 지원) — 형식: [{"icon":"🌀","msg":"...","until":"2026-07-10"}]
def manual_alerts():
    try:
        with open(os.path.join(HERE,"alerts.json"),encoding="utf-8") as f:
            raw=json.load(f)
        today=_t.isoformat()
        return [a for a in raw if isinstance(a,dict) and a.get("msg")
                and (not a.get("until") or a["until"]>=today)]
    except FileNotFoundError:
        return []
    except Exception as e:
        print("alerts.json 스킵:", e); return []

alerts = weather_alerts() + manual_alerts()   # 자동(기상) 먼저, 수기 뒤
if alerts:
    data["alerts"]=alerts
    print(f"알림 {len(alerts)}건 적재")

open(OUT,"w",encoding="utf-8").write(json.dumps(data,ensure_ascii=False,indent=1))
open(os.path.join(PROJ,"data.js"),"w",encoding="utf-8").write(
    "window.PRICE_DATA = "+json.dumps(data,ensure_ascii=False)+";\n")
print(f"\n생성: 지역 {len(regions)}, 시장보유지역 {len(markets_out)} -> {OUT}")
