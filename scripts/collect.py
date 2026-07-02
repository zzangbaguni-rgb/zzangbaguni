#!/usr/bin/env python3
# KAMIS 소매가격 수집 -> app 루트 data.json/data.js  (지역별 x 품종별)
# 실행: python3 scripts/collect.py   (표준 파이썬만, jq 불필요)
import json, os, urllib.parse, urllib.request, datetime
HERE=os.path.dirname(os.path.abspath(__file__)); PROJ=os.path.dirname(HERE)
KEY=os.environ.get("KAMIS_KEY") or open(os.path.join(HERE,".serviceKey")).read().strip()
OUT=os.path.join(PROJ,"data.json")
_t=datetime.date.today(); _d=datetime.timedelta
def _y(x): return x.strftime("%Y%m%d")
TW=(_y(_t-_d(days=5)), _y(_t-_d(days=1)))    # 최근 5일 -> 그중 가장 최근 조사일
BL=(_y(_t-_d(days=12)), _y(_t-_d(days=8)))   # 약 1주일 전
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
  ('4301','소','500'),
  ('4304','돼지','500'),
  ('4401','수입 소고기','500'),
  ('4402','수입 돼지고기','500'),
  ('512','쇠고기','500'),
  ('514','돼지고기','500'),
  ('515','닭고기','500'),
  ('516','계란','500'),
  ('520','오리고기','500'),
  ('535','우유','500'),
  ('9901','닭','500'),
  ('9903','계란','500'),
  ('9908','우유','500'),
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
URL="https://apis.data.go.kr/B552845/perDay/price"
def fetch(item,ctgry,s,e):
    q={"serviceKey":KEY,"returnType":"JSON","numOfRows":"2000","cond[se_cd::EQ]":"01",
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
def latest_by_region(js):
    # {sgg_cd: {"name":sgg_nm, "v": {(vc,vn): {"date","p":[],"unit"}}}}
    out={}
    for it in rows(js):
        sgg=it.get("sgg_cd"); 
        if not sgg: continue
        try: p=float(it.get("exmn_dd_prc"))
        except Exception: continue
        dt=str(it.get("exmn_ymd") or "")
        reg=out.setdefault(sgg, {"name":it.get("sgg_nm") or sgg, "v":{}})
        k=(it.get("vrty_cd"), it.get("vrty_nm") or "")
        g=reg["v"].get(k)
        if g is None or dt> g["date"]:
            reg["v"][k]={"date":dt,"p":[p],"unit":(str(it.get("unit_sz") or "")+str(it.get("unit") or ""))}
        elif dt==g["date"]:
            g["p"].append(p)
    return out
def avg(a): return int(sum(a)/len(a)) if a else None

byRegion={}      # sgg_cd -> list of item dicts
region_names={}  # sgg_cd -> name
for code,name,ctgry in ITEMS:
    tw=latest_by_region(fetch(code,ctgry,*TW))
    bl=latest_by_region(fetch(code,ctgry,*BL))
    for sgg,reg in tw.items():
        region_names[sgg]=reg["name"]
        blv=bl.get(sgg,{}).get("v",{})
        for k,g in reg["v"].items():
            now=avg(g["p"])
            if now is None: continue
            b=blv.get(k); base=avg(b["p"]) if b else None
            pct=int((now-base)/base*100) if base else None
            vn=k[1]
            if vn and vn!=name: label = vn if (name in vn) else f"{name} {vn}"
            else: label = name
            byRegion.setdefault(sgg,[]).append(
                {"code":f"{code}-{k[0]}","name":label,"price":now,"unit":g["unit"],
                 "base":base,"pct":pct,"asof":g["date"]})
    print(f"{name}: {sum(len(v['v']) for v in tw.values())}건 / 지역 {len(tw)}곳")

# 지역 목록: 항목 많은 순
regions=sorted(region_names.keys(), key=lambda s:-len(byRegion.get(s,[])))
data={"updated":_t.isoformat(),
      "regions":[{"code":s,"name":region_names[s]} for s in regions],
      "byRegion":byRegion}
open(OUT,"w",encoding="utf-8").write(json.dumps(data,ensure_ascii=False,indent=1))
open(os.path.join(PROJ,"data.js"),"w",encoding="utf-8").write(
    "window.PRICE_DATA = "+json.dumps(data,ensure_ascii=False)+";\n")
print(f"\n생성 완료: 지역 {len(regions)}곳 -> {OUT}")
