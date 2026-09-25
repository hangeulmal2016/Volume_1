import streamlit as st
import numpy as np
import pandas as pd
import ezdxf
from shapely.geometry import Polygon, Point
from scipy.interpolate import griddata
import io

st.set_page_config(page_title="Earthwork Grid Calculator", layout="wide")
st.title("🧮 Web App Tính Khối Lượng Đào Đắp Theo Lưới Ô Vuông")

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

surface_1 = parse_surface_input("1 (Hiện trạng/Tự nhiên)")
surface_2 = parse_surface_input("2 (Thiết kế/Hoàn thiện)")

st.sidebar.subheader("Ranh giới tính toán")
boundary_mode = st.sidebar.selectbox("Loại dữ liệu ranh giới", ["Sử dụng file chu vi bề mặt", "Tải lên file DXF ranh giới", "Tải lên file TXT ranh giới"])
boundary_file = None
if boundary_mode != "Sử dụng file chu vi bề mặt":
    boundary_file = st.sidebar.file_uploader("Tải lên file ranh giới", type=["txt", "dxf"])

grid_size = st.sidebar.number_input("Kích thước cạnh ô lưới vuông (m)", min_value=1.0, value=5.0, step=1.0)

# --- HÀM XỬ LÝ ĐỌC FILE (MÔ PHỎNG THUẬT TOÁN) ---
def load_points(surface_dict):
    if surface_dict["type"] == "const":
        return None  # Sẽ nội suy dạng mặt phẳng hằng số sau
    if surface_dict["value"] is None:
        return None
    
    points = []
    if surface_dict["type"] == "txt":
        content = surface_dict["value"].read().decode("utf-8")
        for line in content.strip().split("\n"):
            try:
                x, y, z = map(float, line.replace(",", " ").split())
                points.append([x, y, z])
            except:
                continue
    return np.array(points)

# --- NÚT KÍCH HOẠT TÍNH TOÁN ---
if st.sidebar.button("👉 Tiến hành tính toán khối lượng"):
    pts1 = load_points(surface_1)
    pts2 = load_points(surface_2)
    
    # Giả định tạo vùng tọa độ giả lập phục vụ giao diện minh họa nếu chưa up file
    if pts1 is None and surface_1["type"] != "const":
        st.warning("Vui lòng tải lên dữ liệu Bề mặt 1 hợp lệ.")
    else:
        st.info("Đang xử lý thuật toán hình học và nội suy cao độ không gian...")
        
        # [Thuật toán xử lý nội suy logic ở đây...]
        # Tạo bảng DataFrame kết quả mẫu dạng hàng và cột để hiển thị trực quan
        rows, cols = 5, 5
        grid_data = {
            "Hàng/Cột": [f"Hàng {i+1}" for i in range(rows)],
            "Cột 1 (m³ Đào/Đắp)": ["-15.2 / +0.0", "-5.1 / +2.3", "0.0 / +12.4", "-8.0 / +1.0", "0.0 / +20.5"],
            "Cột 2 (m³ Đào/Đắp)": ["-12.0 / +0.0", "-2.1 / +5.0", "0.0 / +14.2", "-4.0 / +3.0", "-1.0 / +10.5"],
            "Cột 3 (m³ Đào/Đắp)": ["-9.2 / +1.0", "0.0 / +8.3", "0.0 / +11.1", "-3.5 / +2.2", "0.0 / +15.0"],
            "Cột 4 (m³ Đào/Đắp)": ["-22.1 / +0.0", "-1.1 / +9.1", "-1.0 / +8.4", "0.0 / +6.1", "-5.0 / +2.0"],
            "Cột 5 (m³ Đào/Đắp)": ["-5.0 / +2.5", "0.0 / +12.0", "-2.0 / +4.0", "-7.1 / +0.0", "-12.3 / +0.0"]
        }
        df_result = pd.DataFrame(grid_data)
        
        # Hiển thị kết quả lên web app dạng lưới
        st.subheader("📊 Kết quả phân phối khối lượng theo lưới ô vuông")
        st.dataframe(df_result, use_container_width=True)
        
        # Thống kê tổng hợp
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng khối lượng ĐÀO 🟥", "2,350.45 m³")
        col2.metric("Tổng khối lượng ĐẮP 🟩", "1,840.12 m³")
        col3.metric("Khối lượng chênh lệch (Cần điều phối)", "-510.33 m³ (Đào dư)")

        # --- XUẤT FILE CHO NGƯỜI DÙNG TẢI VỀ ---
        st.subheader("💾 Tải về file báo cáo thành phẩm")
        
        # 1. Xuất file Excel
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df_result.to_excel(writer, index=False, sheet_name="Earthwork_Grid")
        excel_data = output_excel.getvalue()
        
        st.download_button(
            label="📥 Tải xuống Bảng tính Excel (.xlsx)",
            data=excel_data,
            file_name="khoi_luong_o_vuong.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # 2. Xuất file CAD DXF
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        # Tạo chữ và khung lưới trong CAD mẫu
        msp.add_text("BANG TINH KHOI LUONG O VUONG", dxfattribs={'height': 2.5}).set_placement((0, 10))
        # (Ở mã nguồn thực tế, vòng lặp msp.add_line() và msp.add_text() sẽ vẽ chính xác tọa độ các ô lưới)
        
        output_dxf = io.StringIO()
        doc.write(output_dxf)
        dxf_data = output_dxf.getvalue().encode('utf-8')
        
        st.download_button(
            label="📥 Tải xuống File bản vẽ CAD (.dxf)",
            data=dxf_data,
            file_name="ban_ve_luoi_o_vuong.dxf",
            mime="application/dxf"
        )
