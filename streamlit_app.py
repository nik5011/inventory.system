import streamlit as st
import pandas as pd
from PIL import Image
import io
import csv

# 配置页面
st.set_page_config(page_title="庫存管理系統", layout="wide")

# 初始化session state
if 'products' not in st.session_state:
    st.session_state.products = []
    st.session_state.next_id = 1
    st.session_state.search = ""

def on_search_change():
    """當搜索內容改變時觸發"""
    st.session_state.search = st.session_state.search_input

def add_product(name, warehouse_qty=0, store_qty=0, notes=""):
    """添加新產品"""
    product = {
        'id': st.session_state.next_id,
        'name': name,
        'warehouse_quantity': warehouse_qty,
        'store_quantity': store_qty,
        'notes': notes
    }
    st.session_state.products.append(product)
    st.session_state.next_id += 1

def delete_product(product_id):
    """刪除產品"""
    st.session_state.products = [p for p in st.session_state.products if p['id'] != product_id]

def sort_products(products, search_term):
    """根據搜索詞排序產品"""
    if not search_term:
        return products
    
    search_term = search_term.lower()
    exact_matches = []
    starts_with_matches = []
    contains_matches = []
    other_matches = []
    
    for product in products:
        name = product['name'].lower()
        if name == search_term:
            exact_matches.append(product)
        elif name.startswith(search_term):
            starts_with_matches.append(product)
        elif search_term in name:
            contains_matches.append(product)
        else:
            other_matches.append(product)
    
    return exact_matches + starts_with_matches + contains_matches + other_matches

def main():
    st.title('庫存管理系統')
    
    # 文件上傳
    uploaded_file = st.file_uploader("上傳產品列表", type=['txt', 'xlsx'])
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        if file_type == 'txt':
            content = uploaded_file.read().decode()
            for line in content.split('\n'):
                name = line.strip()
                if name:
                    add_product(name)
            st.success('成功導入產品！')
            
        elif file_type == 'xlsx':
            df = pd.read_excel(uploaded_file)
            if 'name' in df.columns:
                for _, row in df.iterrows():
                    add_product(row['name'])
                st.success('成功導入產品！')
            else:
                st.error('Excel文件必須包含name列')
    
    # 搜索框 - 使用on_change實現即時搜索
    st.text_input(
        '搜索產品',
        key='search_input',
        value=st.session_state.search,
        on_change=on_search_change
    )
    
    # 導出按鈕
    col1, col2 = st.columns([1, 5])
    with col1:
        export_format = st.selectbox('導出格式', ['Excel', 'CSV'])
        if st.button('導出數據'):
            if st.session_state.products:
                df = pd.DataFrame([{
                    '產品名稱': p['name'],
                    '倉庫數量': p['warehouse_quantity'],
                    '門市數量': p['store_quantity'],
                    '總數量': p['warehouse_quantity'] + p['store_quantity'],
                    '備註': p['notes']
                } for p in st.session_state.products])
                
                if export_format == 'Excel':
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button(
                        label='下載Excel文件',
                        data=output.getvalue(),
                        file_name='inventory.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                else:
                    csv_data = io.StringIO()
                    df.to_csv(csv_data, index=False)
                    st.download_button(
                        label='下載CSV文件',
                        data=csv_data.getvalue(),
                        file_name='inventory.csv',
                        mime='text/csv'
                    )
            else:
                st.warning('沒有產品可以導出')
    
    # 刪除所有產品按鈕
    with col2:
        if st.button('刪除所有產品'):
            if st.session_state.products:
                confirm = st.button('確認刪除所有產品？')
                if confirm:
                    st.session_state.products = []
                    st.success('已刪除所有產品')
                    st.experimental_rerun()
    
    # 顯示產品列表
    if st.session_state.products:
        # 排序產品
        sorted_products = sort_products(st.session_state.products, st.session_state.search)
        
        # 創建產品表格
        for product in sorted_products:
            col1, col2, col3, col4, col5, col6 = st.columns([3,2,2,1,3,1])
            
            with col1:
                st.write(product['name'])
            
            with col2:
                new_warehouse = st.number_input(
                    '倉庫數量',
                    value=product['warehouse_quantity'],
                    key=f"wh_{product['id']}",
                    min_value=0
                )
                if new_warehouse != product['warehouse_quantity']:
                    product['warehouse_quantity'] = new_warehouse
            
            with col3:
                new_store = st.number_input(
                    '門市數量',
                    value=product['store_quantity'],
                    key=f"st_{product['id']}",
                    min_value=0
                )
                if new_store != product['store_quantity']:
                    product['store_quantity'] = new_store
            
            with col4:
                total = product['warehouse_quantity'] + product['store_quantity']
                st.write(f"總數: {total}")
            
            with col5:
                notes = st.text_input(
                    '備註',
                    value=product['notes'],
                    key=f"note_{product['id']}"
                )
                if notes != product['notes']:
                    product['notes'] = notes
            
            with col6:
                if st.button('刪除', key=f"del_{product['id']}"):
                    delete_product(product['id'])
                    st.experimental_rerun()

if __name__ == '__main__':
    main()
