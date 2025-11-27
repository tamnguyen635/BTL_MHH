import sys
from pnml_parser import parse_pnml  


#đổi file input ở đây
DEFAULT_FILENAME = "test_task3.pnml" 

def get_petri_net_data():
    """
    Hàm dùng chung cho tất cả các Task.
    Tự động lấy tên file từ dòng lệnh hoặc dùng mặc định.
    """
    # 1. Xác định file cần đọc
    # Nếu chạy: python task2.py my_file.pnml -> Lấy my_file.pnml
    # Nếu chạy: python task2.py              -> Lấy DEFAULT_FILENAME
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = DEFAULT_FILENAME
        print(f"--- Đang dùng file : {filename} ---")

    # 2. Gọi Parser của Task 1
    data = parse_pnml(filename)
    
    # 3. Kiểm tra kết quả
    if data is None:
        print(">>> LỖI FATAL: Không lấy được dữ liệu Petri Net. Dừng chương trình.")
        sys.exit(1) 
        
    return data

if __name__ == "__main__":
    data = get_petri_net_data()
    print("Dữ liệu đã sẵn sàng! ")