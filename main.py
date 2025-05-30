# Streamlit App: Warframe Market Analyzer

import streamlit as st
import pandas as pd
import requests
import plotly.express as px

API_URL = "https://api.warframe.market/v1"
HEADERS = {"accept": "application/json"}

@st.cache_data(ttl=3600)
def get_items():
    response = requests.get(f"{API_URL}/items", headers=HEADERS)
    items = response.json()['payload']['items']
    filtered = [i for i in items if i['url_name'] and not i['url_name'].startswith("riven")]
    return pd.DataFrame(filtered)

@st.cache_data(ttl=300)
def get_orders(item_url):
    response = requests.get(f"{API_URL}/items/{item_url}/orders", headers=HEADERS)
    orders = response.json()['payload']['orders']
    df = pd.DataFrame(orders)
    df = df[df['user'].apply(lambda x: x['status']) == 'ingame']
    return df

def analyze_item(df):
    buys = df[df['order_type'] == 'buy']['platinum']
    sells = df[df['order_type'] == 'sell']['platinum']
    return buys.mean() if not buys.empty else 0, sells.mean() if not sells.empty else 0

def main():
    st.set_page_config(page_title="Warframe Market Analyzer", layout="wide")
    st.title("📈 Warframe Market Analyzer")

    items_df = get_items()
    
    filter_text = st.text_input("🔍 Filtrer par type, mot-clé (melee, arcane, set, prime...)", "melee")
    filtered_items = items_df[items_df['item_name'].str.contains(filter_text, case=False)]

    item_name = st.selectbox("🧩 Choisir un objet :", filtered_items['item_name'].values)
    item_data = filtered_items[filtered_items['item_name'] == item_name].iloc[0]

    orders_df = get_orders(item_data['url_name'])
    buy_avg, sell_avg = analyze_item(orders_df)

    st.markdown(f"### 💰 Prix moyen")
    col1, col2 = st.columns(2)
    col1.metric("Achat moyen (Buy)", f"{buy_avg:.1f}₽")
    col2.metric("Vente moyenne (Sell)", f"{sell_avg:.1f}₽")

    st.markdown("### 📊 Histogramme des prix")
    fig = px.histogram(orders_df, x="platinum", color="order_type",
                       nbins=20, barmode="overlay",
                       labels={"platinum": "Prix (Platinum)"},
                       title=f"Distribution des prix pour {item_name}")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📦 Volume du marché")
    col3, col4 = st.columns(2)
    col3.write(f"Ordres d'achat actifs : {len(orders_df[orders_df['order_type'] == 'buy'])}")
    col4.write(f"Ordres de vente actifs : {len(orders_df[orders_df['order_type'] == 'sell'])}")

    st.info("ℹ️ Conseil : Vendre si le prix de vente est nettement supérieur au prix d'achat moyen.")

if __name__ == '__main__':
    main()
