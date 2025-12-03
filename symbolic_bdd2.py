# symbolic_bdd2.py
import argparse
import json
import time
import sys
from pathlib import Path

# --- IMPORT MODULE ---
try:
    # Import từ common.py
    from common import get_petri_net_data, parse_pnml
except ImportError:
    print("CRITICAL ERROR: Missing 'common.py'. Please ensure it exists in the same directory.")
    sys.exit(1)

try:
    # Import từ bdd_utils.py
    from bdd_utils import (
        build_transition_relation, 
        marking_to_bdd, 
        enumerate_markings_from_bdd,
        varname, varname_prime
    )
except ImportError:
    print("CRITICAL ERROR: Miss'bdd_utils.py'")
    sys.exit(1)

def compute_reachable_states_bdd(petri_model, max_enum=10000):
    """
    using Frontier-Set optimization.

    """
    # Load BDD library
    try:
        from dd import autoref as _bdd_lib
    except ImportError:
        raise RuntimeError("pip install dd")

    # 1. Extract Model Data
    place_list = petri_model['places']
    trans_list = petri_model['transitions']
    num_places = len(place_list)

    # Initialize BDD Manager
    manager = _bdd_lib.BDD()
    
  
    curr_vars = [varname(i) for i in range(num_places)]
    next_vars = [varname_prime(i) for i in range(num_places)]
    
    for v in curr_vars + next_vars:
        manager.declare(v)


    rel_list = []
    for t_obj in trans_list:
        # Build relation for single transition
        rel_t = build_transition_relation(manager, num_places, t_obj)
        rel_list.append(rel_t)


    init_marking_vec = petri_model['initial_marking']
    bdd_init = marking_to_bdd(manager, curr_vars, init_marking_vec)
    
    # --- FRONTIER BFS ALGORITHM ---
    visited_bdd = bdd_init      # Set of ALL reached states
    frontier_bdd = bdd_init     # Set of NEWLY found states
    
    # Map for renaming Next vars -> Current vars
    swap_map = {varname_prime(i): varname(i) for i in range(num_places)}
    
    step_count = 0
    start_time = time.perf_counter()

    while True:
        # Termination condition: No new states in frontier
        if frontier_bdd == manager.false:
            break

        step_count += 1
        
        # Compute Image: Next = Exists(Frontier & Relation)
        accumulated_image = manager.false
        
        for rel_t in rel_list:
            # Conjunction: Intersection of Frontier and Transition Logic
            intersection = frontier_bdd & rel_t 
            
      
            if intersection != manager.false:
            
                img_next_vars = manager.quantify(intersection, curr_vars, forall=False)
                
     
                img_curr_vars = manager.let(swap_map, img_next_vars)
                
                # Union with accumulated results
                accumulated_image = accumulated_image | img_curr_vars

        diff_states = accumulated_image & (~visited_bdd)
        
        # Update Visited set
        visited_bdd = visited_bdd | diff_states
        
        frontier_bdd = diff_states
        
    # Algorithm finished
    exec_time = time.perf_counter() - start_time
    depth = step_count - 1 

    # 5. Enumeration
    enum_start = time.perf_counter()
    state_list = []
    if max_enum > 0:
        state_list = enumerate_markings_from_bdd(manager, visited_bdd, curr_vars, limit=max_enum)
    enum_time = time.perf_counter() - enum_start

    total_count = len(state_list)
    count_display = f">={max_enum}" if (max_enum and total_count >= max_enum) else str(total_count)

    # 6. Construct Result Dictionary
    result_data = {
        'places': [{'id': p['id'], 'index': p['index']} for p in place_list],
        'transitions': [{'id': t['id'], 'index': i} for i, t in enumerate(trans_list)],
        'initial_marking': init_marking_vec,
        'reachable_count': total_count,
        'reachable_count_str': count_display,
        'bfs_depth': depth,
        'reachable_markings': state_list,
        'bdd_time_s': exec_time,
        'enumeration_time_s': enum_time,
        # Objects for downstream tasks (Task 4/5)
        'bdd_manager': manager,       
        'reachable_bdd': visited_bdd,
        'variables': curr_vars 
    }
    return result_data

def main_execution():
    """
    Main entry point 
    """
    parser = argparse.ArgumentParser(description="Symbolic Reachability Analysis")
    parser.add_argument('pnml', nargs='?', help='Path to PNML file')
    parser.add_argument('--out', help='Output JSON path', default=None)
    parser.add_argument('--enum_limit', type=int, default=10000, help='Max states to enumerate')
   
    
    args = parser.parse_args()

    
    model_data = get_petri_net_data()

    # Determine paths
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        input_path = Path(sys.argv[1])
    else:
        input_path = Path("test_task3.pnml") 

    # --- EXECUTE ANALYSIS ---
    try:
        print(f"--- Starting BDD Analysis ---")
        results = compute_reachable_states_bdd(
            model_data,
            max_enum=args.enum_limit
        )
    except Exception as e:
        print(f"RUNTIME ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # --- EXPORT RESULTS ---
    results['symbolic_time_s'] = results['bdd_time_s']
    output_filename = args.out or (input_path.with_suffix('.reach_bdd.json').name)
    
  
    json_safe_data = results.copy()
    keys_to_remove = ['bdd_manager', 'reachable_bdd', 'variables']
    for k in keys_to_remove:
        if k in json_safe_data: del json_safe_data[k]

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(json_safe_data, f, indent=2)
        
    print(f"\n--- ANALYSIS COMPLETE ---")
    print(f"Output File  : {output_filename}")
    print(f"Total States : {results['reachable_count_str']}")
    print(f"BFS Depth    : {results['bfs_depth']}")
    print(f"Compute Time : {results['bdd_time_s']:.6f}s")

def execute_bdd_analysis(file_path_str, limit=10000):
    """
    
    """
    fpath = Path(file_path_str)
    if not fpath.exists():
        print(f"Error: File not found {fpath}")
        return None, None

    # Use parser from common
    model_data = parse_pnml(str(fpath))
    if model_data is None: return None, None

    try:
    
        res = compute_reachable_states_bdd(model_data, limit)
    except Exception as e:
        print(f"BDD Error: {e}")
        return None, None

    res['symbolic_time_s'] = res['bdd_time_s']
    json_path = fpath.with_suffix('.reach_bdd.json').name
    
    # JSON Cleanup
    json_data = res.copy()
    for k in ['bdd_manager', 'reachable_bdd', 'variables']:
        if k in json_data: del json_data[k]

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
        
    return res, json_path

if __name__ == '__main__':
    main_execution()