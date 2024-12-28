import streamlit as st
import pandas as pd
from PIL import Image
import io
import csv
import json
from difflib import SequenceMatcher

def string_similarity(a, b):
    """計算兩個字符串的相似度"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# 配置页面
st.set_page_config(
    page_title="庫存管理系統",
    page_icon="📦",
    layout="wide"
)

# 初始化session state
if 'products' not in st.session_state:
    st.session_state.products = []
    st.session_state.next_id = 1

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

def main():
    st.title('📦 庫存管理系統')
    
    # 側邊欄：���件上傳和導出
    with st.sidebar:
        st.header('📤 文件操作')
        
        # 文件上傳
        uploaded_file = st.file_uploader(
            "上傳產品列表",
            type=['txt', 'xlsx'],
            help="支持的文件格式：\n- TXT文件（每行一個產品名稱）\n- Excel文件（需要包含name列）"
        )
        
        if uploaded_file is not None:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == 'txt':
                content = uploaded_file.read().decode()
                for line in content.split('\n'):
                    name = line.strip()
                    if name:
                        add_product(name)
                st.success('✅ 成功導入產品！')
                
            elif file_type == 'xlsx':
                df = pd.read_excel(uploaded_file)
                if 'name' in df.columns:
                    for _, row in df.iterrows():
                        add_product(row['name'])
                    st.success('✅ 成功導入產品！')
                else:
                    st.error('❌ Excel文件必須包含name列')
        
        # 導出按鈕
        if st.button('📥 導出產品列表'):
            if st.session_state.products:
                csv_data = io.StringIO()
                csv_writer = csv.writer(csv_data)
                csv_writer.writerow(['產品名稱', '倉庫數量', '門市數量', '備註'])
                
                for product in st.session_state.products:
                    csv_writer.writerow([
                        product['name'],
                        product['warehouse_quantity'],
                        product['store_quantity'],
                        product['notes']
                    ])
                
                st.download_button(
                    label="⬇️ 下載CSV文件",
                    data=csv_data.getvalue(),
                    file_name="products.csv",
                    mime="text/csv"
                )
            else:
                st.warning('⚠️ 沒有產品可以導出')
    
    # 主界面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 搜索框
        search = st.text_input('🔍 搜索產品', help="輸入產品名稱進行搜索")
    
    with col2:
        # 刪除所有產品的按鈕
        if st.button('🗑️ 刪除所有產品'):
            if st.session_state.products:
                confirm = st.button('⚠️ 確認刪除所有產品？')
                if confirm:
                    st.session_state.products = []
                    st.success('✅ 已刪除所有產品')
                    st.experimental_rerun()
    
    # 產品列表
    if st.session_state.products:
        # 過濾並排序產品
        if search:
            # 計算每個產品名稱與搜索詞的相似度
            filtered_products = [
                (p, string_similarity(p['name'], search))
                for p in st.session_state.products
            ]
            # 按相似度排序
            filtered_products.sort(key=lambda x: x[1], reverse=True)
            # 只保留相似度大於0的產品
            filtered_products = [p[0] for p in filtered_products if p[1] > 0]
        else:
            filtered_products = st.session_state.products
        
        if filtered_products:
            st.write('### 📋 產品列表')
            
            for product in filtered_products:
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([3,2,2,1,4,1])
                    
                    with col1:
                        st.markdown(f"**{product['name']}**")
                    
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
                        st.markdown(f"**總數: {total}**")
                    
                    with col5:
                        notes = st.text_input(
                            '備註',
                            value=product['notes'],
                            key=f"note_{product['id']}"
                        )
                        if notes != product['notes']:
                            product['notes'] = notes
                    
                    with col6:
                        if st.button('🗑️', key=f"del_{product['id']}"):
                            delete_product(product['id'])
                            st.experimental_rerun()
                    
                    st.markdown("---")
        else:
            st.info('🔍 沒有找到匹配的產品')
    else:
        st.info('ℹ️ 暫無產品數據，請上傳產品列表或手動添加產品')

if __name__ == '__main__':
    main() 
