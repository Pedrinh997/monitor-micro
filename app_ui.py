import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Monitor Micro", layout="wide")
st.title("📊 Monitor Micro - Frontend")

# --- Sidebar ---
with st.sidebar:
    st.header("🔗 Adicionar Produto")
    url = st.text_input("URL do Mercado Livre")
    target_price = st.number_input("Preço Alvo (R$)", min_value=0.0, step=1.0)
    if st.button("🚀 Monitorar"):
        if url:
            try:
                response = requests.post(f"{API_URL}/scrape/", json={"url": url})
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Produto {data['product_id']} enfileirado!")
                else:
                    st.error(f"Erro: {response.text}")
            except:
                st.error("Erro ao conectar com a API.")

# --- Main ---
st.subheader("📋 Produtos Monitorados")

try:
    response = requests.get(f"{API_URL}/products/")
    if response.status_code == 200:
        products = response.json()
        if not products:
            st.info("Nenhum produto cadastrado.")
        else:
            for p in products:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{p.get('title', 'Sem título')}**")
                    col2.write(f"ID: {p['id']}")
                    if st.button(f"📈 Histórico", key=p['id']):
                        st.session_state['selected'] = p['id']
    else:
        st.error("Erro ao buscar produtos.")
except:
    st.error("API não está rodando.")

# --- Histórico (se selecionado) ---
if 'selected' in st.session_state:
    pid = st.session_state['selected']
    st.divider()
    st.subheader(f"📈 Histórico do Produto {pid}")
    try:
        response = requests.get(f"{API_URL}/products/{pid}/prices/")
        if response.status_code == 200:
            prices = response.json()
            if prices:
                for p in prices[-5:]:  # últimos 5
                    st.write(f"💰 R$ {p['price']} - {p['scraped_at']}")
            else:
                st.info("Sem histórico.")
        else:
            st.error("Erro ao buscar histórico.")
    except:
        st.error("API não está rodando.")
