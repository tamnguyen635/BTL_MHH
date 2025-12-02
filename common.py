import sys
import os
from pnml_parser import parse_pnml  


#đổi file input ở đây
DEFAULT_FILENAME = "testcase/test_task4.pnml" 

def get_petri_net_data():
    """
    Hàm dùng chung cho tất cả các Task.
    Tự động lấy tên file từ dòng lệnh hoặc dùng mặc định.
    """
    # 1. Xác định file cần đọc
    # Nếu chạy: python task2.py testcase/my_file.pnml -> Lấy my_file.pnml
    # Nếu chạy: python task2.py                       -> Lấy DEFAULT_FILENAME
    
    if len(sys.argv) > 1:
        raw_filename = sys.argv[1]
    else:
        raw_filename = DEFAULT_FILENAME
        print(f"--- Đang dùng file mặc định: {raw_filename} ---")
    if os.path.exists(raw_filename):
        final_path = raw_filename
    else:
        path_in_folder = os.path.join("testcase", raw_filename)
        if os.path.exists(path_in_folder):
            final_path = path_in_folder
            print(f"-> Đã tìm thấy file trong thư mục testcase: {final_path}")
        else:
            final_path = raw_filename

    # 2. Gọi Parser của Task 1
    data = parse_pnml(final_path)
    
    # 3. Kiểm tra kết quả
    if data is None:
        print(">>> LỖI FATAL: Không lấy được dữ liệu Petri Net. Dừng chương trình.")
        sys.exit(1) 
    data['input_filename'] = final_path   
    return data

if __name__ == "__main__":
    data = get_petri_net_data()
    print("Dữ liệu đã sẵn sàng! Đọc từ:", data['input_filename'])