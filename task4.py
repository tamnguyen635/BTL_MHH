# task4.py
import pulp
import time
import json
import os
from pathlib import Path
from common import get_petri_net_data

def get_bdd_result_path(pnml_file_path):
    """
    Hàm tính toán đường dẫn file JSON kết quả từ tên file PNML.
    Logic: testcase/deadlock.pnml -> result_task3/deadlock.reach_bdd.json
    """
    # Lấy tên file gốc (bỏ thư mục cha, bỏ đuôi .pnml)
    # Ví dụ: "testcase/deadlock_test.pnml" -> "deadlock_test"
    file_stem = Path(pnml_file_path).stem
    
    # Tạo đường dẫn tới folder result_task3
    json_path = Path("result_task3") / f"{file_stem}.reach_bdd.json"
    return json_path

def verify_deadlock_with_json(dead_vector, json_path):
    """Đọc file JSON và kiểm tra vector"""
    print(f"\n>> Đang đối chiếu với kết quả Task 3...")
    print(f"   (Nguồn dữ liệu: {json_path})")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        reachable_set = data.get('reachable_markings', [])
        
        if dead_vector in reachable_set:
            print("\n" + "="*60)
            print(">>> KẾT LUẬN CUỐI CÙNG: DEADLOCK XÁC THỰC (REAL DEADLOCK) <<<")
            print("="*60)
            print("  [OK] Trạng thái này ĐÃ ĐƯỢC TÌM THẤY trong tập Reachable (Task 3).")
        else:
            print("\n" + "="*50)
            print(">>> KẾT LUẬN: DEADLOCK GIẢ (SPURIOUS) <<<")
            print("="*50)
            print("  [!] Trạng thái này KHÔNG THỂ ĐẠT TỚI được (Unreachable).")
            
    except Exception as e:
        print(f"Lỗi khi đọc file JSON: {e}")

def check_deadlock_ilp():
    print(f"\n=== BẮT ĐẦU TASK 4: TÌM DEADLOCK (ILP) ===")
    start_total = time.time()

    # 1. PARSER (Lấy dữ liệu từ common)
    net_data = get_petri_net_data()
    if net_data is None: return
    
    # Lấy tên file input để tí nữa tìm file JSON tương ứng
    input_filename = net_data.get('input_filename')
    print(f"-> Đang xử lý cho file: {input_filename}")

    places = net_data['places']
    transitions = net_data['transitions']
    m0 = net_data['initial_marking']
    matrix = net_data['incidence_matrix']
    num_places = len(places)
    num_transitions = len(transitions)

    # 2. ILP SOLVER
    prob = pulp.LpProblem("PetriNet_Deadlock", pulp.LpMaximize)
    m_vars = {i: pulp.LpVariable(f"M_{i}", 0, 1, 'Integer') for i in range(num_places)}
    x_vars = {j: pulp.LpVariable(f"X_{j}", 0, cat='Integer') for j in range(num_transitions)}
    prob += 1 

    # Ràng buộc trạng thái
    for i in range(num_places):
        token_change = pulp.lpSum([matrix[i][j] * x_vars[j] for j in range(num_transitions)])
        prob += m_vars[i] == m0[i] + token_change

    # Ràng buộc Deadlock
    for t_data in transitions:
        pre = t_data['pre']
        if pre:
            prob += pulp.lpSum([m_vars[p] for p in pre]) <= len(pre) - 1

    print(">> Đang chạy Solver ILP...")
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False)) 

    # 3. KẾT HỢP TASK 3 (CHỈ ĐỌC FILE)
    if pulp.LpStatus[status] == 'Optimal':
        print("\n[INFO] ILP tìm thấy ứng viên Dead Marking:")
        dead_vector = []
        for i in range(num_places):
            val = int(m_vars[i].varValue)
            dead_vector.append(val)
            if val > 0:
                print(f"  - {places[i]['id']}: 1")
        
        # --- ĐOẠN NÀY ĐÃ ĐƯỢC SỬA ---
        # Tự động tính đường dẫn file JSON trong folder result_task3
        json_path = get_bdd_result_path(input_filename)
        
        if json_path.exists():
            verify_deadlock_with_json(dead_vector, json_path)
        else:
            print(f"\n[CẢNH BÁO] Không tìm thấy file kết quả Task 3 tại:")
            print(f"   {json_path}")
            print(">> Hãy chạy Task 3 trước: python symbolic_bdd2.py ...")
            
    else:
        print("\n[OK] Hệ thống an toàn (ILP không tìm thấy nghiệm).")

    print("-" * 50)
    print(f"[TOTAL TIME]: {time.time() - start_total:.6f} s")

if __name__ == "__main__":
    check_deadlock_ilp()