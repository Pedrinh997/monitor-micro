import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

API_URL = "http://localhost:8001"

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
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        col1, col2 = st.columns(2)
        if col1.form_submit_button("Login"):
            try:
                resp = requests.post(f"{API_URL}/auth/token", data={"username": username, "password": password})
                if resp.status_code == 200:
                    st.session_state['token'] = resp.json()['access_token']
                    st.session_state['username'] = username
                    st.success("Login realizado!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")
            except:
                st.error("Erro ao conectar com a API")
        if col2.form_submit_button("Cadastrar"):
            try:
                resp = requests.post(f"{API_URL}/auth/register", json={"username": username, "email": f"{username}@email.com", "password": password})
                if resp.status_code == 200:
                    st.success("Cadastrado! Faça login.")
                else:
                    st.error("Erro no cadastro")
            except:
                st.error("Erro ao conectar com a API")
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
