# bdd_utils.py
from dd import autoref as _bdd

def varname(i):
    return f'x_{i}'

def varname_prime(i):
    return f'y_{i}'

def build_transition_relation(bdd, num_places, t):
    """Xây dựng quan hệ chuyển tiếp cho 1 transition cụ thể"""
    pre_indexes = set(t['pre'])
    post_indexes = set(t['post'])
    
    # 1. Pre-condition
    pre_cond = [varname(i) for i in pre_indexes]
    
    # 2. Change Logic
    change_parts = []
    for i in range(num_places):
        if i in pre_indexes and i not in post_indexes:
            change_parts.append(f'!{varname_prime(i)}') 
        elif i in post_indexes:
            change_parts.append(varname_prime(i))
        else:
            # Frame axiom: Giữ nguyên
            change_parts.append(f'({varname(i)} <-> {varname_prime(i)})')
            
    pre_expr = ' & '.join(pre_cond) if pre_cond else 'TRUE'
    change_expr = ' & '.join(change_parts)
    
    full_expr = f'({pre_expr}) & ({change_expr})'
    return bdd.add_expr(full_expr)

def marking_to_bdd(bdd, old_vars, marking_tuple):
    """Chuyển đổi một marking (list/tuple) thành BDD"""
    expr_parts = []
    for i, val in enumerate(marking_tuple):
        v = varname(i)
        # 1-safe: val > 0 -> True
        expr_parts.append(v if val > 0 else f'!{v}')
    return bdd.add_expr(' & '.join(expr_parts))

def enumerate_markings_from_bdd(bdd, bdd_node, old_vars, limit=1000):
    """Liệt kê các trạng thái cụ thể từ BDD"""
    results = []
    # pick_iter trả về generator các dict {var: value}
    count = 0
    for assignment in bdd.pick_iter(bdd_node, care_vars=old_vars):
        if limit and count >= limit:
            break
        
        # Chuyển assignment {x_0: True, x_1: False...} thành list [1, 0...]
        # Cần sắp xếp theo index của biến
        marking_list = [0] * len(old_vars)
        for var, val in assignment.items():
            # Tách lấy index từ tên biến "x_5" -> 5
            idx = int(var.split('_')[1])
            if val:
                marking_list[idx] = 1
        
        results.append(marking_list)
        count += 1
    return results