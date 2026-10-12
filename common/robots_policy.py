"""Robots group selection, longest path match, wildcard and Allow tie precedence."""
import re
from urllib.parse import urlsplit
class RobotsPolicy:
    def __init__(self,text):
        self.groups=[];agents=[];rules=[];delay=0.;self.sitemaps=[];seen_rule=False
        def finish():
            if agents:self.groups.append((tuple(agents),tuple(rules),delay))
        for raw in text.splitlines():
            line=raw.split('#',1)[0].strip()
            if ':' not in line:continue
            k,v=(x.strip() for x in line.split(':',1));k=k.lower()
            if k=='sitemap':self.sitemaps.append(v);continue
            if k=='user-agent':
                if seen_rule:finish();agents=[];rules=[];delay=0.;seen_rule=False
                agents.append(v.lower())
            elif k in ('allow','disallow') and agents:
                seen_rule=True
                if v:rules.append((v,k=='allow'))
            elif k=='crawl-delay' and agents:
                seen_rule=True
                try:delay=max(0.,float(v))
                except ValueError:pass
        finish()
    def _groups(self,agent):
        agent=agent.lower();specific=[g for g in self.groups if any(a!='*' and a in agent for a in g[0])]
        if specific:
            length=max(len(a) for g in specific for a in g[0] if a!='*' and a in agent)
            return [g for g in specific if any(len(a)==length and a in agent for a in g[0])]
        return [g for g in self.groups if '*' in g[0]]
    def can_fetch(self,agent,url):
        p=urlsplit(url);target=p.path or '/'
        if p.query:target+='?'+p.query
        # Decode unreserved percent escapes only; reserved encoded '/' stays distinct.
        def norm(v):
            return re.sub(r'%([0-9a-fA-F]{2})',lambda m: chr(int(m[1],16)) if chr(int(m[1],16)) in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~' else m[0].upper(),v)
        matches=[]
        for _,rules,_ in self._groups(agent):
            for rule,allow in rules:
                end=rule.endswith('$');r=norm(rule[:-1] if end else rule)
                pattern='^'+'.*'.join(re.escape(x) for x in r.split('*'))+('$' if end else '')
                if re.search(pattern,norm(target)):matches.append((len(r.replace('*','')),allow))
        return max(matches)[1] if matches else True
    def crawl_delay(self,agent):return max((g[2] for g in self._groups(agent)),default=0.)
