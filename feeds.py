"""Leitura de feeds RSS/Atom só com a biblioteca padrão do Python."""
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

UA = "Mozilla/5.0 (compatible; TADJ/1.0; leitor de RSS pessoal)"
NS = {"atom": "http://www.w3.org/2005/Atom", "content": "http://purl.org/rss/1.0/modules/content/",
      "media": "http://search.yahoo.com/mrss/", "dc": "http://purl.org/dc/elements/1.1/"}


def baixar(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def limpar(texto, limite=None):
    """Remove HTML e espaços extras; corta no limite de caracteres sem quebrar palavra."""
    t = re.sub(r"<[^>]+>", " ", texto or "")
    t = html.unescape(re.sub(r"\s+", " ", t)).strip()
    if limite and len(t) > limite:
        t = t[:limite].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return t


def _data(txt):
    if not txt:
        return None
    txt = txt.strip()
    try:
        d = parsedate_to_datetime(txt)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _imagem(el, corpo_html):
    for tag in ("media:content", "media:thumbnail"):
        m = el.find(tag, NS)
        if m is not None and m.get("url"):
            return m.get("url")
    enc = el.find("enclosure")
    if enc is not None and (enc.get("type") or "").startswith("image"):
        return enc.get("url")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', corpo_html or "")
    return m.group(1) if m else None


def ler(xml_bytes):
    """Devolve lista de dicts: titulo, link, data, resumo, imagem."""
    try:
        raiz = ET.fromstring(xml_bytes)
    except ET.ParseError:
        # Feeds mal formados: escapa "&" soltos e remove caracteres de controle, depois tenta de novo.
        t = xml_bytes.decode("utf-8", "replace")
        t = re.sub(r"&(?!#?\w+;)", "&amp;", t)
        t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", t)
        raiz = ET.fromstring(t.encode("utf-8"))
    itens = []
    if raiz.tag.endswith("feed"):  # Atom
        for e in raiz.findall("atom:entry", NS):
            link = e.find("atom:link[@rel='alternate']", NS)
            if link is None:
                link = e.find("atom:link", NS)
            corpo = (e.findtext("atom:content", "", NS) or e.findtext("atom:summary", "", NS))
            itens.append({
                "titulo": limpar(e.findtext("atom:title", "", NS)),
                "link": link.get("href") if link is not None else "",
                "data": _data(e.findtext("atom:published", "", NS) or e.findtext("atom:updated", "", NS)),
                "resumo_html": corpo, "imagem": _imagem(e, corpo)})
    else:  # RSS 2.0 / RDF
        for e in raiz.iter("item"):
            corpo = e.findtext("content:encoded", "", NS) or e.findtext("description", "")
            itens.append({
                "titulo": limpar(e.findtext("title", "")),
                "link": (e.findtext("link", "") or "").strip(),
                "data": _data(e.findtext("pubDate", "") or e.findtext("dc:date", "", NS)),
                "resumo_html": corpo, "imagem": _imagem(e, corpo)})
    return itens
