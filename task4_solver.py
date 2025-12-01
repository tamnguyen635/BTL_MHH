import pulp
import time
from common import get_petri_net_data
def check_deadlock_ilp():
    net_data = get_petri_net_data()
    print(f"\n=== BẮT ĐẦU TASK 4: TÌM DEADLOCK (ILP) ===")
    
    # 1. Dùng Parser của cậu để lấy dữ liệu
    # Parser trả về dict gồm: 'places', 'transitions', 'initial_marking', 'incidence_matrix'
    # Bắt đầu bấm giờ tổng
    start_total = time.time()
    
    if net_data is None:
        print(">> Lỗi: Không đọc được dữ liệu mạng.")
        return

    # Trích xuất dữ liệu cho gọn
    places = net_data['places']          # [{'id': 'p1', 'index': 0}, ...]
    transitions = net_data['transitions'] # [{'id': 't1', 'pre': [indices...]}, ...]
    m0 = net_data['initial_marking']      # [1, 0, 0, ...]
    matrix = net_data['incidence_matrix'] # [[-1, 0..], [1, -1..]]
    
    num_places = len(places)
    num_transitions = len(transitions)

    # 2. Khởi tạo bài toán ILP
    prob = pulp.LpProblem("PetriNet_Deadlock_Detection", pulp.LpMaximize)

    # --- Tạo biến số ---
    # M_i: Số token tại place index i (0 hoặc 1 vì là 1-safe)
    m_vars = {
        i: pulp.LpVariable(f"M_{i}", lowBound=0, upBound=1, cat='Integer') 
        for i in range(num_places)
    }

    # X_j: Số lần bắn của transition index j (>= 0)
    x_vars = {
        j: pulp.LpVariable(f"X_{j}", lowBound=0, cat='Integer') 
        for j in range(num_transitions)
    }

    # Hàm mục tiêu (Dummy)
    prob += 1

    # --- 3. Thêm các Ràng buộc (Constraints) ---

    # Ràng buộc A: Phương trình trạng thái (State Equation)
    # M = M0 + C * X  =>  Với mỗi place i: M[i] == M0[i] + sum(C[i][j] * X[j])
    for i in range(num_places):
        # Tính tổng thay đổi token: row i của ma trận nhân với vector X
        token_change = pulp.lpSum([matrix[i][j] * x_vars[j] for j in range(num_transitions)])
        
        prob += m_vars[i] == m0[i] + token_change, f"State_Eq_Place_{i}"

    # Ràng buộc B: Disablement Constraints (Điều kiện Deadlock)
    # Với mọi transition t: Tổng token tại các input places <= (Số lượng input - 1)
    for t_data in transitions:
        t_idx = transitions.index(t_data) # Lấy index của transition
        pre_indices = t_data['pre']       # Lấy danh sách index của input places (Parser đã làm sẵn cái này)
        
        if not pre_indices:
            # Nếu transition không có đầu vào (source transition), nó luôn bắn được -> ko bao giờ deadlock
            continue
            
        # Tổng token hiện có tại các input places
        sum_tokens_input = pulp.lpSum([m_vars[p_idx] for p_idx in pre_indices])
        
        # Bất đẳng thức: Sum <= K - 1
        prob += sum_tokens_input <= len(pre_indices) - 1, f"Disable_Trans_{t_idx}"

    # 4. Giải bài toán
    print(">> Đang chạy Solver...")
    start_solve = time.time()
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False)) 
    end_solve = time.time()
    # msg=False để tắt log rác của solver
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False)) 

    # 5. Phân tích kết quả
    if pulp.LpStatus[status] == 'Optimal':
        print("\n" + "="*40)
        print("!!! PHÁT HIỆN ỨNG VIÊN DEADLOCK (DEAD MARKING) !!!")
        print("="*40)
        
        # Mapping lại từ index sang ID để in cho dễ đọc
        dead_marking_ids = []
        dead_vector = []
        
        print("\n[1] Trạng thái Chết (M):")
        for i in range(num_places):
            val = int(m_vars[i].varValue)
            dead_vector.append(val)
            if val > 0:
                p_id = places[i]['id'] # Lấy ID từ index
                print(f"  - Place '{p_id}': 1 token")
                dead_marking_ids.append(p_id)
        
        print(f"  => Vector M: {dead_vector}")

        print("\n[2] Đường đi dẫn đến deadlock (Vector bắn X):")
        fired_any = False
        for j in range(num_transitions):
            val = int(x_vars[j].varValue)
            if val > 0:
                t_id = transitions[j]['id']
                print(f"  - Transition '{t_id}' bắn: {val} lần")
                fired_any = True
        
        if not fired_any:
            print("  (Ngay tại trạng thái khởi đầu M0 đã là deadlock)")

        print("\n[LƯU Ý QUAN TRỌNG]:")
        print("  Đây là 'Dead Marking' tìm thấy bởi phương trình trạng thái.")
        print("  Để chắc chắn 100% đây là Deadlock thật (Reachable),")
        print("  cần kiểm tra xem trạng thái M này có nằm trong cây BDD (Task 3) hay không.")
        
    else:
        print("\n[OK] Hệ thống an toàn (Không tìm thấy nghiệm Deadlock thỏa mãn phương trình).")
    end_total = time.time()
    print("-" * 50)
    print(f"[INFO] TỔNG THỜI GIAN CHẠY: {end_total - start_total:.6f} giây")
    print("-" * 50)
# ==========================================
# CHẠY THỬ
# ==========================================
if __name__ == "__main__":
    # Thay tên file pnml của cậu vào đây
    input_file = "test_task4.pnml" 
    check_deadlock_ilp()