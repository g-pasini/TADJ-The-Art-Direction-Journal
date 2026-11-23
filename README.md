# TADJ · The Art Direction Journal

Jornal diário pessoal de design, direção de arte, vídeo e cultura visual.
Atualiza sozinho todo dia às 05:00 (Brasília), sem IA e sem custo.

## Como funciona

- `fontes.json`: lista de feeds RSS, cada um ligado a uma seção.
- `banco.json`: banco curado pequeno (clássico da semana, conceito, referência de base de cada região).
- `gerar.py`: lê os feeds, escolhe os itens sem repetir links já publicados, busca a obra do dia na API aberta do Met e grava `site/edicao.json`.
- `site/`: a página (HTML, CSS e JS). Lê `edicao.json`; edições antigas ficam em `site/edicoes/`.
- `.github/workflows/diario.yml`: roda o `gerar.py` todo dia e publica no GitHub Pages.

## Colocar no ar (uma vez)

1. Crie um repositório **público** no GitHub (ex.: `tadj`) e envie esta pasta.
2. No repositório: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Em **Actions → Edição diária → Run workflow**, gere a primeira edição.
4. A página fica em `https://SEU-USUARIO.github.io/tadj/`.

## Comandos úteis

```
python validar_fontes.py   # testa se as fontes ainda respondem
python gerar.py            # gera a edição localmente
python -m http.server 8765 --directory site   # abre em http://localhost:8765
```

## Atualizações com IA

Aumentar o banco curado ou criar edições especiais gasta tokens do Claude e
só deve ser feito com aprovação explícita do dono do projeto.
