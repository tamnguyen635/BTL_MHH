import time
import sys
from dd import autoref as dd
from common import get_petri_net_data

def build_bdd_logic(data):
    """
    Hàm chính thực hiện Task 3: Tính toán không gian trạng thái bằng BDD.
    """
    # 1. Lấy dữ liệu từ Parser
    places = data['places']             
    transitions = data['transitions']   
    initial_marking = data['initial_marking'] 
    
    num_places = len(places)
    
    print(f"--- [TASK 3] SYMBOLIC BDD REACHABILITY ---")
    print(f"Model Info: {num_places} places, {len(transitions)} transitions")

    # 2. Khởi tạo BDD Manager
    bdd = dd.BDD()
    
    # Khai báo biến:
    # x_i: trạng thái hiện tại (current state) của place i
    # y_i: trạng thái tiếp theo (next state) của place i
    x_vars = [f'x_{i}' for i in range(num_places)]
    y_vars = [f'y_{i}' for i in range(num_places)]
    
    # Đăng ký biến với BDD manager
    for var in x_vars + y_vars:
        bdd.declare(var)
        
    # Dict dùng để đổi tên biến (phục vụ bước next -> current)
    rename_dict = {y: x for x, y in zip(x_vars, y_vars)}

    # ==========================================================
    # 3. MÃ HÓA TRẠNG THÁI BAN ĐẦU (INITIAL MARKING - M0)
    # ==========================================================
    # Logic: (x0 <-> val0) AND (x1 <-> val1) ...
    m0_parts = []
    for i, token_count in enumerate(initial_marking):
        # 1-safe net: token > 0 là TRUE, = 0 là FALSE
        val = 'TRUE' if token_count > 0 else 'FALSE'
        m0_parts.append(f'(x_{i} <-> {val})')
    
    m0_expr = ' & '.join(m0_parts)
    bdd_M0 = bdd.add_expr(m0_expr)
    print("-> Đã mã hóa Initial Marking (M0).")

    # ==========================================================
    # 4. MÃ HÓA QUAN HỆ CHUYỂN TIẾP (TRANSITION RELATION - R)
    # ==========================================================
    # R(x, y) = OR ( Relation_t1, Relation_t2, ... )
    # Relation_t = (Pre_cond) AND (Post_logic) AND (Frame_axiom)
    
    trans_bdd_list = []
    
    for t in transitions:
        pre_indexes = set(t['pre'])
        post_indexes = set(t['post'])
        
        # a. Pre-condition: Tất cả input places phải có token (=1)
        # Ví dụ: x_1 & x_3
        pre_cond = [f'x_{i}' for i in pre_indexes]
        
        # b. Change Logic & Frame Axiom
        # Quy tắc cập nhật cho TỪNG place i trong mạng:
        change_parts = []
        for i in range(num_places):
            if i in pre_indexes and i not in post_indexes:
                # Place bị lấy mất token -> Next state = 0
                change_parts.append(f'!y_{i}') 
            elif i in post_indexes:
                # Place nhận được token -> Next state = 1
                change_parts.append(f'y_{i}')  
            else:
                # Place không liên quan -> Giữ nguyên trạng thái (Frame Axiom)
                # y_i <-> x_i
                change_parts.append(f'(x_{i} <-> y_{i})')
        
        # Hợp nhất logic cho 1 transition
        # Nếu pre_cond rỗng (trans nguồn), coi như TRUE
        pre_expr = ' & '.join(pre_cond) if pre_cond else 'TRUE'
        change_expr = ' & '.join(change_parts)
        
        full_t_expr = f'({pre_expr}) & ({change_expr})'
        trans_bdd_list.append(bdd.add_expr(full_t_expr))
        
    # Hợp (OR) tất cả các transition lại
    if not trans_bdd_list:
        bdd_Rel = bdd.false
    else:
        bdd_Rel = trans_bdd_list[0]
        for t_bdd in trans_bdd_list[1:]:
            bdd_Rel = bdd_Rel | t_bdd
            
    print("-> Đã xây dựng Transition Relation (R).")

    # ==========================================================
    # 5. TÍNH TOÁN TẬP REACHABLE (Fixed Point Iteration)
    # ==========================================================
    # Reach = M0
    # New = M0
    # Loop:
    #    Next = Image(New, R)
    #    New_Real = Next \ Reach
    #    If New_Real is Empty -> Break
    #    Reach = Reach U New_Real
    #    New = New_Real
    
    bdd_Reach = bdd_M0
    bdd_New = bdd_M0
    
    step = 0
    start_time = time.time()
    
    while True:
        step += 1
        
        # [Image Computation]: Tìm tất cả trạng thái y có thể đến từ x (trong tập New)
        # Exists x. (New(x) AND R(x, y))
        bdd_Next_Y = bdd.quantify(bdd_New & bdd_Rel, x_vars, forall=False)
        
        # Đổi tên biến Y về X để so sánh với tập Reach hiện tại
        bdd_Next_X = bdd.let(rename_dict, bdd_Next_Y)
        
        # Tìm phần tử mới chưa từng thấy
        # Delta = Next_X AND (NOT Reach)
        bdd_Delta = bdd_Next_X & (~bdd_Reach)
        
        # Điều kiện dừng: Không còn trạng thái mới
        if bdd_Delta == bdd.false:
            break
            
        # Cập nhật tập Reachable
        bdd_Reach = bdd_Reach | bdd_Delta
        
        # Cập nhật tập biên (Frontier) để duyệt tiếp
        bdd_New = bdd_Delta

    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # ==========================================================
    # 6. BÁO CÁO KẾT QUẢ
    # ==========================================================
    # Đếm số lượng trạng thái thỏa mãn công thức Reachable
    total_states = bdd_Reach.count(nvars=num_places)
    
    print("\n" + "="*40)
    print(f" KẾT QUẢ TASK 3 (BDD)")
    print("="*40)
    print(f" Tổng số trạng thái (Reachable): {total_states}")
    print(f" Thời gian thực thi: {elapsed_time:.6f} giây")
    print(f" Số bước lặp (BFS Depth): {step}")
    print("="*40 + "\n")
    
    return bdd, bdd_Reach, x_vars

if __name__ == "__main__":
    # Tự động lấy file input từ dòng lệnh (nhờ common.py)
    data = get_petri_net_data()
    if data:
        build_bdd_logic(data)