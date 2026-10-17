"""Fetch, filter and snapshot Cardano/Midnight headlines."""
from __future__ import annotations
import hashlib,json,re
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/data/news.json'
FEEDS=[('official','cardano','Cardano Foundation','https://cardanofoundation.org/feed/'),('official','midnight','Midnight Foundation','https://midnight.foundation/feed/'),('official','midnight','Midnight Network','https://midnight.network/feed/'),('media','cardano','Google News · Cardano','https://news.google.com/rss/search?q=Cardano+ADA+blockchain&hl=en-US&gl=US&ceid=US:en'),('media','midnight','Google News · Midnight','https://news.google.com/rss/search?q=Midnight+NIGHT+token+blockchain&hl=en-US&gl=US&ceid=US:en')]
def tx(e,tag):
    x=e.find(tag);return (x.text or '').strip() if x is not None else ''
def clean(s):return re.sub(r'<[^>]+>|\s+',' ',s or '').strip()
def main():
    records=[]
    for typ,topic,source,url in FEEDS:
        try:
            root=ET.fromstring(urlopen(Request(url,headers={'User-Agent':'CardanoNightNews/1.0'}),timeout=15).read())
        except Exception as e: print('skip',url,e);continue
        for item in root.findall('.//item')[:12]:
            title=clean(tx(item,'title'));link=tx(item,'link');date=tx(item,'pubDate');blob=(title+' '+clean(tx(item,'description'))).lower()
            if topic=='midnight' and 'midnight' not in blob:continue
            if not title or not link:continue
            try:d=parsedate_to_datetime(date).date().isoformat()
            except Exception:d=datetime.now(timezone.utc).date().isoformat()
            uid=hashlib.sha1((title.lower()+'|'+link.split('?')[0]).encode()).hexdigest()[:12]
            records.append({'id':uid,'topic':topic,'type':typ,'date':d,'source':source,'title_en':title,'title_zh':title,'summary_en':clean(tx(item,'description'))[:240],'summary_zh':'原文摘要（中文待人工复核）','url':link})
    old=json.loads(OUT.read_text()) if OUT.exists() else {'items':[]};merged={n.get('id') or hashlib.sha1(n['url'].encode()).hexdigest()[:12]:n for n in old.get('items',[])}
    for n in records:merged[n['id']]=n
    payload={'meta':{'updated_at':datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z'),'method':'RSS + Midnight-bound keyword filter + URL/title SHA-1 dedupe','note':'价格与观点类内容仅作报道，不等于事实确认或投资建议'},'items':sorted(merged.values(),key=lambda x:x.get('date',''),reverse=True)[:60]}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
