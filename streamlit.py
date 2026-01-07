import streamlit as st
import pandas as pd

st.set_page_config(page_title="Monitor Estadão", layout="wide")

@st.cache_data
def load_data():
    # Carrega o arquivo (certifique-se de que o nome está correto)
    df = pd.read_csv("accepted_news.csv")
    # Limpa espaços vazios nos nomes das colunas por segurança
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()

    st.title("📰 Monitor de Notícias: Estadão")
    
    # Barra de busca lateral para ficar mais organizado
    busca = st.sidebar.text_input("🔍 Buscar por palavra-chave:", "")

    # Filtro usando a coluna 'title' (que é a correta agora)
    if busca:
        # Procuramos na coluna 'title'
        df_filtrado = df[df['title'].str.contains(busca, case=False, na=False)]
    else:
        df_filtrado = df

    st.write(f"Exibindo **{len(df_filtrado)}** notícias.")

    # Loop para exibir os resultados
    for index, row in df_filtrado.iterrows():
        with st.container():
            # Trocado de 'titulo' para 'title'
            st.subheader(row['title'])
            
            # Use .get() para as outras colunas caso elas também mudem
            st.write(row.get('resumo', '')) 
            
            if 'link' in row or 'url' in row:
                url = row.get('link') or row.get('url')
                st.link_button("Abrir Notícia", url)
            
            st.divider()

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
