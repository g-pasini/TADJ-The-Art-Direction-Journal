const tc = m => "00:" + String(m).padStart(2, "0") + ":00";
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const $ = id => document.getElementById(id);
const sum = arr => (arr || []).reduce((a, b) => a + (b.min || 0), 0);
const safeUrl = u => /^https?:\/\//i.test(u || "") ? u : "";

let salvos = new Set();
try { salvos = new Set(JSON.parse(localStorage.getItem("tadj-salvos") || "[]")); } catch (e) {}
const persist = () => { try { localStorage.setItem("tadj-salvos", JSON.stringify([...salvos])); } catch (e) {} };

// Salvos guardam o item inteiro, para continuarem acessíveis em edições futuras
let salvosItens = {};
try { salvosItens = JSON.parse(localStorage.getItem("tadj-salvos-itens") || "{}"); } catch (e) {}
const persistItens = () => { try { localStorage.setItem("tadj-salvos-itens", JSON.stringify(salvosItens)); } catch (e) {} };
const porId = {};

function img(url, alt, label) {
  const u = safeUrl(url);
  return `<div class="ph${u ? " loaded" : ""}">${u ? `<img src="${esc(u)}" alt="${esc(alt)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove();this.parentNode.classList.remove('loaded')">` : ""}<span class="caps">${esc(label)}</span></div>`;
}
function deep(it) {
  let h = "";
  if (it.trecho && it.trecho !== it.resumo) h += `<h4 class="caps">Trecho da fonte</h4><p>${esc(it.trecho)}</p>`;
  if (it.data) h += `<div class="terms caps"><span>Publicado em ${esc(it.data)}</span></div>`;
  const u = safeUrl(it.url);
  if (u) h += `<a class="src-link" href="${esc(u)}" target="_blank" rel="noopener">Ler na fonte ↗</a>`;
  return `<details><summary>Aprofundar</summary><div class="deep">${h}</div></details>`;
}
function saveBtn(id) {
  const on = salvos.has(id);
  return `<button type="button" class="save" data-save="${esc(id)}" aria-pressed="${on}">${on ? "Salvo" : "Salvar"}</button>`;
}
function body(it) {
  porId[it.id] = it;
  return `<div class="item-top caps"><span class="tag">${esc(it.tag)}</span>${saveBtn(it.id)}</div>
    <h3>${esc(it.titulo)}</h3>
    ${it.resumo ? `<p class="resumo">${esc(it.resumo)}</p>` : ""}
    <div class="meta"><span class="caps">${esc(it.fonte)}</span><span class="mono">TC ${tc(it.min || 3)}</span></div>
    ${deep(it)}`;
}
const item = (it, comImg) => `<article class="item" data-id="${esc(it.id)}">${comImg ? img(it.imagem, it.titulo, "Imagem") : ""}${body(it)}</article>`;
const vazio = txt => `<p class="empty-note">${esc(txt)}</p>`;

function render(E) {
  $("ed-num").textContent = "Edição " + String(E.numero).padStart(3, "0");
  $("ed-date").textContent = E.data;
  const listas = [E.noticias, E.referencias, E.biblioteca, E.bolhas];
  const total = (E.manchete?.min || 0) + listas.reduce((a, l) => a + sum(l), 0) + 8;
  $("ed-total").textContent = "Leitura completa TC " + tc(Math.min(total, 59));
  $("ft-fontes").textContent = `${E.fontes_ativas} de ${E.fontes_total} fontes responderam hoje (gerado às ${E.gerado}).`;

  const f = E.inspiracao;
  if (f) {
    $("hero").innerHTML = `${img(f.imagem, f.titulo, "Obra do dia")}
      <div class="hero-text">
        <span class="caps" style="color:var(--muted)">Obra de inspiração</span>
        <h1>${esc(f.titulo)}</h1>
        <dl class="caps"><dt>Autor</dt><dd>${esc(f.autor)}</dd><dt>Data</dt><dd>${esc(f.ano)}</dd><dt>Técnica</dt><dd>${esc(f.tecnica)}</dd><dt>Acervo</dt><dd>${esc(f.acervo)}</dd></dl>
        ${safeUrl(f.url) ? `<a class="src-link" href="${esc(f.url)}" target="_blank" rel="noopener">Ver no acervo ↗</a>` : ""}
      </div>`;
  } else $("hero").hidden = true;

  const m = E.manchete;
  if (m) $("lead").innerHTML = `${img(m.imagem, m.titulo, "Imagem da matéria")}<div class="item" data-id="${esc(m.id)}">${body(m)}</div>`;
  else $("lead").hidden = true;
  $("list-noticias").innerHTML = (E.noticias || []).map(i => item(i, false)).join("") || vazio("Nenhuma notícia nova hoje.");
  $("tc-noticias").textContent = ((E.noticias || []).length + (m ? 1 : 0)) + " notas · TC " + tc(sum(E.noticias) + (m?.min || 0));

  $("list-referencias").innerHTML = (E.referencias || []).map(i => item(i, true)).join("") || vazio("Nenhuma referência nova hoje.");
  $("tc-referencias").textContent = (E.referencias || []).length + " itens · TC " + tc(sum(E.referencias));

  $("week-temas").innerHTML = E.temas.map((t, i) => `<span class="${i === E.dia_semana ? "on" : ""}">${esc(t)}</span>`).join("");
  $("lede-biblioteca").textContent = "Hoje: " + E.tema.toLowerCase() + ".";
  const c = E.classico, k = E.conceito;
  $("classic").innerHTML = `<div><span class="caps tag">Clássico da semana</span><h3>${esc(c.obra)}</h3>
      <span class="caps" style="color:var(--muted)">${esc(c.autor)} · ${esc(c.ano)}</span><p>${esc(c.porque)}</p></div>
    <div><span class="caps tag">Conceito · ${esc(k.nome)}</span><blockquote>${esc(k.texto)}</blockquote></div>`;
  $("list-biblioteca").innerHTML = (E.biblioteca || []).map(i => item(i, false)).join("") || vazio("Nenhuma leitura nova hoje.");
  $("tc-biblioteca").textContent = (E.biblioteca || []).length + " leituras · TC " + tc(sum(E.biblioteca));

  $("week-regioes").innerHTML = E.regioes.map((r, i) => `<span class="${i === E.regiao_idx ? "on" : ""}">${esc(r)}</span>`).join("");
  const b = E.bolha_base;
  $("lede-bolhas").textContent = "Esta semana: " + b.regiao.toLowerCase() + ".";
  $("bolha-base").innerHTML = `<div><span class="caps tag">Referência de base</span><h3>${esc(b.nome)}</h3>
      <span class="caps" style="color:var(--muted)">${esc(b.origem)}</span><p>${esc(b.texto)}</p></div>
    <div><span class="caps tag">Para guardar</span><blockquote>${esc(b.guardar)}</blockquote></div>`;
  $("list-bolhas").innerHTML = (E.bolhas || []).map(i => item(i, true)).join("") || vazio("Nada novo de outras bolhas hoje.");
  $("tc-bolhas").textContent = (E.bolhas || []).length + " notas · TC " + tc(sum(E.bolhas));

  $("saved-count").textContent = salvos.size;
}

let onlySaved = false;
function applyFilter() {
  document.querySelectorAll("[data-id]").forEach(el => el.hidden = onlySaved && !salvos.has(el.dataset.id));
  ["hero", "classic", "bolha-base", "week-temas", "week-regioes"].forEach(id => $(id).hidden = onlySaved);
  $("lead").querySelector(".ph")?.toggleAttribute("hidden", onlySaved);
  let antigos = $("salvos-antigos");
  if (onlySaved) {
    const fora = [...salvos].filter(id => !document.querySelector(`[data-id="${CSS.escape(id)}"]`) && salvosItens[id]);
    if (!antigos) { antigos = document.createElement("section"); antigos.id = "salvos-antigos"; antigos.style.setProperty("--plate", "var(--ink)"); $("inicio").appendChild(antigos); }
    antigos.innerHTML = `<div class="sec-head"><h2><i class="dot"></i>Salvos de outras edições</h2></div><div class="grid">${fora.map(id => item(salvosItens[id], false)).join("") || vazio("Nenhum.")}</div>`;
    antigos.hidden = false;
  } else if (antigos) antigos.hidden = true;
}

document.addEventListener("click", e => {
  const b = e.target.closest("[data-save]");
  if (!b) return;
  const id = b.dataset.save;
  if (salvos.has(id)) { salvos.delete(id); delete salvosItens[id]; }
  else { salvos.add(id); if (porId[id]) salvosItens[id] = porId[id]; }
  persist(); persistItens();
  document.querySelectorAll(`[data-save="${CSS.escape(id)}"]`).forEach(x => { x.setAttribute("aria-pressed", salvos.has(id)); x.textContent = salvos.has(id) ? "Salvo" : "Salvar"; });
  $("saved-count").textContent = salvos.size;
  if (onlySaved) applyFilter();
});
document.addEventListener("toggle", e => {
  if (e.target.tagName === "DETAILS" && e.target.open) e.target.closest("[data-id]")?.classList.add("read");
}, true);
$("only-saved").addEventListener("click", e => {
  onlySaved = !onlySaved;
  e.currentTarget.setAttribute("aria-pressed", onlySaved);
  applyFilter();
});

async function iniciar() {
  const d = new URLSearchParams(location.search).get("d");
  const arquivo = d && /^\d{4}-\d{2}-\d{2}$/.test(d) ? `edicoes/${d}.json` : "edicao.json";
  try {
    const E = await (await fetch(arquivo, { cache: "no-cache" })).json();
    render(E);
    const lista = await (await fetch("arquivo.json", { cache: "no-cache" })).json();
    $("archive").innerHTML = lista.slice(0, 21).map(x => {
      const [a, mes, dia] = x.split("-");
      return `<a class="mono" href="?d=${x}"${x === E.data_iso ? ' aria-current="page"' : ""}>${dia}/${mes}</a>`;
    }).join("");
  } catch (err) {
    $("ed-date").textContent = "Não foi possível carregar a edição. Tente recarregar a página.";
  }
}
iniciar();
