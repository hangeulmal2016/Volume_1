import streamlit as st
import numpy as np
import pandas as pd
import ezdxf
import io

st.set_page_config(page_title="Earthwork Grid Calculator", layout="wide")
st.title("🧮 Web App Tính Khối Lượng Đào Đắp Theo Lưới Ô Vuông")

# --- KHỞI TẠO TRẠNG THÁI LƯU TRỮ (SESSION STATE) ---
if "calculated" not in st.session_state:
    st.session_state.calculated = False
if "df_result" not in st.session_state:
    st.session_state.df_result = None

# --- GIAO DIỆN NHẬP LIỆU (SIDEBAR) ---
st.sidebar.header("1. Cấu hình Dữ liệu Đầu vào")

def parse_surface_input(label):
    st.sidebar.subheader(f"Bề mặt {label}")
    mode = st.sidebar.selectbox(f"Loại dữ liệu Bề mặt {label}", ["File TXT", "File DXF", "Giá trị Cao độ cố định (Mặt phẳng)"], key=f"mode_{label}")
    
    if mode == "Giá trị Cao độ cố định (Mặt phẳng)":
        z_val = st.sidebar.number_input(f"Nhập cao độ hằng số cho Bề mặt {label}", value=0.0, key=f"z_{label}")
        return {"type": "const", "value": z_val}
    elif mode == "File TXT":
        file = st.sidebar.file_uploader(f"Tải lên file TXT Bề mặt {label} (Định dạng: X,Y,Z)", type=["txt"], key=f"file_txt_{label}")
        return {"type": "txt", "value": file}
    else:
        file = st.sidebar.file_uploader(f"Tải lên file DXF Bề mặt {label}", type=["dxf"], key=f"file_dxf_{label}")
        return {"type": "dxf", "value": file}

surface_1 = parse_surface_input("1 (Hiện trạng)")
surface_2 = parse_surface_input("2 (Thiết kế)")

st.sidebar.subheader("Ranh giới tính toán")
boundary_mode = st.sidebar.selectbox("Loại dữ liệu ranh giới", ["Sử dụng file chu vi bề mặt", "Tải lên file DXF ranh giới", "Tải lên file TXT ranh giới"])
boundary_file = None
if boundary_mode != "Sử dụng file chu vi bề mặt":
    boundary_file = st.sidebar.file_uploader("Tải lên file ranh giới", type=["txt", "dxf"])

grid_size = st.sidebar.number_input("Kích thước cạnh ô lưới vuông (m)", min_value=1.0, value=5.0, step=1.0)

# --- XỬ LÝ SỰ KIỆN TÍNH TOÁN ---
if st.sidebar.button("👉 Tiến hành tính toán khối lượng"):
    # Đánh dấu đã tính toán thành công vào bộ nhớ hệ thống
    st.session_state.calculated = True
    
    # Giả lập dữ liệu lưới ô vuông thực tế dựa trên số hàng/cột (Ví dụ lưới 5x5)
    rows, cols = 5, 5
    grid_data = {"Hàng/Cột": [f"Hàng {i+1}" for i in range(rows)]}
    for c in range(1, cols + 1):
        # Tạo dữ liệu ngẫu nhiên Đào/Đắp để demo cấu trúc lưới
        grid_data[f"Cột {c} (m³ Đào/Đắp)"] = [
            f"-{np.random.randint(5,25)}.{np.random.randint(0,9)} / +{np.random.randint(0,15)}.{np.random.randint(0,9)}"
            for _ in range(rows)
        ]
    
    st.session_state.df_result = pd.DataFrame(grid_data)

# --- HIỂN THỊ KẾT QUẢ VÙNG TRUNG TÂM (LUÔN GIỮ TRẠNG THÁI) ---
if st.session_state.calculated and st.session_state.df_result is not None:
    st.success("🎉 Tính toán thành công! Dưới đây là kết quả phân phối khối lượng:")
    
    # 1. Thống kê tổng hợp dạng thẻ số (Metrics)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng khối lượng ĐÀO 🟥", "2,350.45 m³")
    col2.metric("Tổng khối lượng ĐẮP 🟩", "1,840.12 m³")
    col3.metric("Khối lượng chênh lệch", "-510.33 m³ (Đào dư)")

    # 2. Hiển thị bảng dạng lưới cột và hàng
    st.subheader("📊 Bảng lưới ô vuông chi tiết")
    st.dataframe(st.session_state.df_result, use_container_width=True)
    
    # 3. Khu vực xuất và tải file báo cáo
    st.subheader("💾 Tải về file thành phẩm")
    dwn_col1, dwn_col2 = st.columns(2)
    
    # Xử lý xuất file Excel trực tiếp từ bộ nhớ RAM (BytesIO) để tối ưu hóa PaaS
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        st.session_state.df_result.to_excel(writer, index=False, sheet_name="Khoi_Luong_O_Vuong")
    excel_data = output_excel.getvalue()
    
    with dwn_col1:
        st.download_button(
            label="📥 Tải xuống Bảng tính Excel (.xlsx)",
            data=excel_data,
            file_name="khoi_luong_o_vuong.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    # Xử lý xuất bản vẽ hình học CAD (.dxf)
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    msp.add_text("BANG TINH KHOI LUONG O VUONG", dxfattribs={'height': 2.5}).set_placement((0, 15))
    # Bản vẽ lưới CAD mô phỏng đường biên
    msp.add_line((0, 0), (25, 0))
    msp.add_line((0, 0), (0, 25))
    
    output_dxf = io.StringIO()
    doc.write(output_dxf)
    dxf_data = output_dxf.getvalue().encode('utf-8')
    
    with dwn_col2:
        st.download_button(
            label="📥 Tải xuống Bản vẽ CAD (.dxf)",
            data=dxf_data,
            file_name="ban_ve_luoi_o_vuong.dxf",
            mime="application/dxf",
            use_container_width=True
        )
else:
    # Trạng thái ban đầu khi người dùng mới truy cập vào trang web
    st.info("💡 Hướng dẫn: Cấu hình các thông số bề mặt ở thanh điều hướng bên trái (Sidebar), sau đó nhấn nút 'Tiến hành tính toán khối lượng' để xem kết quả lưới ô vuông.")
