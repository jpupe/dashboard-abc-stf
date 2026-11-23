# -*- coding: utf-8 -*-
"""
Painel das Decisões do STF em Direito Minerário — Índice A/B/C
================================================================
Output 5 do projeto de tese de Suzy Sousa (UFPA): ETL + dashboard em Streamlit.

O painel lê SOMENTE o banco final (output 2, banco_ABC_STF_mineracao.xlsx,
aba "Banco", formato longo: uma linha por resposta do questionário). O arquivo
data/brasil_ufs.geojson contém só o contorno dos estados, usado para desenhar o mapa.

Rodar localmente:
    pip install -r requirements.txt
    streamlit run app.py

Publicar de graça (Streamlit Community Cloud):
    1. Suba esta pasta para um repositório no GitHub (com data/banco_ABC_STF_mineracao.xlsx).
    2. Em https://share.streamlit.io clique em "Create app", escolha o repositório,
       a branch "main" e o arquivo "app.py". O link gerado (…streamlit.app) é o que a banca abre.
    3. Para atualizar o painel depois da validação, substitua o Excel em data/ e faça commit.

ETL:
    Extração   → lê a aba "Banco" do Excel (caminho em CAMINHO_EXCEL).
    Transformação → separa decisões e núcleos; monta a visão longa núcleo × princípio a partir
                 dos códigos de pergunta (IN_/FSP_/MA_); mantém os marcadores de dados como
                 categoria própria (não são descartados); lê as colunas de validação da pesquisadora.
    Carga      → dados em memória com st.cache_data.
"""
import html
import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------- configuração
CAMINHO_EXCEL = Path(__file__).parent / "data" / "banco_ABC_STF_mineracao.xlsx"
CAMINHO_MAPA = Path(__file__).parent / "data" / "brasil_ufs.geojson"   # contorno dos estados (só para o desenho do mapa)
ABA = "Banco"

st.set_page_config(page_title="Painel A/B/C — STF e Mineração", page_icon="⚖️", layout="wide")

PRINCIPIOS = {
    "IN": "Interesse nacional",
    "FSP": "Função social da propriedade",
    "MA": "Meio ambiente",
}
ARTIGOS = {"IN": "art. 176, § 1º", "FSP": "art. 170, III", "MA": "art. 225"}
MARCADORES = [
    "Não aplicável", "Informação não disponível ou não localizada",
    "Inconclusivo — evidência examinada insuficiente", "Campo aplicável ainda não preenchido",
    "Registro provisório pendente de conferência",
]

# Ordem e cores (paleta azul, como no painel de referência)
ORDEM_CONCR = [
    "Concretização institucional com critério potencialmente replicável", "Concretização no caso",
    "Fundamento determinante sem densificação", "Presença contextual/discursiva", "Não mobilizado", "Inconclusivo",
]
ROTULO_CONCR = {
    "Concretização institucional com critério potencialmente replicável": "Concretização institucional",
    "Concretização no caso": "Concretização no caso",
    "Fundamento determinante sem densificação": "Fundamento sem densificação",
    "Presença contextual/discursiva": "Presença contextual",
    "Não mobilizado": "Não mobilizado",
    "Inconclusivo": "Inconclusivo",
}
COR_CONCR = {
    "Concretização institucional": "#0B3C8C", "Concretização no caso": "#1F77D0",
    "Fundamento sem densificação": "#5DA9E9", "Presença contextual": "#A9D3F5",
    "Não mobilizado": "#D9DEE4", "Inconclusivo": "#F2B134",
}
ORDEM_POS = [
    "Fundamento determinante", "Relevante sem participação determinante", "Genérica/ornamental",
    "Voto não prevalecente", "Obstáculo processual/institucional", "Presença documental não judicial",
    "Ausente", "Inconclusivo",
]
COR_POS = dict(zip(ORDEM_POS, ["#0B3C8C", "#1F77D0", "#5DA9E9", "#8E7CC3", "#C27BA0",
                               "#B7C9DB", "#D9DEE4", "#F2B134"]))
ORDEM_FS = ["Função simbólica demonstrada", "Indícios", "Sem indicador suficiente", "Não aplicável", "Inconclusivo"]
COR_FS = dict(zip(ORDEM_FS, ["#B03A2E", "#E67E22", "#5DA9E9", "#D9DEE4", "#F2B134"]))
ORDEM_DENS = ["Densificação institucional com critério potencialmente replicável", "Densificação no caso/corrente",
              "Conteúdo não densificado", "Não aplicável", "Inconclusivo"]
ROT_DENS = {"Densificação institucional com critério potencialmente replicável": "Densificação institucional",
            "Densificação no caso/corrente": "Densificação no caso/corrente",
            "Conteúdo não densificado": "Conteúdo não densificado", "Não aplicável": "Não aplicável",
            "Inconclusivo": "Inconclusivo"}
COR_DENS = {"Densificação institucional": "#0B3C8C", "Densificação no caso/corrente": "#1F77D0",
            "Conteúdo não densificado": "#A9D3F5", "Não aplicável": "#D9DEE4", "Inconclusivo": "#F2B134"}

# Coordenadas aproximadas das capitais (para posicionar as decisões no mapa)
UF_COORD = {
    "Acre": (-9.97, -67.81), "Alagoas": (-9.67, -35.74), "Amapá": (0.03, -51.07), "Amazonas": (-3.12, -60.02),
    "Bahia": (-12.97, -38.50), "Ceará": (-3.73, -38.53), "Distrito Federal": (-15.79, -47.88),
    "Espírito Santo": (-20.32, -40.34), "Goiás": (-16.68, -49.25), "Maranhão": (-2.53, -44.30),
    "Mato Grosso": (-15.60, -56.10), "Mato Grosso do Sul": (-20.44, -54.65), "Minas Gerais": (-19.92, -43.94),
    "Pará": (-1.46, -48.50), "Paraíba": (-7.12, -34.86), "Paraná": (-25.43, -49.27), "Pernambuco": (-8.05, -34.88),
    "Piauí": (-5.09, -42.80), "Rio de Janeiro": (-22.91, -43.17), "Rio Grande do Norte": (-5.79, -35.21),
    "Rio Grande do Sul": (-30.03, -51.23), "Rondônia": (-8.76, -63.90), "Roraima": (2.82, -60.67),
    "Santa Catarina": (-27.59, -48.55), "São Paulo": (-23.55, -46.63), "Sergipe": (-10.91, -37.07),
    "Tocantins": (-10.18, -48.33),
}

# ------------------------------------------------------------------- estilo
st.markdown("""
<style>
.block-container {padding-top: 3rem; padding-bottom: 1rem;}
.faixa {background: linear-gradient(90deg, #1B2A6B 0%, #2D4FA3 45%, #1FA2C9 100%);
        color: white; padding: 18px 28px; border-radius: 4px; display:flex; align-items:center;
        justify-content:space-between; margin-bottom: 8px;}
.faixa .marca {font-size: 30px; font-weight: 800; letter-spacing: 1px; border-right: 1px solid rgba(255,255,255,.5);
        padding-right: 18px; margin-right: 18px; line-height: 1;}
.faixa .sub {font-size: 15px; line-height: 1.3;}
.faixa .sigla {font-size: 26px; font-weight: 700;}
.titulo-painel {font-size: 28px; color: #1E1E1E; margin: 6px 0 2px 0;}
.secao {font-size: 17px; color: #222; margin: 6px 0 4px 0; font-weight: 500;}
.secao-cinza {font-size: 17px; color: #B0B6BE; margin: 6px 0 4px 0; font-weight: 500;}
.caixa-scroll {max-height: 420px; overflow-y: auto; border: 1px solid #E3E7EC;}
.tab-resumo {width:100%; border-collapse: collapse; font-size: 13.5px;}
.tab-resumo th {text-align:left; padding:6px 8px; background:#FFFFFF; position: sticky; top: 0; font-weight:500;}
.tab-resumo td {vertical-align: top; padding: 6px 8px; color:#10233F;}
.tab-resumo tr:nth-child(odd) td {background: #9FCCF5;}
.tab-resumo tr:nth-child(even) td {background: #3D9BEA; color:#0B1A33;}
.tab-escura {width:100%; border-collapse: collapse; font-size: 13px;}
.tab-escura th {background:#1A1A1A; color:#fff; text-align:left; padding:8px; position: sticky; top: 0;
        border-bottom: 3px solid #3D9BEA;}
.tab-escura td {vertical-align: top; padding: 7px 8px; border-bottom: 1px solid #E5E5E5;}
.tab-escura tr:nth-child(even) td {background:#F2F2F2;}
.pag {color:#1F5FBF; text-decoration: underline;}
.palavras {text-align:center; font-size: 17px; line-height: 1.45; color:#111; padding: 30px 6px;}
.lista-rep {font-size: 13.5px; line-height: 1.35;}
.lista-rep div {padding: 6px 8px; border-bottom: 1px solid #E8E8E8;}
.lista-rep div:nth-child(even) {background:#EFEFEF;}
.selo {display:inline-block; padding:2px 8px; border-radius: 10px; font-size: 12px; background:#FFF2CC; color:#7F6000;}
.rodape {color:#6B7280; font-size: 12.5px; border-top: 1px solid #E5E7EB; margin-top: 18px; padding-top: 8px;}
</style>
""", unsafe_allow_html=True)


# ====================================================================== ETL
@st.cache_data(show_spinner="Carregando o banco de decisões…")
def carregar(caminho: str) -> pd.DataFrame:
    """Extração: lê a aba Banco como texto (preserva marcadores e categorias)."""
    df = pd.read_excel(caminho, sheet_name=ABA, dtype=str).fillna("")
    df["Núcleo"] = df["Núcleo"].str.replace(r"\.0$", "", regex=True)
    for c in ("Resposta", "Concorda?"):
        df[c] = df[c].str.strip()
    return df


def _uf(texto: str) -> str:
    m = re.search(r"\(([^);]+)", texto or "")
    uf = m.group(1).strip() if m else ""
    return uf if uf in UF_COORD else "Distrito Federal"


@st.cache_data
def transformar(df: pd.DataFrame):
    """Transformação: tabelas de decisões, núcleos e núcleo × princípio."""
    dec_rows = df[df["Nível"] == "decisão"]
    piv = dec_rows.pivot_table(index="ID_decisao", columns="ID_pergunta", values="Resposta", aggfunc="first")
    base = df.groupby("ID_decisao").agg(Decisão=("Decisão", "first"), Classe=("Classe", "first"),
                                        Data=("Data do julgamento", "first"))
    dec = base.join(piv, how="left").reset_index()
    dec["Data"] = pd.to_datetime(dec["Data"], format="%d/%m/%Y", errors="coerce")
    dec["Ano"] = dec["Data"].dt.year
    dec["UF"] = dec["S01_classe_numero"].fillna("").map(_uf)
    dec["Resumo"] = (dec["S01_objeto"].fillna("") + " Resultado: " + dec["S01_resultado_proclamado"].fillna(""))

    nuc_rows = df[(df["Nível"] == "núcleo") & (df["Núcleo"] != "0") & (df["Item"] == "")]
    pn = nuc_rows.pivot_table(index=["ID_decisao", "Núcleo"], columns="ID_pergunta", values="Resposta",
                              aggfunc="first").reset_index()
    tit = nuc_rows.groupby(["ID_decisao", "Núcleo"])["Título do núcleo"].first().reset_index()
    nuc = pn.merge(tit, on=["ID_decisao", "Núcleo"]).merge(dec[["ID_decisao", "Decisão", "Classe", "Ano"]],
                                                           on="ID_decisao")

    # trecho ilustrativo e validação por núcleo × princípio (linha da posição)
    ev = df[df["ID_pergunta"].str.match(r"^(IN|FSP|MA)_B_posicao$")][
        ["ID_decisao", "Núcleo", "ID_pergunta", "Trecho (evidência literal)", "Página PDF", "Página impressa",
         "Autoria e plano", "Justificativa"]]
    ev = ev.assign(px=ev["ID_pergunta"].str.split("_").str[0])

    # validação: núcleo × princípio considerado validado se a linha da concretização tiver "Concorda?"
    val = df[df["ID_pergunta"].str.match(r"^(IN|FSP|MA)_CN_concretizacao$")][["ID_decisao", "Núcleo", "ID_pergunta",
                                                                              "Concorda?"]]
    val = val.assign(px=val["ID_pergunta"].str.split("_").str[0])

    longos = []
    for px_, nome in PRINCIPIOS.items():
        t = nuc[["ID_decisao", "Decisão", "Classe", "Ano", "Núcleo", "Título do núcleo"]].copy()
        t["px"], t["Princípio"] = px_, nome
        for campo, col in (("B_posicao", "Posição"), ("C_densificacao", "Densificação"),
                           ("AT_atribuicao", "Atribuição"), ("CN_concretizacao", "Concretização"),
                           ("FS_funcao_simbolica", "Função simbólica")):
            t[col] = nuc.get(f"{px_}_{campo}", pd.Series([""] * len(nuc))).fillna("Campo aplicável ainda não preenchido")
        longos.append(t)
    npz = pd.concat(longos, ignore_index=True)
    npz = npz.merge(ev.drop(columns="ID_pergunta"), on=["ID_decisao", "Núcleo", "px"], how="left") \
             .merge(val.drop(columns="ID_pergunta"), on=["ID_decisao", "Núcleo", "px"], how="left")
    npz["Concretização (rótulo)"] = npz["Concretização"].map(ROTULO_CONCR).fillna(npz["Concretização"])
    npz["Densificação (rótulo)"] = npz["Densificação"].map(ROT_DENS).fillna(npz["Densificação"])
    npz["Validado"] = npz["Concorda?"].fillna("").ne("")
    return dec, nuc, npz


try:
    bruto = carregar(str(CAMINHO_EXCEL))
except FileNotFoundError:
    st.error(f"Banco não encontrado em {CAMINHO_EXCEL}. Coloque o Excel do projeto na pasta data/.")
    st.stop()
dec, nuc, npz = transformar(bruto)


@st.cache_data
def carregar_mapa(caminho: str):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


GEOJSON_UF = carregar_mapa(str(CAMINHO_MAPA))
# contornos por estado: {nome: [anel, ...]} com anéis externos dos polígonos
CONTORNOS = {}
for _f in GEOJSON_UF["features"]:
    _g = _f["geometry"]
    _polis = [_g["coordinates"]] if _g["type"] == "Polygon" else _g["coordinates"]
    CONTORNOS[_f["properties"]["name"]] = [p[0] for p in _polis]

# ================================================================== filtros
with st.sidebar:
    st.markdown("### Filtros")
    classes = sorted(dec["Classe"].dropna().unique())
    f_classe = st.multiselect("Classe processual", classes, default=classes)
    anos = dec["Ano"].dropna().astype(int)
    f_ano = st.slider("Período (ano do julgamento)", int(anos.min()), int(anos.max()),
                      (int(anos.min()), int(anos.max())))
    f_princ = st.multiselect("Princípio", list(PRINCIPIOS.values()), default=list(PRINCIPIOS.values()))
    dec_opcoes = dec[(dec["Classe"].isin(f_classe)) & (dec["Ano"].between(*f_ano))]["Decisão"].tolist()
    f_dec = st.multiselect("Decisão (vazio = todas)", dec_opcoes)
    st.markdown("---")
    st.caption("O painel lê apenas o banco validável (output 2). As classificações são provisórias até a "
               "validação da pesquisadora.")

decf = dec[(dec["Classe"].isin(f_classe)) & (dec["Ano"].between(*f_ano))]
if f_dec:
    decf = decf[decf["Decisão"].isin(f_dec)]
ids = set(decf["ID_decisao"])
npzf = npz[npz["ID_decisao"].isin(ids) & npz["Princípio"].isin(f_princ)]
nucf = nuc[nuc["ID_decisao"].isin(ids)]

# ================================================================== cabeçalho
st.markdown("""
<div class="faixa">
  <div style="display:flex;align-items:center">
    <div class="marca">A/B/C</div>
    <div class="sub">Instrumento de análise dos núcleos decisórios<br>e de classificação pelo índice A/B/C</div>
  </div>
  <div class="sigla">STF · Mineração</div>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="titulo-painel">Painel das Decisões do STF em Direito Minerário</div>',
            unsafe_allow_html=True)

total_val = npz["Validado"].sum()
if total_val < len(npz):
    st.warning(f"Pré-preenchimento assistido por IA: {len(npz) - total_val} de {len(npz)} classificações "
               "(núcleo × princípio) ainda não foram validadas pela pesquisadora. Os resultados são provisórios.",
               icon="⚠️")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Decisões", len(decf))
k2.metric("Núcleos decisórios analisados", len(nucf))
per = decf["Data"].dropna()
k3.metric("Período coberto", f"{per.min():%Y}–{per.max():%Y}" if len(per) else "—")
k4.metric("Classificações validadas", f"{int(npzf['Validado'].sum())} de {len(npzf)}")

aba_painel, aba_abc, aba_tempo, aba_ficha, aba_sobre = st.tabs(
    ["Painel geral", "Índice A/B/C", "Linha do tempo", "Ficha da decisão", "Sobre o método"])


def tabela_html(df_: pd.DataFrame, classe: str, colunas: list, altura: int = 420) -> str:
    linhas = []
    for _, r in df_.iterrows():
        cel = "".join(f"<td>{r[c]}</td>" for c in colunas)
        linhas.append(f"<tr>{cel}</tr>")
    cab = "".join(f"<th>{html.escape(c)}</th>" for c in colunas)
    return (f'<div class="caixa-scroll" style="max-height:{altura}px"><table class="{classe}">'
            f"<thead><tr>{cab}</tr></thead><tbody>{''.join(linhas)}</tbody></table></div>")


def esc(s) -> str:
    return html.escape(str(s or ""))


# ================================================================ PAINEL GERAL
with aba_painel:
    c1, c2 = st.columns([1, 1.35])
    with c1:
        st.markdown('<div class="secao">Localidade e Decisão</div>', unsafe_allow_html=True)
        m = decf.copy()
        if len(m):
            m["lat"] = m["UF"].map(lambda u: UF_COORD[u][0])
            m["lon"] = m["UF"].map(lambda u: UF_COORD[u][1])
            # pequeno deslocamento para separar decisões da mesma UF
            m["ordem"] = m.groupby("UF").cumcount()
            # decisões da mesma UF ficam num pequeno círculo em volta da capital
            import math
            n_uf = m.groupby("UF")["ordem"].transform("max") + 1
            ang = 2 * math.pi * m["ordem"] / n_uf
            raio = n_uf.map(lambda n: 0 if n == 1 else 0.9 + 0.12 * n)
            m["lat"] = m["lat"] + raio * ang.map(math.sin)
            m["lon"] = m["lon"] + raio * ang.map(math.cos)
            # Mapa desenhado como gráfico comum (longitude × latitude) a partir do contorno dos estados embutido
            # no repositório (data/brasil_ufs.geojson): não depende de nenhum servidor de mapas externo.
            com_decisao = set(decf["UF"])
            fig = go.Figure()
            for tem, cor in ((False, "#E9EDF2"), (True, "#BFD9F2")):
                xs, ys = [], []
                for nome, aneis in CONTORNOS.items():
                    if (nome in com_decisao) != tem:
                        continue
                    for anel in aneis:
                        xs += [c[0] for c in anel] + [None]
                        ys += [c[1] for c in anel] + [None]
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor=cor,
                                         line=dict(color="#FFFFFF", width=0.8), hoverinfo="skip", showlegend=False))
            for nome, (lat, lon) in UF_COORD.items():
                if nome in com_decisao:
                    fig.add_annotation(x=lon, y=lat + 1.1, text=nome.upper(), showarrow=False,
                                       font=dict(size=8, color="#5B6B7C"))
            paleta = px.colors.qualitative.Plotly + px.colors.qualitative.Pastel + px.colors.qualitative.Bold
            for i, (_, linha) in enumerate(m.iterrows()):
                ano = int(linha["Ano"]) if pd.notna(linha["Ano"]) else ""
                fig.add_trace(go.Scatter(
                    x=[linha["lon"]], y=[linha["lat"]], mode="markers", name=linha["Decisão"], showlegend=False,
                    marker=dict(size=14, color=paleta[i % len(paleta)], opacity=0.9, line=dict(width=1, color="white")),
                    hovertemplate=f"<b>{linha['Decisão']}</b><br>{linha['UF']} · {ano}<extra></extra>"))
            fig.update_xaxes(visible=False, range=[-74.5, -33.5])
            fig.update_yaxes(visible=False, range=[-34.5, 6], scaleanchor="x", scaleratio=1)
            fig.update_layout(height=430, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="#C9DDF0",
                              paper_bgcolor="#C9DDF0", dragmode=False)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.caption("Posição pela unidade da federação de origem do processo (ações contra leis federais aparecem em Brasília).")
    with c2:
        st.markdown('<div class="secao">Detalhamento da Decisão</div>', unsafe_allow_html=True)
        tdet = decf.sort_values("Data", ascending=False)
        tdet = tdet.assign(Caso=tdet["Decisão"].map(esc) + "<br><small>" + tdet["Data"].dt.strftime("%d/%m/%Y").fillna("") +
                           " · " + tdet["UF"].map(esc) + "</small>",
                           **{"Resumo da decisão": tdet["Resumo"].map(esc)})
        st.markdown(tabela_html(tdet, "tab-resumo", ["Caso", "Resumo da decisão"], 450), unsafe_allow_html=True)

    st.write("")
    d1, d2, d3 = st.columns([1.2, 0.9, 1.1])
    with d1:
        st.markdown('<div class="secao">Concretização normativa por categoria</div>', unsafe_allow_html=True)
        cont = npzf["Concretização (rótulo)"].value_counts()
        ordem = [ROTULO_CONCR[o] for o in ORDEM_CONCR if ROTULO_CONCR[o] in cont.index] + \
                [o for o in cont.index if o not in ROTULO_CONCR.values()]
        fig = go.Figure(go.Pie(labels=ordem, values=[cont[o] for o in ordem], hole=0.62, sort=False,
                               marker=dict(colors=[COR_CONCR.get(o, "#999") for o in ordem]),
                               textinfo="value", textposition="outside"))
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10),
                          annotations=[dict(text=f"<b>{cont.sum()}</b>", x=0.5, y=0.5, font_size=30, showarrow=False)],
                          legend=dict(title="Concretização", font=dict(size=11)))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.caption("Cada unidade é um núcleo decisório × princípio.")
    with d2:
        st.markdown('<div class="secao-cinza">Relator(a) e órgão julgador</div>', unsafe_allow_html=True)
        rel = decf.sort_values("Data")[["Decisão", "S01_relator_originario", "S01_orgao_julgador"]].fillna("")
        itens = "".join(f"<div><b>{esc(r['Decisão'])}</b> — {esc(r['S01_relator_originario'])}"
                        f"<br><small>{esc(r['S01_orgao_julgador'])}</small></div>" for _, r in rel.iterrows())
        st.markdown(f'<div class="caixa-scroll lista-rep" style="max-height:330px">{itens}</div>',
                    unsafe_allow_html=True)
    with d3:
        st.markdown('<div class="secao-cinza">Palavras-chave</div>', unsafe_allow_html=True)
        termos = {}
        for col in ("S05_macrocampos", "S05_marcadores_auxiliares"):
            if col in nucf:
                for v in nucf[col].fillna(""):
                    for t in v.split(" ; "):
                        t = t.strip()
                        if t and t not in MARCADORES:
                            t = t.replace("outro: ", "").replace("outra: ", "")
                            termos[t[:1].upper() + t[1:]] = termos.get(t[:1].upper() + t[1:], 0) + 1
        texto = "; ".join(sorted(termos, key=lambda x: -termos[x])[:14])
        st.markdown(f'<div class="palavras">{esc(texto) or "—"}</div>', unsafe_allow_html=True)

    st.markdown('<div class="secao">Princípios por núcleo decisório</div>', unsafe_allow_html=True)
    ttab = npzf.sort_values(["Decisão", "Núcleo", "px"]).copy()
    ttab["Decisão / núcleo"] = ttab["Decisão"].map(esc) + "<br><small>" + ttab["Título do núcleo"].map(esc) + "</small>"
    ttab["Validação"] = ttab["Validado"].map(lambda v: "validado" if v else '<span class="selo">pendente</span>')
    ttab["Trecho ilustrativo"] = ttab["Trecho (evidência literal)"].fillna("").map(
        lambda t: esc(t.split(" || ")[0][:420]) or "—")
    ttab["Página"] = ttab["Página PDF"].fillna("").map(lambda p: f'<span class="pag">p. {esc(p.split(" || ")[0])}</span>'
                                                        if p else "—")
    for c in ("Princípio", "Posição", "Concretização (rótulo)", "Função simbólica"):
        ttab[c] = ttab[c].map(esc)
    ttab = ttab.drop(columns=["Concretização"]).rename(columns={"Concretização (rótulo)": "Concretização"})
    st.markdown(tabela_html(ttab, "tab-escura", ["Decisão / núcleo", "Princípio", "Posição", "Concretização",
                                                 "Função simbólica", "Trecho ilustrativo", "Página", "Validação"], 520),
                unsafe_allow_html=True)

# ================================================================ ÍNDICE A/B/C
with aba_abc:
    st.markdown("#### Dimensão A — o STF resolveu a controvérsia?")
    a = nucf.get("S06_resolucao_operativa", pd.Series(dtype=str)).value_counts().reset_index()
    a.columns = ["Resolução operativa", "Núcleos"]
    fig = px.bar(a, x="Núcleos", y="Resolução operativa", orientation="h", text="Núcleos",
                 color_discrete_sequence=["#1F77D0"], height=200)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title=None)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    def barras(df_, col, ordem, cores, titulo):
        t = df_.groupby(["Princípio", col]).size().reset_index(name="Núcleos")
        ordem_ = [o for o in ordem if o in t[col].unique()] + [o for o in t[col].unique() if o not in ordem]
        fig = px.bar(t, y="Princípio", x="Núcleos", color=col, orientation="h", category_orders={col: ordem_},
                     color_discrete_map=cores, height=300, text="Núcleos")
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), legend_title=None, yaxis_title=None, barmode="stack",
                          title=dict(text=titulo, font=dict(size=15)),
                          legend=dict(orientation="h", y=-0.25))
        return fig

    st.markdown("#### Dimensão B — que lugar cada princípio ocupou na fundamentação?")
    st.plotly_chart(barras(npzf, "Posição", ORDEM_POS, COR_POS, "Posição na fundamentação"),
                    width="stretch", config={"displayModeBar": False})
    st.markdown("#### Dimensão C — o princípio ganhou conteúdo (critério) próprio?")
    dd = npzf.assign(**{"Densificação": npzf["Densificação (rótulo)"]})
    st.plotly_chart(barras(dd, "Densificação", list(COR_DENS), COR_DENS, "Densificação normativa"),
                    width="stretch", config={"displayModeBar": False})
    st.markdown("#### Concretização normativa e função simbólica, lado a lado")
    e1, e2 = st.columns(2)
    with e1:
        cc = npzf.assign(**{"Concretização": npzf["Concretização (rótulo)"]})
        st.plotly_chart(barras(cc, "Concretização", list(COR_CONCR), COR_CONCR, "Concretização normativa"),
                        width="stretch", config={"displayModeBar": False})
    with e2:
        st.plotly_chart(barras(npzf, "Função simbólica", ORDEM_FS, COR_FS, "Função simbólica"),
                        width="stretch", config={"displayModeBar": False})
    st.caption("Os marcadores do instrumento (por exemplo, “Não aplicável” ou “Inconclusivo”) aparecem como categorias "
               "próprias. Concretização normativa e função simbólica são eixos independentes.")

# ================================================================ LINHA DO TEMPO
with aba_tempo:
    st.markdown('<div class="secao">Linha do tempo das decisões</div>', unsafe_allow_html=True)
    tl = decf.dropna(subset=["Data"]).copy()
    melhor = npz[npz["px"] == "MA"].groupby("ID_decisao")["Concretização (rótulo)"].agg(
        lambda s: next((ROTULO_CONCR[o] for o in ORDEM_CONCR if ROTULO_CONCR[o] in set(s)), s.iloc[0]))
    tl["Meio ambiente (melhor núcleo)"] = tl["ID_decisao"].map(melhor).fillna("—")
    fig = px.scatter(tl, x="Data", y="Classe", color="Meio ambiente (melhor núcleo)", hover_name="Decisão",
                     hover_data={"S01_objeto": True, "Classe": False}, color_discrete_map=COR_CONCR, height=420,
                     category_orders={"Meio ambiente (melhor núcleo)": list(COR_CONCR)})
    fig.update_traces(marker=dict(size=16, line=dict(width=1, color="white")))
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=-0.2), yaxis_title=None,
                      xaxis_title=None)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    por_ano = npzf[npzf["Concretização (rótulo)"].isin(["Concretização institucional", "Concretização no caso"])] \
        .groupby(["Ano", "Princípio"]).size().reset_index(name="Núcleos concretizadores")
    if len(por_ano):
        fig = px.bar(por_ano, x="Ano", y="Núcleos concretizadores", color="Princípio", height=280,
                     color_discrete_sequence=["#7F6000", "#833C0B", "#2E7D32"])
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ================================================================ FICHA
with aba_ficha:
    if len(decf) == 0:
        st.info("Nenhuma decisão nos filtros escolhidos.")
    else:
        escolha = st.selectbox("Escolha a decisão", decf.sort_values("Data")["Decisão"].tolist())
        r = decf[decf["Decisão"] == escolha].iloc[0]
        f1, f2, f3 = st.columns(3)
        f1.metric("Julgamento", r["Data"].strftime("%d/%m/%Y") if pd.notna(r["Data"]) else "—")
        f2.metric("Núcleos elegíveis", r.get("S04_total_elegiveis", "—"))
        f3.metric("Origem", r["UF"])
        st.markdown(f"**Objeto.** {esc(r.get('S01_objeto'))}")
        st.markdown(f"**Resultado proclamado.** {esc(r.get('S01_resultado_proclamado'))}")
        st.markdown(f"**Relator(a).** {esc(r.get('S01_relator_originario'))} &nbsp;·&nbsp; "
                    f"**Meio.** {esc(r.get('S01_meio_julgamento'))}", unsafe_allow_html=True)
        for _, n in nuc[nuc["ID_decisao"] == r["ID_decisao"]].sort_values("Núcleo").iterrows():
            with st.expander(f"Núcleo {n['Núcleo']} — {n['Título do núcleo']}", expanded=True):
                st.markdown(f"**Questão.** {esc(n.get('S05_questao_juridica'))}")
                st.markdown(f"**Resolução operativa (A):** {esc(n.get('S06_resolucao_operativa'))}")
                sub = npz[(npz["ID_decisao"] == r["ID_decisao"]) & (npz["Núcleo"] == n["Núcleo"])]
                cols = st.columns(3)
                for col, (_, p) in zip(cols, sub.iterrows()):
                    with col:
                        st.markdown(f"**{p['Princípio']}** <small>({ARTIGOS[p['px']]})</small>", unsafe_allow_html=True)
                        st.markdown(f"Posição (B): {esc(p['Posição'])}  \nDensificação (C): {esc(p['Densificação'])}  \n"
                                    f"Concretização: **{esc(p['Concretização (rótulo)'])}**  \n"
                                    f"Função simbólica: {esc(p['Função simbólica'])}")
                        tr = str(p.get("Trecho (evidência literal)") or "").split(" || ")[0]
                        if tr:
                            pg = str(p.get("Página PDF") or "").split(" || ")[0]
                            st.markdown(f"> “{esc(tr[:500])}” <span class='pag'>(p. {esc(pg)})</span>",
                                        unsafe_allow_html=True)
                        st.markdown("validado" if p["Validado"] else '<span class="selo">validação pendente</span>',
                                    unsafe_allow_html=True)
        inc = r.get("CTRL_inconsistencias")
        if inc:
            with st.expander("Inconsistências documentais registradas no acórdão"):
                st.write(inc)

# ================================================================ SOBRE
with aba_sobre:
    st.markdown("""
**O que é este painel.** Uma visão resumida do banco construído com o *Instrumento de análise dos núcleos decisórios
e de classificação pelo índice A/B/C* (versão 5.0), aplicado a decisões do Supremo Tribunal Federal sobre direito
minerário. Cada decisão é dividida em **núcleos decisórios** (questões jurídicas autônomas); em cada núcleo, três
princípios constitucionais são examinados separadamente: **interesse nacional** (art. 176, § 1º), **função social da
propriedade** (art. 170, III) e **meio ambiente ecologicamente equilibrado** (art. 225).

**Como ler o índice.**
- **A — Resolução operativa:** a decisão produziu um comando jurídico determinado?
- **B — Posição na fundamentação:** o princípio foi ausente, ornamental, relevante ou determinante para a conclusão?
- **C — Densificação:** o tribunal extraiu do princípio um critério, dever ou limite?
- **Concretização normativa** combina B, C e a atribuição do critério ao princípio; **função simbólica** é um eixo
  independente, que exige requisitos cumulativos e o teste de explicações alternativas.

**Como os dados foram produzidos.** O texto de cada decisão foi extraído do PDF por script (com OCR nas páginas
escaneadas); a leitura interpretativa e o pré-preenchimento foram feitos por modelo de linguagem seguindo o capítulo de
regras e o questionário; todos os trechos citados foram conferidos automaticamente contra o texto extraído; e toda
classificação está sujeita à validação da pesquisadora (colunas “Concorda?”, “Correções” e “Comentário” do banco).
""")

st.markdown('<div class="rodape">Método descrito no apêndice da tese (Suzy Sousa, UFPA). Fonte: banco_ABC_STF_mineracao.xlsx. '
            'Classificações provisórias até a validação da pesquisadora.</div>', unsafe_allow_html=True)
