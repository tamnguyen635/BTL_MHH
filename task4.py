# task4.py
import pulp
import time
import os
from common import get_petri_net_data

try:
    from symbolic_bdd2 import run_task3
except ImportError:
    run_task3 = None
    print("[WARN] Không tìm thấy symbolic_bdd2.py")

def verify_deadlock_with_bdd(dead_vector, bdd_data, bdd_file_path):
    """Kiểm chứng deadlock"""
    # In ra đường dẫn file để cậu yên tâm là nó đọc đúng chỗ
    print(f"\n>> Đang đối chiếu với kết quả Task 3...")
    print(f"   (Nguồn dữ liệu: {bdd_file_path})")
    
    reachable_set = bdd_data.get('reachable_markings', [])
    
    if dead_vector in reachable_set:
        print("\n" + "="*60)
        print(">>> KẾT LUẬN CUỐI CÙNG: DEADLOCK XÁC THỰC (REAL DEADLOCK) <<<")
        print("="*60)
        print("  [OK] Trạng thái này ĐÃ ĐƯỢC TÌM THẤY trong tập Reachable.")
    else:
        print("\n" + "="*50)
        print(">>> KẾT LUẬN: DEADLOCK GIẢ (SPURIOUS) <<<")
        print("="*50)
        print("  [!] Trạng thái này KHÔNG THỂ ĐẠT TỚI được (Unreachable).")

def check_deadlock_ilp():
    print(f"\n=== BẮT ĐẦU TASK 4: TÌM DEADLOCK (ILP) ===")
    start_total = time.time()

    # 1. PARSER (Tự tìm file trong folder testcase nhờ common.py)
    net_data = get_petri_net_data()
    if net_data is None: return
    
    input_filename = net_data.get('input_filename')
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

    for i in range(num_places):
        token_change = pulp.lpSum([matrix[i][j] * x_vars[j] for j in range(num_transitions)])
        prob += m_vars[i] == m0[i] + token_change

    for t_data in transitions:
        pre = t_data['pre']
        if pre:
            prob += pulp.lpSum([m_vars[p] for p in pre]) <= len(pre) - 1

    print(">> Đang chạy Solver ILP...")
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False)) 

    # 3. KẾT HỢP TASK 3
    if pulp.LpStatus[status] == 'Optimal':
        print("\n[INFO] ILP tìm thấy ứng viên Dead Marking:")
        dead_vector = []
        for i in range(num_places):
            val = int(m_vars[i].varValue)
            dead_vector.append(val)
            if val > 0:
                print(f"  - {places[i]['id']}: 1")
        
        if run_task3:
            print(f"\n>> Đang gọi Task 3 để kiểm tra tính Reachable...")
            # Hàm run_task3 bây giờ sẽ tự lưu vào folder result_task3 
            # và trả về đường dẫn đúng đó.
            bdd_data, bdd_path = run_task3(input_filename, verbose=False)
            
            if bdd_data:
                verify_deadlock_with_bdd(dead_vector, bdd_data, bdd_path)
            else:
                print(">> Lỗi khi chạy Task 3.")
    else:
        print("\n[OK] Hệ thống an toàn (ILP không tìm thấy nghiệm).")

    print("-" * 50)
    print(f"[TOTAL TIME]: {time.time() - start_total:.6f} s")

if __name__ == "__main__":
    check_deadlock_ilp()