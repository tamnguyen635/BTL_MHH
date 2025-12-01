import xml.etree.ElementTree as ET
import sys
import pprint

class PetriNet:
    def __init__(self):
        # Dữ liệu dạng Dictionary để truy cập nhanh theo ID
        self.places = {}      # { 'p1': { 'id': 'p1', 'token': 1 }, ... }
        self.transitions = {} # { 't1': { 'id': 't1', 'preset': [], 'postset': [] }, ... }
        self.arcs = []        # [ { 'source': 'p1', 'target': 't1' }, ... ]
        
        # Dữ liệu dạng List đã sắp xếp (quan trọng cho Ma trận và BDD)
        self.place_ids = []       # ['p1', 'p2', 'p3'...]
        self.transition_ids = []  # ['t1', 't2', 't3'...]
        
        # Ma trận liên thuộc (Incidence Matrix)
        self.incidence_matrix = [] 

    def load_from_pnml(self, file_path):
        """Đọc file PNML và xây dựng cấu trúc mạng"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception as e:
            print(f"[LỖI] Không thể đọc file {file_path}: {e}")
            return False

        # 1. Xử lý Namespace
        ns = {}
        if '}' in root.tag:
            ns_url = root.tag.split('}')[0].strip('{')
            ns = {'pnml': ns_url}

        def find_all(node, tag_name):
            if ns: return node.findall(f'.//pnml:{tag_name}', ns)
            return node.findall(f'.//{tag_name}')

        # 2. Parse Places (CÓ KIỂM TRA TRÙNG LẶP)
        for place in find_all(root, 'place'):
            p_id = place.get('id')
            if not p_id: continue

            # [MỚI] lỗi trùng lặp
            if p_id in self.places:
                print(f"[LỖI INPUT] Place ID '{p_id}' bị khai báo trùng lặp!")
                return False

            initial_marking = 0
            marking_tag = place.find('pnml:initialMarking', ns) if ns else place.find('initialMarking')
            if marking_tag is not None:
                text_tag = marking_tag.find('pnml:text', ns) if ns else marking_tag.find('text')
                if text_tag is not None and text_tag.text:
                    try: initial_marking = int(text_tag.text)
                    except: pass
            
            self.places[p_id] = {'id': p_id, 'token': initial_marking}

        # 3. Parse Transitions (CÓ KIỂM TRA TRÙNG LẶP)
        for trans in find_all(root, 'transition'):
            t_id = trans.get('id')
            if not t_id: continue
            
            # [MỚI] lỗi trùng lặp
            if t_id in self.transitions:
                print(f"[LỖI INPUT] Transition ID '{t_id}' bị khai báo trùng lặp!")
                return False
            # [MỚI] lỗi ID vừa là Place vừa là Transition
            if t_id in self.places:
                print(f"[LỖI INPUT] ID '{t_id}' bị trùng (vừa là Place vừa là Transition)!")
                return False

            self.transitions[t_id] = {'id': t_id, 'preset': [], 'postset': []}

        # 4. Parse Arcs
        for arc in find_all(root, 'arc'):
            self.arcs.append({
                'id': arc.get('id', 'unknown'), 
                'source': arc.get('source'), 
                'target': arc.get('target')
            })

        # 5. Xây dựng quan hệ
        self._build_relationships()
        return True

    def _build_relationships(self):
        self.place_ids = sorted(self.places.keys())
        self.transition_ids = sorted(self.transitions.keys())

        # Reset preset/postset
        for t in self.transitions.values():
            t['preset'] = []
            t['postset'] = []

        # Điền preset/postset 
        for arc in self.arcs:
            src, tgt = arc['source'], arc['target']
            if src in self.places and tgt in self.transitions:
                self.transitions[tgt]['preset'].append(src)
            elif src in self.transitions and tgt in self.places:
                self.transitions[src]['postset'].append(tgt)
                
        self._generate_incidence_matrix()

    def _generate_incidence_matrix(self):
        n_p = len(self.place_ids)
        n_t = len(self.transition_ids)
        matrix = [[0] * n_t for _ in range(n_p)]

        for t_idx, t_id in enumerate(self.transition_ids):
            trans_data = self.transitions[t_id]
            for p_id in trans_data['preset']:
                if p_id in self.place_ids:
                    matrix[self.place_ids.index(p_id)][t_idx] -= 1
            for p_id in trans_data['postset']:
                if p_id in self.place_ids:
                    matrix[self.place_ids.index(p_id)][t_idx] += 1
        self.incidence_matrix = matrix

    def check_consistency(self):
        """Task 1.2: Kiểm tra tính nhất quán (NÂNG CẤP)"""
        print("\n--- [CHECK] Kiểm tra lỗi mạng Petri ---")
        errors = []
        warnings = [] # Cảnh báo 
        
        if not self.places and not self.transitions:
            errors.append("Mạng rỗng: Không có Place hoặc Transition nào.")

        all_places = set(self.places.keys())
        all_transitions = set(self.transitions.keys())
        all_nodes = all_places | all_transitions
        connected_nodes = set() # Theo dõi những node có dây nối

        for arc in self.arcs:
            aid = arc['id']
            src = arc['source']
            tgt = arc['target']

            # [LỖI 1] Node không tồn tại (Missing Node) - Ví dụ: p1 -> p3 (p3 ko có)
            src_exists = src in all_nodes
            tgt_exists = tgt in all_nodes

            if not src_exists:
                errors.append(f"Arc '{aid}': Nguồn '{src}' không tồn tại.")
            if not tgt_exists:
                errors.append(f"Arc '{aid}': Đích '{tgt}' không tồn tại.")

            if src_exists and tgt_exists:
                connected_nodes.add(src)
                connected_nodes.add(tgt)
                
                # [LỖI 2] Sai cấu trúc (Place -> Place hoặc Trans -> Trans)
                if src in all_places and tgt in all_places:
                    errors.append(f"Arc '{aid}': Lỗi cấu trúc (Place '{src}' nối thẳng sang Place '{tgt}').")
                if src in all_transitions and tgt in all_transitions:
                    errors.append(f"Arc '{aid}': Lỗi cấu trúc (Trans '{src}' nối thẳng sang Trans '{tgt}').")

        # [LỖI 3] Node bị cô lập (Isolated Nodes)
        isolated_nodes = all_nodes - connected_nodes
        if isolated_nodes:
            warnings.append(f"Cảnh báo: Có {len(isolated_nodes)} node bị cô lập (không nối đi đâu): {isolated_nodes}")

        # In ra kết quả
        if warnings:
            print(">> WARNINGS:")
            for w in warnings: print(f"   [!] {w}")
            
        if errors:
            print(f">> FAILED: Phát hiện {len(errors)} lỗi nghiêm trọng:")
            for e in errors: print(f"   [x] {e}")
            return False
        
        print(">> PASSED: Mạng hợp lệ.")
        return True

    def export_to_dict(self):
        """Xuất dữ liệu kèm Ma trận"""
        places_list = [{'id': pid, 'index': i} for i, pid in enumerate(self.place_ids)]
        
        transitions_list = []
        for t_id in self.transition_ids:
            t = self.transitions[t_id]
            # Chỉ export các node hợp lệ
            pre = [self.place_ids.index(p) for p in t['preset'] if p in self.place_ids]
            post = [self.place_ids.index(p) for p in t['postset'] if p in self.place_ids]
            
            transitions_list.append({'id': t_id, 'pre': pre, 'post': post})

        return {
            'places': places_list,
            'transitions': transitions_list,
            'initial_marking': [self.places[p]['token'] for p in self.place_ids],
            'incidence_matrix': self.incidence_matrix # Thêm ma trận cho Task 4
        }

# ==========================================
# GIAO TIẾP VỚI BÊN NGOÀI
# ==========================================
def parse_pnml(file_path):
    net = PetriNet()
    
    # 1. Đọc file (Nếu lỗi trùng ID sẽ dừng ngay)
    if not net.load_from_pnml(file_path):
        return None
        
    # 2. Kiểm tra logic (Nếu lỗi cấu trúc/thiếu node sẽ dừng ngay)
    if not net.check_consistency():
        print(">> DỪNG CHƯƠNG TRÌNH DO INPUT LỖI.")
        return None
        
    # 3. Xuất kết quả
    return net.export_to_dict()

# ==========================================
# CHẠY THỬ
# ==========================================
if __name__ == "__main__":
    pnml_file = "test_task4.pnml"
    
    data = parse_pnml(pnml_file)
    
    if data:
        print("\n--- KẾT QUẢ ---")
        pprint.pprint(data, sort_dicts=False)