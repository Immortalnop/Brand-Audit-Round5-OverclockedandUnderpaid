"""Robots group selection, longest path match, wildcard and Allow tie precedence.

Group selection matches the PRODUCT TOKEN exactly (RFC 9309 2.2.1: the token is
compared case-insensitively, and a crawler uses the record whose token is its
own, or the "*" record). It deliberately does not do substring or prefix
matching, which is what made a `User-agent: Applebot` group apply to
Applebot-Extended: two different tokens, with two different purposes -- search
access and AI training data -- and a site that blocks one has not said anything
about the other. Collapsing them turns a purpose-specific policy question into a
wrong answer about the site.

Where a vendor documents that one of its tokens inherits another's rules (Google
says Googlebot-News and Googlebot-Image follow the Googlebot group when they have
no group of their own), that is a per-vendor fact, not a string rule, and belongs
in an explicit table rather than in the matcher. None of the tokens this audit
evaluates needs one, so the table is empty and any inheritance a caller wants
has to be stated.
"""
import re
from urllib.parse import urlsplit

# Vendor-documented token inheritance: {token: fallback token}. Empty by design;
# see the module docstring.
TOKEN_FALLBACKS = {}


def product_token(agent):
    """The product token of a user-agent string, lowercased (RFC 9309 2.2.1).

    'Applebot-Extended' -> 'applebot-extended'
    'BrandAIReadinessAuditBot/2.0 (read-only audit)' -> 'brandaireadinessauditbot'
    """
    value=(agent or '').strip().lower()
    value=value.split('(',1)[0].strip()
    value=value.split('/',1)[0].strip()
    return value.split()[0] if value.split() else ''
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
        """Every group whose product token is this agent's, or the '*' groups when
        it has none of its own. Exact token match, never substring."""
        token=product_token(agent)
        for candidate in (token,TOKEN_FALLBACKS.get(token)):
            if not candidate:continue
            specific=[g for g in self.groups if any(product_token(a)==candidate for a in g[0] if a!='*')]
            if specific:return specific
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
