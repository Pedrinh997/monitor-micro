import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="Monitor Micro", layout="wide")
st.title("📊 Monitor Micro - Frontend")

if 'selected' not in st.session_state:
    st.session_state['selected'] = None
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'search_term' not in st.session_state:
    st.session_state['search_term'] = ""
if 'sort_by' not in st.session_state:
    st.session_state['sort_by'] = "Data (mais recente)"

# --- LOGIN ---
if not st.session_state['token']:
    st.sidebar.header("🔐 Autenticação")

    with st.sidebar.form("login_form"):
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pass")
        if st.form_submit_button("Login"):
            try:
                resp = requests.post(
                    f"{API_URL}/auth/token",
                    data={"username": username, "password": password},
                    timeout=10,
                )
                if resp.status_code == 200:
                    st.session_state['token'] = resp.json()['access_token']
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error(f"Credenciais inválidas (HTTP {resp.status_code})")
            except Exception as e:
                st.error(f"Erro ao conectar com a API: {e}")

    with st.sidebar.expander("➕ Cadastrar novo usuário"):
        with st.form("register_form"):
            reg_user = st.text_input("Usuário", key="reg_user")
            reg_pass = st.text_input("Senha", type="password", key="reg_pass")
            reg_email = st.text_input("Email", key="reg_email")
            if st.form_submit_button("Cadastrar"):
                if not (reg_user and reg_pass and reg_email):
                    st.error("Preencha todos os campos")
                else:
                    try:
                        r = requests.post(
                            f"{API_URL}/auth/register",
                            json={"username": reg_user, "email": reg_email, "password": reg_pass},
                            timeout=10,
                        )
                        if r.status_code == 200:
                            st.success("Cadastrado! Faça login.")
                        else:
                            st.error(f"Erro no cadastro: {r.text}")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.stop()

# --- SIDEBAR (logado) ---
with st.sidebar:
    st.write(f"👋 **{st.session_state['username']}**")
    if st.button("🚪 Sair"):
        st.session_state['token'] = None
        st.session_state['username'] = None
        st.rerun()
    
    st.divider()
    st.header("🔗 Adicionar Produto")
    url = st.text_input("URL do Mercado Livre")
    target_price = st.number_input("Preço Alvo (R$)", min_value=0.0, step=1.0)
    if st.button("🚀 Monitorar"):
        if url:
            try:
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                response = requests.post(f"{API_URL}/scrape/", json={"url": url}, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Produto {data['product_id']} enfileirado!")
                else:
                    st.error(f"Erro: {response.text}")
            except:
                st.error("Erro ao conectar com a API.")
    
    if st.button("🔄 Forçar Atualização"):
        st.rerun()

# --- MAIN ---
# --- ANALYTICS (DuckDB + MinIO) ---
st.subheader("📊 Analytics (DuckDB + MinIO)")

_analytics_headers = {"Authorization": f"Bearer {st.session_state['token']}"}
try:
    r_stats = requests.get(f"{API_URL}/analytics/stats", headers=_analytics_headers, timeout=10)
    if r_stats.status_code == 200:
        stats = r_stats.json()
        if stats.get("count", 0) > 0:
            a, b, c, d = st.columns(4)
            cur = stats.get("currency", "")
            a.metric("Amostras", stats.get("count"))
            b.metric("Preço Médio", f"{stats.get('avg_price', 0):.2f} {cur}")
            c.metric("Mínimo",     f"{stats.get('min_price', 0):.2f} {cur}")
            d.metric("Máximo",     f"{stats.get('max_price', 0):.2f} {cur}")
        else:
            st.info("Sem amostras no data lake ainda.")
    else:
        st.warning(f"Analytics indisponível (HTTP {r_stats.status_code})")
except Exception as e:
    st.warning(f"Erro ao consultar analytics: {e}")

st.divider()

st.subheader("📋 Produtos Monitorados")

headers = {"Authorization": f"Bearer {st.session_state['token']}"}
try:
    response = requests.get(f"{API_URL}/products/", headers=headers)
    if response.status_code == 200:
        products = response.json()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Produtos", len(products))
        col2.metric("Usuário", st.session_state['username'])
        col3.metric("Última Atualização", datetime.now().strftime("%H:%M"))

        if not products:
            st.info("Nenhum produto cadastrado.")
        else:
            # Filtro e ordenação
            col_filtro, col_ordem = st.columns(2)
            with col_filtro:
                search = st.text_input("🔍 Buscar produto", value=st.session_state['search_term'])
                st.session_state['search_term'] = search
            with col_ordem:
                sort_options = ["Data (mais recente)", "Data (mais antiga)", "Preço (crescente)", "Preço (decrescente)", "Título (A-Z)"]
                sort_by = st.selectbox("Ordenar por", sort_options, index=0)
                st.session_state['sort_by'] = sort_by

            if search:
                products = [p for p in products if search.lower() in p.get('title', '').lower()]

            if sort_by == "Data (mais recente)":
                products.sort(key=lambda x: x['created_at'], reverse=True)
            elif sort_by == "Data (mais antiga)":
                products.sort(key=lambda x: x['created_at'])
            elif sort_by == "Preço (crescente)":
                products.sort(key=lambda x: x.get('target_price', 0) or 0)
            elif sort_by == "Preço (decrescente)":
                products.sort(key=lambda x: x.get('target_price', 0) or 0, reverse=True)
            elif sort_by == "Título (A-Z)":
                products.sort(key=lambda x: x.get('title', '').lower())

            for p in products:
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                    col1.write(f"**{p.get('title', 'Sem título')}**")
                    col2.write(f"ID: {p['id']}")
                    col3.write(f"Alvo: R$ {p.get('target_price', 0):.2f}" if p.get('target_price') else "")
                    if col4.button(f"📈 Histórico", key=f"hist_{p['id']}"):
                        st.session_state['selected'] = p['id']
    else:
        st.error("Erro ao buscar produtos.")
except Exception as e:
    st.error(f"API não está rodando.")

# --- HISTÓRICO E GRÁFICO ---
if st.session_state['selected']:
    pid = st.session_state['selected']
    st.divider()
    st.subheader(f"📈 Histórico do Produto ID {pid}")
    
    try:
        response = requests.get(f"{API_URL}/products/{pid}/prices/", headers=headers)
        if response.status_code == 200:
            prices = response.json()
            if prices:
                df = pd.DataFrame(prices)
                df["scraped_at"] = pd.to_datetime(df["scraped_at"])
                
                fig = px.line(df, x="scraped_at", y="price", markers=True, title="Evolução do Preço")
                fig.update_layout(yaxis_title="Preço (R$)", xaxis_title="Data")
                st.plotly_chart(fig, use_container_width=True)
                
                st.write("Últimas medições:")
                st.dataframe(df.tail(5)[["scraped_at", "price"]].sort_values("scraped_at", ascending=False))
            else:
                st.info("Sem histórico.")
        else:
            st.error("Erro ao buscar histórico.")
    except Exception as e:
        st.error(f"Erro: {e}")
