## 1. Giới thiệu
Module `pnml_parser.py` dùng để đọc file PNML và chuyển thành dữ liệu mạng Petri (Places, Transitions, Marking, Incidence Matrix).
Các Task sau chỉ cần gọi chung hàm `get_petri_net_data()` để lấy dữ liệu đã parse.
## 2. Các lỗi đã xử lý
### Lỗi nghiêm trọng (Dừng chương trình)

* **Trùng Place ID**
* **Trùng Transition ID**
* **Một ID là cả Place lẫn Transition**
* **Arc trỏ tới node không tồn tại**
* **Arc sai cấu trúc:** Place → Place hoặc Transition → Transition

### Cảnh báo (Không dừng)
* **Node bị cô lập:** không có bất kỳ arc nào nối tới/ra

## 3. Cách lấy dữ liệu trong các Task
Các file Task không cần tự đọc PNML; chỉ cần dùng đoạn code sau:

```python
from common_loader import get_petri_net_data

data = get_petri_net_data()
```
## Quy tắc chọn file input:  
* python your_task.py your_file.pnml

## 4. Dữ liệu trả về
Dữ liệu trả về là một dictionary có cấu trúc như sau:

```python
{
    "places": [
        {"id": "p1", "index": 0},
        {"id": "p2", "index": 1}
    ],

    "transitions": [
        {"id": "t1", "pre": [0], "post": [1]},
        {"id": "t2", "pre": [1], "post": [0]}
    ],

    "initial_marking": [1, 0, 2],

    "incidence_matrix": [
        [-1, 1],
        [1, -1],
        [0, 0]
    ]
}
```
# Ý nghĩa Output

* places: danh sách Place theo thứ tự cố định → dùng làm index cho các thành phần khác.
* transitions: chứa luật bắn, trong đó pre (preset) và post (postset) đã được chuyển thành số index.
* initial_marking: Vector marking ban đầu theo đúng thứ tự của places.
* incidence_matrix: Ma trận liên thuộc (Place × Transition) với giá trị -1 (Input), 0 (Không liên quan), +1 (Output).