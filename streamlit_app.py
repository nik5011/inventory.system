import streamlit as st
import pandas as pd
import os
from PIL import Image
import pytesseract
import pdfplumber
from opencc import OpenCC
import io
import json

# 配置页面
st.set_page_config(page_title="庫存管理系統", layout="wide")

# 配置繁体转换器
cc = OpenCC('s2t')

# 初始化会话状态
if 'products' not in st.session_state:
    if os.path.exists('products.json'):
        with open('products.json', 'r', encoding='utf-8') as f:
            st.session_state.products = json.load(f)
    else:
        st.session_state.products = []

def save_products():
    """保存产品数据到文件"""
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.products, f, ensure_ascii=False, indent=2)

def extract_text_from_image(image):
    """从图片中提取文本"""
    try:
        # 转换为RGB模式（如果是RGBA）
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        # 调整图像大小以提高OCR准确性
        width, height = image.size
        if width > 2000 or height > 2000:
            ratio = min(2000/width, 2000/height)
            image = image.resize((int(width*ratio), int(height*ratio)), Image.Resampling.LANCZOS)
        # 使用Tesseract进行OCR
        text = pytesseract.image_to_string(image, lang='chi_sim')
        return text.strip()
    except Exception as e:
        st.error(f'圖片處理錯誤: {str(e)}')
        return None

def process_pdf_file(pdf_file):
    """处理PDF文件"""
    try:
        product_names = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    product_names.extend(lines)
        return product_names
    except Exception as e:
        st.error(f'PDF處理錯誤: {str(e)}')
        return []

# 标题
st.title('庫存管理系統')

# 文件上传部分
st.header('添加新產品')
uploaded_file = st.file_uploader(
    "選擇文件上傳",
    type=['txt', 'xlsx', 'pdf', 'jpg', 'jpeg', 'png'],
    help="支持的文件類型：TXT（每行一個產品）、Excel（第一列為產品名稱）、PDF、圖片"
)

if uploaded_file is not None:
    try:
        file_type = uploaded_file.type
        if file_type.startswith('image'):
            # 处理图片
            image = Image.open(uploaded_file)
            product_name = extract_text_from_image(image)
            if product_name:
                new_product = {
                    'name': product_name,
                    'warehouse_quantity': 0,
                    'store_quantity': 0,
                    'notes': ''
                }
                st.session_state.products.append(new_product)
                save_products()
                st.success('產品添加成功！')
        
        elif file_type == 'text/plain':
            # 处理文本文件
            content = uploaded_file.getvalue().decode('utf-8')
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            for line in lines:
                new_product = {
                    'name': line,
                    'warehouse_quantity': 0,
                    'store_quantity': 0,
                    'notes': ''
                }
                st.session_state.products.append(new_product)
            save_products()
            st.success(f'成功添加 {len(lines)} 個產品！')
        
        elif file_type == 'application/pdf':
            # 处理PDF文件
            product_names = process_pdf_file(uploaded_file)
            for name in product_names:
                new_product = {
                    'name': name,
                    'warehouse_quantity': 0,
                    'store_quantity': 0,
                    'notes': ''
                }
                st.session_state.products.append(new_product)
            save_products()
            st.success(f'成功添加 {len(product_names)} 個產品！')
        
        elif file_type.startswith('application/vnd.openxmlformats-officedocument.spreadsheetml') or \
             file_type.startswith('application/vnd.ms-excel'):
            # 处理Excel文件
            df = pd.read_excel(uploaded_file)
            if not df.empty:
                names = df.iloc[:, 0].dropna().tolist()
                for name in names:
                    new_product = {
                        'name': str(name),
                        'warehouse_quantity': 0,
                        'store_quantity': 0,
                        'notes': ''
                    }
                    st.session_state.products.append(new_product)
                save_products()
                st.success(f'成功添加 {len(names)} 個產品！')
    
    except Exception as e:
        st.error(f'文件處理錯誤: {str(e)}')

# 搜索框
search_term = st.text_input('搜索產品', key='search')

# 导出按钮
col1, col2 = st.columns([1, 5])
with col1:
    export_format = st.selectbox('導出格式', ['Excel', 'TXT'])
    if st.button('導出數據'):
        try:
            if export_format == 'Excel':
                output = io.BytesIO()
                df = pd.DataFrame([{
                    '產品名稱': cc.convert(p['name']),
                    '倉庫數量': p['warehouse_quantity'],
                    '店面數量': p['store_quantity'],
                    '總數量': p['warehouse_quantity'] + p['store_quantity'],
                    '備註': cc.convert(p['notes'])
                } for p in st.session_state.products])
                df.to_excel(output, index=False)
                st.download_button(
                    label='下載Excel文件',
                    data=output.getvalue(),
                    file_name='inventory.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                output = io.StringIO()
                for p in st.session_state.products:
                    output.write(f"產品名稱: {cc.convert(p['name'])}\n")
                    output.write(f"倉庫數量: {p['warehouse_quantity']}\n")
                    output.write(f"店面數量: {p['store_quantity']}\n")
                    output.write(f"總數量: {p['warehouse_quantity'] + p['store_quantity']}\n")
                    output.write(f"備註: {cc.convert(p['notes'])}\n")
                    output.write("-" * 50 + "\n")
                st.download_button(
                    label='下載文本文件',
                    data=output.getvalue(),
                    file_name='inventory.txt',
                    mime='text/plain'
                )
        except Exception as e:
            st.error(f'導出錯誤: {str(e)}')

# 删除所有产品按钮
with col2:
    if st.button('刪除所有產品', type='secondary'):
        if st.session_state.products:
            if st.button('確認刪除所有產品？', type='primary'):
                st.session_state.products = []
                save_products()
                st.success('所有產品已刪除！')
                st.rerun()

# 显示产品列表
if st.session_state.products:
    # 过滤产品
    filtered_products = [p for p in st.session_state.products 
                        if search_term.lower() in p['name'].lower()]
    
    # 创建产品表格
    for i, product in enumerate(filtered_products):
        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 3, 1])
        
        with col1:
            st.text(cc.convert(product['name']))
        
        with col2:
            new_warehouse = st.number_input(
                '倉庫數量',
                value=product['warehouse_quantity'],
                key=f'wh_{i}',
                min_value=0
            )
            if new_warehouse != product['warehouse_quantity']:
                product['warehouse_quantity'] = new_warehouse
                save_products()
        
        with col3:
            new_store = st.number_input(
                '店面數量',
                value=product['store_quantity'],
                key=f'st_{i}',
                min_value=0
            )
            if new_store != product['store_quantity']:
                product['store_quantity'] = new_store
                save_products()
        
        with col4:
            st.text(f"總數量: {product['warehouse_quantity'] + product['store_quantity']}")
        
        with col5:
            new_notes = st.text_input(
                '備註',
                value=product['notes'],
                key=f'note_{i}'
            )
            if new_notes != product['notes']:
                product['notes'] = new_notes
                save_products()
        
        with col6:
            if st.button('🗑️', key=f'del_{i}'):
                st.session_state.products.remove(product)
                save_products()
                st.rerun()
        
        st.divider()
else:
    st.info('暫無產品數據')
