import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT=Path(__file__).parent
SOURCE_STATUS=[]
KEYWORDS={'WTI Crude':['oil','crude','opec','inventory','supply','demand','petroleum','middle east'],'Brent Crude':['oil','crude','opec','inventory','supply','demand','petroleum','middle east'],'Gold':['gold','precious metal','federal reserve','fed','interest rate','yield','inflation','dollar','safe haven'],'Silver':['silver','precious metal','industrial demand','federal reserve','fed','interest rate'],'Copper':['copper','china','manufacturing','construction','industrial','property'],'Natural Gas':['natural gas','lng','storage','weather','power demand','pipeline'],'US Large Cap':['federal reserve','fed','interest rate','inflation','employment','gdp','tariff','recession'],'US Tech':['federal reserve','fed','interest rate','yield','technology','semiconductor','ai','inflation'],'US Industrials':['federal reserve','fed','manufacturing','industrial','gdp','employment','tariff'],'Shanghai Composite':['china','property','stimulus','pboc','manufacturing','consumer'],'Hang Seng':['china','property','stimulus','technology','regulation'],'Nikkei 225':['japan','boj','yen','inflation','export','semiconductor'],'KOSPI':['korea','bank of korea','semiconductor','export','china','manufacturing']}
def _text(node,tag): return ' '.join((node.findtext(tag) or '').split())
def _date(value):
    try: return parsedate_to_datetime(value).astimezone(timezone.utc)
    except Exception: return datetime.now(timezone.utc)
def fetch_articles():
    articles=[]; cutoff=datetime.now(timezone.utc)-timedelta(hours=36); SOURCE_STATUS.clear()
    for source in json.loads((ROOT/'news_sources.json').read_text(encoding='utf-8')):
        status={'name':source['name'],'url':source['url'],'status':'OK','error':''}
        try:
            with urlopen(Request(source['url'],headers={'User-Agent':'MarketBook/1.0'}),timeout=20) as response: root=ET.fromstring(response.read())
            for item in root.findall('.//item'):
                title=_text(item,'title'); link=_text(item,'link'); desc=_text(item,'description'); published=_date(_text(item,'pubDate'))
                if title and link and published>=cutoff: articles.append({'source':source['name'],'feed_url':source['url'],'title':title,'link':link,'description':desc,'published':published.isoformat()})
        except Exception as exc: status['status']='ERROR'; status['error']=str(exc); print(f'News warning ({source["name"]}): {exc}')
        SOURCE_STATUS.append(status)
    return list({a['link']:a for a in articles}.values())
def match_articles(asset_name,articles):
    keys=KEYWORDS.get(asset_name,[]); matches=[]
    for article in articles:
        hay=(article['title']+' '+article['description']).lower(); score=sum(1 for key in keys if key in hay)
        if score: matches.append((score,article))
    return [a for _,a in sorted(matches,key=lambda pair:(pair[0],pair[1]['published']),reverse=True)[:3]]
