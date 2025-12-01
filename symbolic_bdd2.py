# symbolic_bdd3.py
import argparse
import json
import time
import sys
from pathlib import Path

# --- IMPORT MODULE CỦA BẠN ---
# 1. Import Parser để đọc và kiểm tra dữ liệu
try:
    from pnml_parser import parse_pnml
except ImportError:
    print("LỖI: Không tìm thấy file 'pnml_parser.py'. ")
    sys.exit(1)

# 2. Import các hàm hỗ trợ BDD
try:
    from bdd_utils import (
        build_transition_relation, 
        marking_to_bdd, 
        enumerate_markings_from_bdd,
        varname, varname_prime
    )
except ImportError:
    print("LỖI: Không tìm thấy file 'bdd_utils.py'. Hãy tạo file này trước.")
    sys.exit(1)

def symbolic_reachability_frontier(net, enum_limit=10000, verbose=False):
    """
    Thuật toán Frontier-Based BFS: Chỉ tính ảnh từ các trạng thái MỚI.
    Tối ưu hóa tốc độ và bộ nhớ so với BFS thông thường.
    """
    # Không cần validate lại vì parse_pnml đã làm rồi
    
    # Khởi động thư viện BDD
    try:
        from dd import autoref as _bdd
    except ImportError:
        raise RuntimeError("Thiếu thư viện 'dd'. Hãy chạy: pip install dd")

    places = net['places']
    transitions = net['transitions']
    n = len(places)

    bdd = _bdd.BDD()
    
    # 1. Khai báo biến (x: hiện tại, y: tiếp theo)
    x_vars = [varname(i) for i in range(n)]
    y_vars = [varname_prime(i) for i in range(n)]
    for v in x_vars + y_vars:
        bdd.declare(v)

    # 2. Xây dựng Relations (Disjunctive Partitioning)
    if verbose: print(f"-> Đang xây dựng quan hệ chuyển tiếp cho {len(transitions)} transitions...")
    R_list = []
    for t in transitions:
        Rt = build_transition_relation(bdd, n, t)
        R_list.append(Rt)

    # 3. Khởi tạo trạng thái ban đầu
    start_marking = net['initial_marking']
    bdd_M0 = marking_to_bdd(bdd, x_vars, start_marking)
    
    # --- THUẬT TOÁN FRONTIER BFS ---
    reachable = bdd_M0    # Tập đã biết
    frontier = bdd_M0     # Tập biên (chỉ chứa cái mới)
    
    rename_map = {varname_prime(i): varname(i) for i in range(n)}
    
    iteration = 0
    t0 = time.perf_counter()

    while True:
        # Nếu biên rỗng -> Đã khám phá hết
        if frontier == bdd.false:
            break

        iteration += 1
        if verbose:
            print(f"[Iter {iteration}] Đang mở rộng biên...")

        img_old_total = bdd.false
        
        # Tính ảnh chỉ từ FRONTIER (nhanh hơn nhiều so với Reachable)
        for Rt in R_list:
            # Bước 1: Frontier(x) & T(x,y)
            conj = frontier & Rt 
            
            # Optimization: Nếu không giao nhau thì bỏ qua quantify
            if conj != bdd.false:
                # Bước 2: Exists x -> Kết quả theo biến y
                img_new = bdd.quantify(conj, x_vars, forall=False)
                
                # Bước 3: Đổi tên y -> x
                img_old = bdd.let(rename_map, img_new)
                
                # Hợp vào tổng ảnh
                img_old_total = img_old_total | img_old

        # Tìm trạng thái THỰC SỰ MỚI: New = Image \ Reachable
        new_states = img_old_total & (~reachable)
        
        # Cập nhật Reachable: Reach = Reach U New
        reachable = reachable | new_states
        
        # Cập nhật Frontier cho vòng sau
        frontier = new_states
        
    t1 = time.perf_counter()
    bfs_depth = iteration - 1 # Trừ vòng lặp cuối (check rỗng)

    # 4. Liệt kê trạng thái (Enumeration) để báo cáo
    t2 = time.perf_counter()
    markings = []
    if enum_limit > 0:
        markings = enumerate_markings_from_bdd(bdd, reachable, x_vars, limit=enum_limit)
    t3 = time.perf_counter()

    reachable_count = len(markings)
    if enum_limit and len(markings) >= enum_limit:
        reachable_count_str = f">={enum_limit}" 
    else:
        reachable_count_str = str(reachable_count)

    return {
        'places': [{'id': p['id'], 'index': p['index']} for p in places],
        'transitions': [{'id': t['id'], 'index': i} for i, t in enumerate(transitions)],
        'initial_marking': start_marking,
        'reachable_count': reachable_count,
        'reachable_count_str': reachable_count_str,
        'bfs_depth': bfs_depth,
        'reachable_markings': markings,
        'bdd_time_s': t1 - t0,
        'enumeration_time_s': t3 - t2,
    }

def main():
    ap = argparse.ArgumentParser(description="BDD Reachability (Frontier-BFS)")
    ap.add_argument('pnml', help='Đường dẫn file PNML')
    ap.add_argument('--out', help='File xuất JSON', default=None)
    ap.add_argument('--enum_limit', type=int, default=10000, help='Giới hạn số trạng thái liệt kê')
    ap.add_argument('--verbose', action='store_true', help='Hiện chi tiết quá trình')
    
    args = ap.parse_args()

    pnml_path = Path(args.pnml)
    if not pnml_path.exists():
        print(f"LỖI: Không tìm thấy file {pnml_path}")
        return

    # --- GỌI PARSER CỦA BẠN ---
    print(f"--- Đọc và Kiểm tra file: {pnml_path.name} ---")
    
    # Hàm parse_pnml này sẽ tự gọi check_consistency() bên trong
    # Nếu có lỗi, nó trả về None hoặc parser sẽ in lỗi ra màn hình
    net_data = parse_pnml(str(pnml_path))
    
    if net_data is None:
        print(">>> HỦY TASK: Dữ liệu đầu vào không hợp lệ.")
        return

    # --- CHẠY THUẬT TOÁN BDD ---
    try:
        print(f"--- Bắt đầu Symbolic Reachability (Frontier-BFS) ---")
        res = symbolic_reachability_frontier(
            net_data,
            enum_limit=args.enum_limit,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"LỖI RUNTIME: {e}")
        import traceback
        traceback.print_exc()
        return

    # --- XUẤT KẾT QUẢ ---
    res['symbolic_time_s'] = res['bdd_time_s']
    out_path = args.out or (pnml_path.with_suffix('.reach_bdd.json').name)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
        
    print(f"\n--- HOÀN THÀNH TASK 3 ---")
    print(f"Output File  : {out_path}")
    print(f"Reachable    : {res['reachable_count_str']}")
    print(f"BFS Depth    : {res['bfs_depth']}")
    print(f"Time (BDD)   : {res['bdd_time_s']:.6f}s")

if __name__ == '__main__':
    main()