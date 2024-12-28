import streamlit as st
import pandas as pd
import sqlite3
from PIL import Image
import io
import csv
import os

# 創建數據庫連接
conn = sqlite3.connect('inventory.db')
c = conn.cursor()

# 創建產品表
c.execute('''CREATE TABLE IF NOT EXISTS products
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              warehouse_quantity INTEGER DEFAULT 0,
              store_quantity INTEGER DEFAULT 0,
              notes TEXT)''')
conn.commit()

def main():
    st.title('庫存管理系統')
    
    # 文件上傳
    uploaded_file = st.file_uploader("上傳產品列表", type=['txt', 'xlsx'])
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        if file_type == 'txt':
            # 處理txt文件
            content = uploaded_file.read().decode()
            for line in content.split('\n'):
                name = line.strip()
                if name:  # 確保不是空行
                    c.execute("INSERT INTO products (name) VALUES (?)", (name,))
            conn.commit()
            st.success('成功導入產品！')
            
        elif file_type == 'xlsx':
            # 處理Excel文件
            df = pd.read_excel(uploaded_file)
            if 'name' in df.columns:
                for _, row in df.iterrows():
                    c.execute("INSERT INTO products (name) VALUES (?)", (row['name'],))
                conn.commit()
                st.success('成功導入產品！')
            else:
                st.error('Excel文件必須包含name列')
    
    # 搜索框
    search = st.text_input('搜索產品')
    
    # 獲取產品列表
    if search:
        c.execute("SELECT * FROM products WHERE name LIKE ?", (f'%{search}%',))
    else:
        c.execute("SELECT * FROM products")
    products = c.fetchall()
    
    # 顯示產品列表
    if products:
        st.write('產品列表：')
        for product in products:
            col1, col2, col3, col4, col5 = st.columns([2,1,1,2,1])
            
            with col1:
                st.write(product[1])  # 產品名稱
            
            with col2:
                new_warehouse = st.number_input(
                    '倉庫數量',
                    value=product[2],
                    key=f'wh_{product[0]}'
                )
                if new_warehouse != product[2]:
                    c.execute(
                        "UPDATE products SET warehouse_quantity=? WHERE id=?",
                        (new_warehouse, product[0])
                    )
                    conn.commit()
            
            with col3:
                new_store = st.number_input(
                    '門市數量',
                    value=product[3],
                    key=f'st_{product[0]}'
                )
                if new_store != product[3]:
                    c.execute(
                        "UPDATE products SET store_quantity=? WHERE id=?",
                        (new_store, product[0])
                    )
                    conn.commit()
            
            with col4:
                notes = st.text_input(
                    '備註',
                    value=product[4] if product[4] else '',
                    key=f'note_{product[0]}'
                )
                if notes != product[4]:
                    c.execute(
                        "UPDATE products SET notes=? WHERE id=?",
                        (notes, product[0])
                    )
                    conn.commit()
            
            with col5:
                if st.button('刪除', key=f'del_{product[0]}'):
                    c.execute("DELETE FROM products WHERE id=?", (product[0],))
                    conn.commit()
                    st.experimental_rerun()
    
    # 刪除所有產品的按鈕
    if st.button('刪除所有產品'):
        if st.button('確認刪除所有產品？'):
            c.execute("DELETE FROM products")
            conn.commit()
            st.success('已刪除所有產品')
            st.experimental_rerun()
    
    # 導出按鈕
    if st.button('導出產品列表'):
        c.execute("SELECT * FROM products")
        products = c.fetchall()
        
        if products:
            # 創建CSV文件
            csv_data = io.StringIO()
            csv_writer = csv.writer(csv_data)
            csv_writer.writerow(['產品名稱', '倉庫數量', '門市數量', '備註'])
            
            for product in products:
                csv_writer.writerow([product[1], product[2], product[3], product[4]])
            
            # 提供下載
            st.download_button(
                label="下載CSV文件",
                data=csv_data.getvalue(),
                file_name="products.csv",
                mime="text/csv"
            )
        else:
            st.warning('沒有產品可以導出')

if __name__ == '__main__':
    main()
