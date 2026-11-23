"""Testa cada fonte de fontes.json e imprime uma linha por fonte (status, itens, último post)."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from feeds import baixar, ler

AQUI = Path(__file__).parent


def testar(f):
    try:
        itens = ler(baixar(f["url"]))
        datas = [i["data"] for i in itens if i["data"]]
        ultimo = max(datas) if datas else None
        dias = (datetime.now(timezone.utc) - ultimo).days if ultimo else None
        imgs = sum(1 for i in itens if i["imagem"])
        ok = bool(itens) and (dias is None or dias <= 60)
        return ok, f"{'OK ' if ok else 'VELHO'} {f['nome'][:24]:<24} itens={len(itens):<3} img={imgs:<3} ultimo={'?' if dias is None else str(dias)+'d'}"
    except Exception as e:
        return False, f"ERRO  {f['nome'][:24]:<24} {type(e).__name__}: {str(e)[:60]}"


if __name__ == "__main__":
    fontes = json.loads((AQUI / "fontes.json").read_text(encoding="utf-8"))
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(testar, fontes))
    for _, linha in res:
        print(linha)
    print(f"\n{sum(ok for ok, _ in res)}/{len(res)} fontes OK")
    sys.exit(0)
