# symbolic_bdd2.py
import argparse
import json
import time
import sys
from pathlib import Path

try:
    from pnml_parser import parse_pnml
    from bdd_utils import build_transition_relation, marking_to_bdd, enumerate_markings_from_bdd, varname, varname_prime
except ImportError as e:
    print(f"Lỗi Import: {e}")
    sys.exit(1)

def symbolic_reachability_frontier(net, enum_limit=10000, verbose=False):
    """Thuật toán Frontier-Based BFS"""
    try:
        from dd import autoref as _bdd
    except ImportError:
        raise RuntimeError("Thiếu thư viện 'dd'. Hãy chạy: pip install dd")

    places = net['places']
    transitions = net['transitions']
    n = len(places)
    bdd = _bdd.BDD()
    
    x_vars = [varname(i) for i in range(n)]
    y_vars = [varname_prime(i) for i in range(n)]
    for v in x_vars + y_vars: bdd.declare(v)

    if verbose: print(f"-> Xây dựng quan hệ chuyển tiếp ({len(transitions)} transitions)...")
    R_list = [build_transition_relation(bdd, n, t) for t in transitions]

    start_marking = net['initial_marking']
    bdd_M0 = marking_to_bdd(bdd, x_vars, start_marking)
    
    reachable = bdd_M0    
    frontier = bdd_M0     
    rename_map = {varname_prime(i): varname(i) for i in range(n)}
    
    iteration = 0
    t0 = time.perf_counter()

    while frontier != bdd.false:
        iteration += 1
        if verbose: print(f"[Iter {iteration}] Mở rộng biên...")
        img_old_total = bdd.false
        for Rt in R_list:
            conj = frontier & Rt 
            if conj != bdd.false:
                img_new = bdd.quantify(conj, x_vars, forall=False)
                img_old_total |= bdd.let(rename_map, img_new)

        new_states = img_old_total & (~reachable)
        reachable |= new_states
        frontier = new_states
        
    t1 = time.perf_counter()
    
    t2 = time.perf_counter()
    markings = []
    if enum_limit > 0:
        markings = enumerate_markings_from_bdd(bdd, reachable, x_vars, limit=enum_limit)
    t3 = time.perf_counter()

    return {
        'places': [{'id': p['id'], 'index': p['index']} for p in places],
        'initial_marking': start_marking,
        'reachable_count': len(markings),
        'bfs_depth': iteration - 1,
        'reachable_markings': markings,
        'bdd_time_s': t1 - t0,
        'enumeration_time_s': t3 - t2,
    }

def save_result_to_json(res, pnml_path_str):
    """Hàm phụ trợ để lưu file vào folder result_task3"""
    pnml_path = Path(pnml_path_str)
    
    # 1. Tạo folder output nếu chưa có
    output_dir = Path("result_task3")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Tạo tên file output (lấy tên gốc, bỏ phần thư mục cha nếu có)
    # Ví dụ input: testcase/deadlock.pnml -> output: result_task3/deadlock.reach_bdd.json
    file_name = pnml_path.with_suffix('.reach_bdd.json').name
    out_path = output_dir / file_name
    
    res['symbolic_time_s'] = res['bdd_time_s']
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
        
    return str(out_path)

def run_task3(pnml_path_str, enum_limit=10000, verbose=False):
    """Wrapper cho Task 4 gọi"""
    if not Path(pnml_path_str).exists():
        print(f"Lỗi: Không tìm thấy file {pnml_path_str}")
        return None, None

    net_data = parse_pnml(str(pnml_path_str))
    if net_data is None: return None, None

    try:
        res = symbolic_reachability_frontier(net_data, enum_limit, verbose)
        # Gọi hàm lưu file chuẩn folder
        out_path = save_result_to_json(res, pnml_path_str)
        return res, out_path
    except Exception as e:
        print(f"Lỗi BDD: {e}")
        return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pnml', help='File PNML')
    ap.add_argument('--out', help='File xuất (Tùy chọn)')
    args = ap.parse_args()

    # Nếu chạy trực tiếp thì gọi hàm wrapper luôn cho đồng bộ
    res, saved_path = run_task3(args.pnml)
    if res:
        print(f"\n--- HOÀN THÀNH TASK 3 ---")
        print(f"Output saved to: {saved_path}")

if __name__ == '__main__':
    main()