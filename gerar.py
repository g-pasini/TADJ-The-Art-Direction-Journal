"""Gera a edição do dia (site/edicao.json) a partir dos feeds, do banco curado e da API do Met.
Não usa IA nem gasta tokens. Roda todo dia pelo GitHub Actions ou à mão: python gerar.py
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from feeds import UA, baixar, ler, limpar

AQUI = Path(__file__).parent
SITE = AQUI / "site"
HIST = AQUI / "dados" / "historico.json"
BRT = timezone(timedelta(hours=-3))  # Brasília, sem horário de verão

# Quantos itens por seção e idade máxima (dias) para contar como novidade
COTAS = {"noticias": (9, 3), "referencias": (4, 10), "biblioteca": (3, 21), "bolhas": (4, 10)}
DIAS = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def coletar(fonte):
    try:
        return fonte, ler(baixar(fonte["url"]))
    except Exception as e:  # uma fonte fora do ar não derruba a edição
        print(f"  aviso: {fonte['nome']} falhou ({type(e).__name__})")
        return fonte, []


def minutos(corpo_html):
    palavras = len(limpar(corpo_html).split())
    return max(2, min(20, round(palavras / 200))) if palavras > 250 else 4


def escolher(candidatos, n):
    """Ordena por data e alterna entre fontes, para a seção não ficar dominada por um site só."""
    por_fonte = {}
    for c in sorted(candidatos, key=lambda c: c["_data"], reverse=True):
        por_fonte.setdefault(c["fonte"], []).append(c)
    filas, saida = list(por_fonte.values()), []
    while filas and len(saida) < n:
        for f in list(filas):
            if f:
                saida.append(f.pop(0))
            if not f:
                filas.remove(f)
            if len(saida) >= n:
                break
    return saida


def obra_do_dia(hoje):
    base = "https://collectionapi.metmuseum.org/public/collection/v1.1"
    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    try:
        ids = get(f"{base}/search?isHighlight=true&hasImages=true&q=*")["objectIDs"]
        n = hoje.toordinal() * 7919
        for k in range(15):
            o = get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{ids[(n + k) % len(ids)]}")
            if o.get("isPublicDomain") and o.get("primaryImage"):
                return {"titulo": o.get("title"), "autor": o.get("artistDisplayName") or o.get("culture") or "Autoria desconhecida",
                        "ano": o.get("objectDate"), "tecnica": o.get("medium"), "acervo": "The Met · domínio público",
                        "imagem": o.get("primaryImageSmall") or o.get("primaryImage"), "imagem_grande": o.get("primaryImage"),
                        "url": o.get("objectURL"), "departamento": o.get("department")}
    except Exception as e:
        print(f"  aviso: obra do dia falhou ({type(e).__name__})")
    return None


def main():
    agora = datetime.now(BRT)
    hoje = agora.date()
    dia = hoje.weekday()
    semana = hoje.isocalendar().week

    fontes = json.loads((AQUI / "fontes.json").read_text(encoding="utf-8"))
    banco = json.loads((AQUI / "banco.json").read_text(encoding="utf-8"))
    historico = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else []
    vistos = set(historico)

    with ThreadPoolExecutor(10) as ex:
        resultados = list(ex.map(coletar, fontes))

    secoes = {s: [] for s in COTAS}
    for fonte, itens in resultados:
        _, idade = COTAS[fonte["secao"]]
        for it in itens:
            if not it["link"] or not it["titulo"] or it["link"] in vistos:
                continue
            d = it["data"] or datetime(1970, 1, 1, tzinfo=timezone.utc)
            if not fonte.get("atemporal") and (agora - d).days > idade:
                continue
            secoes[fonte["secao"]].append({
                "titulo": it["titulo"], "url": it["link"], "fonte": fonte["nome"], "tag": fonte["tag"],
                "resumo": limpar(it["resumo_html"], 220), "trecho": limpar(it["resumo_html"], 900),
                "imagem": it["imagem"], "min": minutos(it["resumo_html"]),
                "data": d.astimezone(BRT).strftime("%d/%m/%Y") if it["data"] else "", "_data": d,
                "atemporal": bool(fonte.get("atemporal")), "tema": fonte.get("tema")})

    edicao_secoes = {}
    for s, (n, _) in COTAS.items():
        cand = secoes[s]
        if s == "referencias":  # vitrine: prioriza itens com imagem
            com_img = [c for c in cand if c["imagem"]]
            cand = com_img if len(com_img) >= n else cand
        if s == "biblioteca":  # 1 artigo do tema do dia + ensaios novos + atemporais completando
            tema_hoje = banco["temas"][min(dia, 5)]["tema"]
            do_tema = [c for c in cand if c["tema"] == tema_hoje]
            escolha = escolher(do_tema, 1)
            novos = [c for c in cand if not c["atemporal"] and c not in escolha]
            escolha += escolher(novos, n - 1)
            resto = [c for c in cand if c["atemporal"] and c not in escolha]
            escolha += escolher(resto, n - len(escolha))
        else:
            escolha = escolher(cand, n)
        for i, c in enumerate(escolha):
            c.pop("_data", None)
            c["id"] = f"{hoje.isoformat()}-{s[0]}{i}"
        edicao_secoes[s] = escolha

    tema = banco["temas"][min(dia, 5)]
    regiao = banco["regioes"][semana % len(banco["regioes"])]
    noticias = edicao_secoes["noticias"]
    edicao = {
        "data_iso": hoje.isoformat(),
        "data": f"{DIAS[dia]}, {hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}",
        "numero": (hoje - datetime(2026, 11, 18).date()).days + 1,
        "gerado": agora.strftime("%H:%M"),
        "fontes_ativas": sum(1 for _, itens in resultados if itens), "fontes_total": len(fontes),
        "dia_semana": min(dia, 5),
        "temas": [t["dia"] + " · " + t["tema"] for t in banco["temas"]],
        "regioes": [r["regiao"] for r in banco["regioes"]],
        "regiao_idx": banco["regioes"].index(regiao),
        "inspiracao": obra_do_dia(hoje),
        "manchete": next((n for n in noticias if n["imagem"]), noticias[0]) if noticias else None,
        "tema": tema["tema"],
        "classico": tema["classicos"][semana % len(tema["classicos"])],
        "conceito": tema["conceitos"][semana % len(tema["conceitos"])],
        "bolha_base": regiao,
    }
    if edicao["manchete"]:
        noticias.remove(edicao["manchete"])
    edicao.update(edicao_secoes)

    # Salva edição, arquivo e histórico de links (para não repetir nos próximos dias)
    (SITE / "edicoes").mkdir(parents=True, exist_ok=True)
    texto = json.dumps(edicao, ensure_ascii=False, indent=1)
    (SITE / "edicao.json").write_text(texto, encoding="utf-8")
    (SITE / "edicoes" / f"{hoje.isoformat()}.json").write_text(texto, encoding="utf-8")
    arquivo = sorted({p.stem for p in (SITE / "edicoes").glob("*.json")}, reverse=True)
    (SITE / "arquivo.json").write_text(json.dumps(arquivo), encoding="utf-8")

    usados = [it["url"] for s in COTAS for it in edicao_secoes[s]] + ([edicao["manchete"]["url"]] if edicao["manchete"] else [])
    HIST.parent.mkdir(exist_ok=True)
    HIST.write_text(json.dumps((historico + [u for u in usados if u not in vistos])[-3000:], ensure_ascii=False), encoding="utf-8")

    contagem = ", ".join(f"{s}={len(edicao_secoes[s])}" for s in COTAS)
    print(f"Edição {edicao['data']} gerada: {contagem}, obra={'ok' if edicao['inspiracao'] else 'sem'}, "
          f"fontes {edicao['fontes_ativas']}/{edicao['fontes_total']}")


if __name__ == "__main__":
    main()
