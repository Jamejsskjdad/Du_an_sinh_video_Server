# MathFormulaProcessor - Xử lý Công thức Toán học từ PowerPoint

## 📖 Tổng quan

`MathFormulaProcessor` là một module Python được thiết kế để giải quyết vấn đề **không đọc được các công thức toán học, vật lý, hóa học** từ PowerPoint khi sử dụng thư viện `python-pptx`.

## 🎯 Vấn đề được giải quyết

- **Office Math objects**: Thư viện `python-pptx` bỏ qua hoàn toàn các đối tượng "Office Math"
- **Ký tự đặc biệt**: Các ký tự như số mũ (², ³), chỉ số dưới (₁, ₂), chữ Hy Lạp (α, β, π) không được xử lý
- **Công thức phức tạp**: Các công thức toán học, vật lý, hóa học bị mất hoặc hiển thị sai

## 🚀 Tính năng chính

### 1. Xử lý Ký tự Đặc biệt
- **Số mũ**: ² → "mũ hai", ³ → "mũ ba"
- **Chỉ số dưới**: ₁ → "chỉ số một", ₂ → "chỉ số hai"
- **Chữ Hy Lạp**: α → "alpha", β → "beta", π → "pi"
- **Ký tự toán học**: √ → "căn bậc hai", ∫ → "tích phân", ∑ → "tổng"

### 2. Nhận diện Mẫu Toán học
- **Phân số**: a/b → "a chia b"
- **Căn bậc hai**: √x → "căn bậc hai của x"
- **Lũy thừa**: x^n → "x mũ n"
- **Tích phân**: ∫f(x)dx → "tích phân của f(x) theo x"

### 3. Xử lý Unicode
- Tự động nhận diện và xử lý các ký tự Unicode
- Hỗ trợ các ký tự toán học từ các ngôn ngữ khác nhau

## 📁 Cấu trúc File

```
src/utils/
└── math_formula_processor.py    # Module chính
test_math_processor.py           # File test
demo_math_processor.py           # File demo
MATH_FORMULA_PROCESSOR_README.md # Hướng dẫn này
```

## 🔧 Cài đặt và Sử dụng

### 1. Import Module

```python
from src.utils.math_formula_processor import MathFormulaProcessor, process_math_text
```

### 2. Sử dụng Cơ bản

```python
# Tạo instance
processor = MathFormulaProcessor()

# Xử lý văn bản
text = "E = mc² + α × β"
result = processor.process_special_characters(text)
# Kết quả: "E = mc mũ hai +  alpha ×  beta"
```

### 3. Sử dụng Hàm Tiện ích

```python
# Xử lý nhanh với hàm tiện ích
result = process_math_text("x² + y³ = z")
# Kết quả: "x mũ hai + y mũ ba = z"
```

### 4. Xử lý Toàn bộ PowerPoint

```python
# Xử lý file PowerPoint hoàn chỉnh
result = processor.process_powerpoint_text("presentation.pptx")
print(f"Tổng số slides: {result['total_slides']}")
print(f"Slides có công thức: {result['slides_with_math']}")

for slide in result['slides']:
    print(f"Slide {slide['slide_number']}: {slide['processed_text']}")
```

## 📊 Ví dụ Xử lý

### Toán học
| Input | Output |
|-------|--------|
| `x² + y³ = z` | `x mũ hai + y mũ ba = z` |
| `√(a² + b²)` | `căn bậc hai của (a mũ hai + b mũ hai)` |
| `∫f(x)dx` | `tích phân của f(x) theo x` |
| `∑(i=1 to n) x_i` | `tổng của (i=1 to n) = x_i` |

### Hóa học
| Input | Output |
|-------|--------|
| `H₂O` | `H chỉ số hai O` |
| `C₆H₁₂O₆` | `C chỉ số sáu H chỉ số một chỉ số hai O chỉ số sáu` |
| `H₂SO₄` | `H chỉ số hai S O chỉ số bốn` |

### Vật lý
| Input | Output |
|-------|--------|
| `F = ma` | `F = ma` |
| `E = ½mv²` | `E = ½mv mũ hai` |
| `θ = 45°` | `theta = 45 độ` |

## 🔄 Tích hợp với SadTalker

### 1. Sửa đổi `lecture_input.py`

```python
from src.utils.math_formula_processor import MathFormulaProcessor, process_math_text

def extract_slides_from_pptx(pptx_file):
    # Sử dụng MathFormulaProcessor
    math_processor = MathFormulaProcessor()
    processed_result = math_processor.process_powerpoint_text(pptx_file.name)
    
    # Xử lý kết quả...
```

### 2. Xử lý Tự động

Module sẽ tự động:
- Phát hiện các đối tượng toán học trong PowerPoint
- Chuyển đổi ký tự đặc biệt thành văn bản tiếng Việt
- Tích hợp với hệ thống TTS hiện tại

## 🧪 Testing

### Chạy Test

```bash
python test_math_processor.py
```

### Chạy Demo

```bash
python demo_math_processor.py
```

## 📝 Cấu hình

### Thêm Ký tự Mới

```python
# Trong MathFormulaProcessor.__init__()
self.special_char_map['new_symbol'] = 'mô tả tiếng Việt'
```

### Thêm Mẫu Regex

```python
# Trong MathFormulaProcessor.__init__()
self.math_patterns.append((r'pattern', r'replacement'))
```

## ⚠️ Lưu ý

1. **Fallback**: Nếu có lỗi xử lý công thức toán học, hệ thống sẽ tự động fallback về phương pháp cũ
2. **Performance**: Xử lý Unicode có thể chậm hơn với văn bản dài
3. **Dependencies**: Cần cài đặt `python-pptx` để xử lý PowerPoint

## 🚀 Cải tiến Tương lai

- [ ] Hỗ trợ LaTeX input/output
- [ ] Tích hợp với MathJax Speech Rule Engine
- [ ] Hỗ trợ OCR cho công thức dạng ảnh
- [ ] Tối ưu hóa performance cho file lớn
- [ ] Hỗ trợ đa ngôn ngữ

## 📞 Hỗ trợ

Nếu gặp vấn đề hoặc có đề xuất cải tiến, vui lòng:

1. Kiểm tra log để xem lỗi chi tiết
2. Chạy test để xác định vấn đề
3. Tạo issue với thông tin chi tiết

## 📄 License

Module này được phát triển như một phần của dự án SadTalker và tuân theo cùng license.


