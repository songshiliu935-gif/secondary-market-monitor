"""Fetch public Yahoo Finance chart data and build the daily Market Book."""
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
from pathlib import Path
from urllib.request import Request, urlopen
from io import StringIO
import csv
from urllib.parse import quote
import json, statistics
from news_matcher import fetch_articles, match_articles, SOURCE_STATUS

ROOT=Path(__file__).parent; OUT=ROOT/'data'/'market_book.json'; HISTORY=ROOT/'data'/'history'; OUT.parent.mkdir(exist_ok=True); HISTORY.mkdir(exist_ok=True)
ASSETS=[('US Large Cap','^GSPC','Index','US equities; growth and risk appetite'),('US Tech','^IXIC','Index','Technology, semiconductors and high-duration growth'),('US Industrials','^DJI','Index','Industrials, financials and cyclical demand'),('Shanghai Composite','000001.SS','Index','China domestic growth, property and consumer demand'),('Hang Seng','^HSI','Index','Hong Kong internet, China property and financials'),('Nikkei 225','^N225','Index','Japanese exporters, banks and domestic cyclicals'),('KOSPI','^KS11','Index','Korean semiconductors, exporters and cyclicals'),('WTI Crude','CL=F','Commodity','Energy producers; airlines, transport and chemicals'),('Brent Crude','BZ=F','Commodity','Energy producers; airlines, transport and chemicals'),('Gold','GC=F','Commodity','Gold miners; real yields, USD and defensive assets'),('Silver','SI=F','Commodity','Precious metals and industrial demand'),('Copper','HG=F','Commodity','Mining, construction, industrials and China demand'),('Natural Gas','NG=F','Commodity','Gas producers; utilities, chemicals and energy-intensive users'),('AUD/USD','AUDUSD=X','FX','Australian exporters, commodities and domestic risk appetite'),('US 2Y Treasury Yield','FRED:DGS2','Yield','Fed expectations, front-end rates and financial conditions'),('US 10Y Treasury Yield','FRED:DGS10','Yield','Long-term rates, duration assets, mortgages and banks'),('VIX','^VIX','Risk','Equity volatility and risk appetite'),('US Dollar Index','DX-Y.NYB','FX','Global dollar liquidity and emerging-market conditions'),('Technology','XLK','Sector','Growth, semiconductors and high-duration equities'),('Financials','XLF','Sector','Banks, brokers and insurers'),('Energy','XLE','Sector','Oil and gas producers'),('Industrials','XLI','Sector','Cyclicals, capital goods and transport'),('Materials','XLB','Sector','Mining, chemicals and raw materials'),('Healthcare','XLV','Sector','Defensive growth and healthcare services'),('Utilities','XLU','Sector','Defensive income and rate sensitivity'),('Real Estate','XLRE','Sector','Property and long-duration income assets'),('Consumer Discretionary','XLY','Sector','Household demand and growth sensitivity'),('Consumer Staples','XLP','Sector','Defensive consumption')]
CONTEXT={'WTI Crude':'supply risk, inventory data, OPEC+ policy and global demand','Brent Crude':'geopolitical supply risk, OPEC+ policy and global demand','Gold':'real yields, US dollar direction and safe-haven demand','Silver':'precious-metals flows and industrial demand','Copper':'China activity, construction demand and global manufacturing','Natural Gas':'weather, storage levels, LNG flows and power demand','Shanghai Composite':'China policy expectations, property data and domestic liquidity','Hang Seng':'China policy, property conditions and technology regulation','Nikkei 225':'yen direction, BOJ expectations and global technology demand','KOSPI':'semiconductor cycle, China demand and export conditions','CNY/USD':'China-US rate differentials, PBOC fixing and dollar direction','CNY/AUD':'China demand, commodity prices and the relative movement of the Australian dollar','AUD/USD':'commodity prices, China demand, RBA expectations and global risk appetite','US Dollar Index':'Fed expectations, US yields, global liquidity and safe-haven demand','VIX':'equity index volatility, hedging demand and risk appetite','US 2Y Treasury Yield':'near-term Fed policy expectations and incoming inflation or employment data','US 10Y Treasury Yield':'long-term growth and inflation expectations, fiscal supply and term premium','10Y–2Y Yield Spread':'the relative repricing of long-term growth/inflation risk versus near-term Fed policy','Technology':'long-duration growth, semiconductor demand and real yields','Financials':'yield-curve slope, credit conditions and economic growth','Energy':'oil and gas prices, inventories and supply discipline','Industrials':'manufacturing activity, capital spending and global growth','Materials':'metals prices, China demand and construction activity','Healthcare':'defensive demand, rates and healthcare policy','Utilities':'defensive demand, bond yields and income-seeking flows','Real Estate':'bond yields, financing conditions and property demand','Consumer Discretionary':'household demand, rates and consumer confidence','Consumer Staples':'defensive consumption, pricing power and input costs'}
def news_link(asset):
    return 'https://news.google.com/search?q='+quote(asset+' market news')+'&hl=en-US&gl=US&ceid=US%3Aen'
def source_metadata(name,ticker,kind):
    if ticker.startswith('FRED:'):
        series=ticker.split(':',1)[1]; return {'source_name':'FRED / Federal Reserve Bank of St. Louis','source_symbol':series,'source_urls':[f'https://fred.stlouisfed.org/series/{series}'],'data_status':'validated'}
    if ticker=='Derived':
        if name=='CNY/USD': return {'source_name':'Derived from Yahoo Finance CNY=X (inverted USD/CNY)','source_symbol':'CNY/USD','source_urls':['https://finance.yahoo.com/quote/CNY=X/'],'data_status':'derived'}
        if name=='CNY/AUD': return {'source_name':'Derived from Yahoo Finance CNY=X and AUDUSD=X','source_symbol':'CNY/AUD','source_urls':['https://finance.yahoo.com/quote/CNY=X/','https://finance.yahoo.com/quote/AUDUSD=X/'],'data_status':'derived'}
        if name=='10Y–2Y Yield Spread': return {'source_name':'Derived from FRED DGS10 minus DGS2','source_symbol':'DGS10-DGS2','source_urls':['https://fred.stlouisfed.org/series/DGS10','https://fred.stlouisfed.org/series/DGS2'],'data_status':'derived'}
    return {'source_name':'Yahoo Finance chart endpoint','source_symbol':ticker,'source_urls':[f'https://finance.yahoo.com/quote/{quote(ticker,safe="")}/'],'data_status':'validated'}
def specific_driver(name,change,z,assets):
    by={x['name']:x for x in assets}; get=lambda key: by.get(key)
    def move(key):
        x=get(key); return f"{x['name']} {x['change_pct']:+.2f}%" if x else f"{key} unavailable"
    if name=='VIX':
        return f"VIX rose {change:+.2f}% while {move('US Large Cap')}, {move('US Tech')} and {move('US Industrials')}; volatility therefore increased without a broad equity sell-off, pointing to hedging or event risk rather than a confirmed risk-off session"
    if name=='US Dollar Index':
        return f"the dollar gained {change:+.2f}% while {move('AUD/USD')} and {move('CNY/USD')}; this is consistent with firmer dollar demand, although the equity response was {move('US Large Cap')}"
    if name in ('CNY/USD','CNY/AUD'):
        return f"the derived {name} cross moved {change:+.2f}%; the move should be read through its components, including {move('US Dollar Index')}, {move('AUD/USD')} and {move('Shanghai Composite')}"
    if name in ('US 2Y Treasury Yield','US 10Y Treasury Yield'):
        return f"{name} moved {change:+.2f}% while {move('US Tech')}, {move('US Dollar Index')} and {move('VIX')}; this links the rate move to duration-sensitive equities, the dollar and hedging demand"
    if name=='10Y–2Y Yield Spread':
        return f"the spread changed {change:+.2f}% with {move('US 10Y Treasury Yield')} versus {move('US 2Y Treasury Yield')}; the curve signal is therefore driven more by the long end than by a repricing of near-term Fed expectations"
    if name in ('Gold','Silver'):
        return f"{name} moved {change:+.2f}% alongside {move('US Dollar Index')}, {move('US 10Y Treasury Yield')} and {move('VIX')}; the combination helps distinguish safe-haven demand from a pure real-yield or dollar move"
    if name in ('WTI Crude','Brent Crude','Natural Gas'):
        return f"{name} moved {change:+.2f}% versus {move('WTI Crude')}, {move('Brent Crude')} and {move('Energy')}; the relative move indicates whether the session was broad energy strength or concentrated in one contract"
    if name in ('Copper','Materials'):
        return f"{name} moved {change:+.2f}% while {move('Shanghai Composite')}, {move('Hang Seng')} and {move('Materials')}; this provides a direct read on China-sensitive industrial demand versus a broad materials move"
    if name in ('Shanghai Composite','Hang Seng','Nikkei 225','KOSPI'):
        return f"{name} moved {change:+.2f}% relative to {move('US Large Cap')}, {move('US Dollar Index')} and {move('Copper')}; the divergence points to regional rather than purely global risk drivers"
    if get(name) and get(name)['kind']=='Sector':
        benchmark=get('US Large Cap'); rel=change-benchmark['change_pct'] if benchmark else change
        return f"{name} moved {change:+.2f}%, {rel:+.2f} percentage points versus the S&P 500 proxy, while {move('US 10Y Treasury Yield')} and {move('VIX')} set the broader risk backdrop"
    return f"{name} moved {change:+.2f}% over the 60-day baseline; the nearest cross-asset checks are {move('US Large Cap')}, {move('US Dollar Index')} and {move('US 10Y Treasury Yield')}"
def fetch(ticker):
    url='https://query1.finance.yahoo.com/v8/finance/chart/'+ticker+'?range=6mo&interval=1d'; req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req,timeout=20) as r: raw=json.loads(r.read())
    return [v for v in raw['chart']['result'][0]['indicators']['quote'][0]['close'] if v is not None]
def fetch_fred(series):
    with urlopen(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}',timeout=20) as r: text=r.read().decode('utf-8')
    values=[]
    for row in csv.DictReader(StringIO(text)):
        try: values.append(float(row[series]))
        except (ValueError,TypeError,KeyError): pass
    return values[-180:]
def zscore(closes):
    returns=[(closes[i]/closes[i-1]-1)*100 for i in range(1,len(closes))]; window=returns[-61:]; today=window[-1]; hist=window[:-1]
    mean=statistics.mean(hist) if hist else 0; sd=statistics.stdev(hist) if len(hist)>1 else 0
    return today, ((today-mean)/sd if sd else 0)
def percentile(closes):
    returns=[abs((closes[i]/closes[i-1]-1)*100) for i in range(1,len(closes))]; window=returns[-61:]; today=window[-1]; hist=window[:-1]
    return round(100*sum(value<=today for value in hist)/len(hist),1) if hist else 0
def main():
    assets=[]; events=[]; articles=fetch_articles(); series={}; warnings=[]
    for name,ticker,kind,lens in ASSETS:
        try:
            closes=fetch_fred(ticker[5:]) if ticker.startswith('FRED:') else fetch(ticker)
            series[ticker]=closes; change,z=zscore(closes); close=closes[-1]; level='Major' if abs(z)>=3 else 'Significant' if abs(z)>=2 else 'Watchlist' if abs(z)>=1 else 'Normal'
            assets.append({'name':name,'ticker':ticker,'kind':kind,'close':round(close,4),'close_display':f'{close:,.2f}','change_pct':round(change,2),'z_score':round(z,2),'percentile':percentile(closes),'sparkline':[round(v,5) for v in closes[-60:]],'signal':level,'sector_lens':lens,**source_metadata(name,ticker,kind)})
            if level in ('Significant','Major','Watchlist'):
                direction='up' if change>0 else 'down'; drivers=specific_driver(name,change,z,assets)
                matched=match_articles(name,articles); evidence=[{'source':a['source'],'feed_url':a.get('feed_url',''),'title':a['title'],'link':a['link'],'published':a['published']} for a in matched]
                confidence='Likely' if evidence else 'Hypothesis'
                driver_text=f'{direction.capitalize()} {abs(change):.2f}% move, an unusually large move relative to the 60-day baseline (unusual-move score {abs(z):.2f}). {drivers}. ' + (('Related official-source items: ' + '; '.join(a['title'] for a in evidence)) if evidence else 'No matching official-source item was found in the last 36 hours; this remains a hypothesis rather than a confirmed catalyst.')
                if not evidence: evidence=[{'source':'News search','title':f'Search latest news about {name}','link':news_link(name),'published':''}]
                events.append({'asset':name,'change_pct':round(change,2),'level':level,'confidence':confidence,'drivers':driver_text,'sectors':lens,'evidence':evidence})
        except Exception as e: warnings.append(f'{name}: {e}'); print(f'Warning: {name}: {e}')
    try:
        cny_usd=[1/v for v in fetch('CNY=X') if v]; aud=series['AUDUSD=X']; n=min(len(cny_usd),len(aud)); cny_aud=[cny_usd[-n+i]/aud[-n+i] for i in range(n)]
        for name,closes,lens in [('CNY/USD',cny_usd,'China-US trade, PBOC policy and dollar direction'),('CNY/AUD',cny_aud,'China demand, commodity prices and Australian dollar direction')]:
            change,z=zscore(closes); close=closes[-1]; level='Major' if abs(z)>=3 else 'Significant' if abs(z)>=2 else 'Watchlist' if abs(z)>=1 else 'Normal'
            assets.append({'name':name,'ticker':'Derived','kind':'FX','close':round(close,6),'close_display':f'{close:,.4f}','change_pct':round(change,2),'z_score':round(z,2),'percentile':percentile(closes),'sparkline':[round(v,6) for v in closes[-60:]],'signal':level,'sector_lens':lens,**source_metadata(name,'Derived','FX')})
            if level in ('Significant','Major','Watchlist'):
                matched=match_articles(name,articles); evidence=[{'source':a['source'],'feed_url':a.get('feed_url',''),'title':a['title'],'link':a['link'],'published':a['published']} for a in matched]
                if not evidence: evidence=[{'source':'News search','title':f'Search latest news about {name}','link':news_link(name),'published':''}]
                events.append({'asset':name,'change_pct':round(change,2),'level':level,'confidence':'Likely' if matched else 'Hypothesis','drivers':('Up' if change>0 else 'Down')+f' {abs(change):.2f}% move, an unusually large move relative to the 60-day baseline (unusual-move score {abs(z):.2f}). '+specific_driver(name,change,z,assets)+(' Related official-source items: '+ '; '.join(a['title'] for a in matched) if matched else ' No matching official-source item was found in the last 36 hours.'),'sectors':lens,'evidence':evidence})
    except Exception as e: print(f'Warning: derived FX: {e}')
    try:
        y10=series['FRED:DGS10']; y2=series['FRED:DGS2']; n=min(len(y10),len(y2)); spread=[y10[-n+i]-y2[-n+i] for i in range(n)]
        change,z=zscore(spread); close=spread[-1]; level='Major' if abs(z)>=3 else 'Significant' if abs(z)>=2 else 'Watchlist' if abs(z)>=1 else 'Normal'
        assets.append({'name':'10Y–2Y Yield Spread','ticker':'Derived','kind':'Yield','close':round(close,2),'close_display':f'{close:.2f}%','change_pct':round(change,2),'z_score':round(z,2),'percentile':percentile(spread),'sparkline':[round(v,4) for v in spread[-60:]],'signal':level,'sector_lens':'Yield-curve slope; growth expectations, banks and recession risk',**source_metadata('10Y–2Y Yield Spread','Derived','Yield')})
    except Exception as e: print(f'Warning: yield spread: {e}')
    for event in events:
        asset=next((x for x in assets if x['name']==event['asset']),None)
        if asset:
            confirmed=any(evidence_item.get('source')!='News search' for evidence_item in event.get('evidence',[]))
            detail=specific_driver(event['asset'],asset['change_pct'],asset['z_score'],assets)
            evidence_text=(' Related official-source items: '+ '; '.join(item['title'] for item in event.get('evidence',[]) if item.get('source')!='News search')) if confirmed else ' No matching official-source item was found in the last 36 hours; this remains a hypothesis rather than a confirmed catalyst.'
            event['drivers']=('Up' if asset['change_pct']>0 else 'Down')+f' {abs(asset["change_pct"]):.2f}% move, an unusually large move relative to the 60-day baseline (unusual-move score {abs(asset["z_score"]):.2f}). '+detail+'.'+evidence_text
    gains=sum(x['change_pct']>0 for x in assets); losses=len(assets)-gains; regime='Risk-on' if gains>losses*1.5 else 'Risk-off' if losses>gains*1.5 else 'Mixed'
    indices=[x for x in assets if x['kind']=='Index']; commodities=[x for x in assets if x['kind']=='Commodity']; sectors=[x for x in assets if x['kind']=='Sector']; fx=[x for x in assets if x['kind']=='FX']; yields=[x for x in assets if x['kind']=='Yield']
    strongest=max(assets,key=lambda x:x['change_pct']); weakest=min(assets,key=lambda x:x['change_pct']); sector_best=max(sectors,key=lambda x:x['change_pct']) if sectors else None; sector_worst=min(sectors,key=lambda x:x['change_pct']) if sectors else None
    index_text=', '.join(f"{x['name']} {x['change_pct']:+.2f}%" for x in sorted(indices,key=lambda x:x['change_pct'],reverse=True)[:3]); commodity_text=', '.join(f"{x['name']} {x['change_pct']:+.2f}%" for x in sorted(commodities,key=lambda x:x['change_pct'],reverse=True)[:3]); fx_text=', '.join(f"{x['name']} {x['change_pct']:+.2f}%" for x in sorted(fx,key=lambda x:abs(x['change_pct']),reverse=True)[:2]); curve=next((x for x in assets if x['name']=='10Y–2Y Yield Spread'),None)
    idx_avg=sum(x['change_pct'] for x in indices)/len(indices) if indices else 0; vix=next((x for x in assets if x['name']=='VIX'),None); dxy=next((x for x in assets if x['name']=='US Dollar Index'),None); y10=next((x for x in assets if x['name']=='US 10Y Treasury Yield'),None); y2=next((x for x in assets if x['name']=='US 2Y Treasury Yield'),None)
    if idx_avg>0.25 and vix and vix['change_pct']>0: lead='Equities advanced, but the risk-on signal was not clean: investors added exposure while volatility and hedging demand also increased.'
    elif idx_avg>0.25 and (not vix or vix['change_pct']<=0): lead='The session showed a relatively clean risk-on pattern, with equity indices advancing while volatility remained contained.'
    elif idx_avg<-0.25 and vix and vix['change_pct']>0: lead='The market tone was risk-off, with equities weakening as volatility and demand for protection increased.'
    else: lead='The session was mixed, with cross-asset signals pointing to a market still searching for a clear macro direction.'
    y10_text=f"{y10['close_display']} ({y10['change_pct']:+.2f}% daily)" if y10 else 'unavailable'; y2_text=y2['close_display'] if y2 else 'unavailable'; dxy_text=f"{dxy['change_pct']:+.2f}%" if dxy else 'unavailable'; vix_text=f"{vix['change_pct']:+.2f}%" if vix else 'unavailable'
    oil=next((x for x in assets if x['name']=='Brent Crude'),None); wti=next((x for x in assets if x['name']=='WTI Crude'),None); gold=next((x for x in assets if x['name']=='Gold'),None); copper=next((x for x in assets if x['name']=='Copper'),None); gas=next((x for x in assets if x['name']=='Natural Gas'),None)
    oil_news=match_articles('Brent Crude',articles) if oil else []; geo_news=[a for a in oil_news if any(term in (a['title']+' '+a['description']).lower() for term in ('iran','hormuz','opec','middle east'))]; oil_headlines='; '.join(a['title'] for a in oil_news[:2]) if oil_news else 'No direct oil headline was matched in the monitored feeds.'; geo_headlines='; '.join(a['title'] for a in geo_news[:2]) if geo_news else 'No direct Iran, Strait of Hormuz, OPEC or Middle East headline was matched in the monitored feeds.'
    if oil and abs(oil['change_pct'])<0.75: oil_catalyst='With the oil move still contained, the next catalysts are EIA inventory data, OPEC+ supply guidance and any new U.S.–Iran or Strait of Hormuz developments.'
    else: oil_catalyst='The next confirmation points are EIA inventory data, OPEC+ supply guidance and whether U.S.–Iran or Strait of Hormuz headlines translate into a sustained supply-risk premium.'
    p1=f"Macro and commodities lead the story. Brent crude moved {oil['change_pct']:+.2f}% and WTI {wti['change_pct']:+.2f}%, while Gold moved {gold['change_pct']:+.2f}% and Copper {copper['change_pct']:+.2f}%; Natural Gas changed {gas['change_pct']:+.2f}%. The commodity tape therefore points to {'an energy-led inflation and supply-risk signal' if oil and oil['change_pct']>0.75 else 'limited outright commodity repricing, with the next move likely to depend on a catalyst'} rather than a broad, confirmed commodity shock."
    p2=f"The oil narrative is being monitored through supply and geopolitics. The closest matched feed items were: {oil_headlines}. Geopolitical evidence specifically related to Iran, the Strait of Hormuz, OPEC or the Middle East was: {geo_headlines} {oil_catalyst} This is the key distinction between a temporary futures move and a durable repricing of physical supply risk."
    asian_text=', '.join(f"{x['name']} {x['change_pct']:+.2f}%" for x in indices if x['name'] in ('Shanghai Composite','Hang Seng','Nikkei 225','KOSPI'))
    p3=f"That macro backdrop then transmits into indices. U.S. performance was {index_text}; Asian indices were {asian_text}. The dollar moved {dxy_text}, VIX {vix_text}, the 10Y yield was {y10_text}, the 2Y yield was {y2_text}, and the 10Y–2Y spread stood at {curve['close_display']}. The combination suggests that index moves were being filtered through rates, currency and regional growth sensitivity rather than driven by one uniform global risk signal."
    p4=f"Sector transmission was selective: {sector_best['name']} led at {sector_best['change_pct']:+.2f}% versus {sector_worst['name']} at {sector_worst['change_pct']:+.2f}%. Energy and Materials are the direct commodity beneficiaries, Industrials and Consumer Discretionary reflect growth sensitivity, while Utilities and Real Estate are being repriced through yields and income demand. The working market story is therefore a macro-to-market chain: commodity and geopolitical signals first, rates and FX second, then index and sector rotation. {len([e for e in events if e['level'] in ('Significant','Major')])} significant statistical moves require review; source links and confidence labels are shown in Event Radar."
    summary='\n\n'.join([p1,p2,p3,p4])
    now_utc=datetime.now(timezone.utc); as_of=now_utc.strftime('%Y-%m-%d %H:%M UTC'); sydney=now_utc.astimezone(ZoneInfo('Australia/Sydney')) if ZoneInfo else now_utc.astimezone(); updated_local=sydney.strftime('%Y-%m-%d %H:%M %Z'); market_close_date=now_utc.strftime('%Y-%m-%d'); expected=len(ASSETS)+3; news_errors=[x for x in SOURCE_STATUS if x['status']!='OK']; quality={'status':'OK' if not warnings and not news_errors and len(assets)>=expected else 'DEGRADED','assets_loaded':len(assets),'assets_expected':expected,'warnings':warnings+['News feed error: '+x['name'] for x in news_errors],'news_items_checked':len(articles),'news_feeds_ok':len(SOURCE_STATUS)-len(news_errors),'news_feeds_total':len(SOURCE_STATUS),'market_data_source':'Yahoo Finance chart endpoint','rates_source':'FRED DGS2/DGS10','news_source':'Federal Reserve, EIA and Google News RSS'}
    payload={'as_of':as_of,'updated_at_utc':as_of,'updated_at_local':updated_local,'market_close_date':market_close_date,'regime':regime,'summary':summary,'source':'Yahoo Finance + FRED (DGS2/DGS10) · official RSS: Federal Reserve and EIA','assets':assets,'events':sorted(events,key=lambda x:abs(x['change_pct']),reverse=True),'news_checked':len(articles),'news_sources':SOURCE_STATUS,'data_quality':quality}
    OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); (HISTORY/(datetime.now(timezone.utc).strftime('%Y-%m-%d')+'.json')).write_text(json.dumps(payload,indent=2),encoding='utf-8'); print('Market book written successfully.')
if __name__=='__main__': main()
