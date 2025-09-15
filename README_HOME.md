# 🎭 SadTalker - Trang Home Sinh Động

## 📋 Mô tả

Đây là phiên bản cải tiến của SadTalker với trang home sinh động và giao diện hiện đại. Trang web bao gồm:

- **🏠 Trang Home**: Giao diện chào mừng với thiết kế gradient động và hiệu ứng đẹp mắt
- **🎬 Trang Sinh Video**: Giao diện chính để tạo video nói chuyện từ ảnh và âm thanh

## ✨ Tính năng mới

### 🎨 Thiết kế sinh động
- Gradient background với animation liên tục
- Hiệu ứng floating cho các phần tử
- Button "Sinh Video" với hiệu ứng glow
- Cards trong suốt với backdrop blur
- Responsive design cho mobile

### 🚀 Giao diện cải tiến
- Tab navigation để chuyển đổi giữa Home và Sinh Video
- Typography gradient cho tiêu đề
- Hover effects cho tất cả interactive elements
- Loading animations

## 🎯 Cách sử dụng

### 1. Chạy ứng dụng
```bash
python app_with_home.py
```

### 2. Truy cập trang web
- Mở trình duyệt và truy cập: `http://127.0.0.1:7860`
- Trang Home sẽ hiển thị đầu tiên với giao diện sinh động

### 3. Sử dụng tính năng
- **Tab Home**: Xem thông tin và hướng dẫn
- **Tab Sinh Video**: Tạo video nói chuyện từ ảnh và âm thanh

## 🎨 Các file đã tạo

1. **`app_with_home.py`** - File chính với giao diện hoàn chỉnh
2. **`home_page.py`** - Phiên bản home page phức tạp (tham khảo)
3. **`home_page_simple.py`** - Phiên bản home page đơn giản (tham khảo)

## 🎭 Tính năng SadTalker

### 📸 Upload ảnh
- Tải lên ảnh khuôn mặt
- Hỗ trợ nhiều định dạng: JPG, PNG, etc.

### 🎵 Âm thanh
- Upload file âm thanh
- Chuyển văn bản thành âm thanh (TTS)
- Hỗ trợ nhiều ngôn ngữ

### ⚙️ Cài đặt
- Pose style (0-46)
- Face model resolution (256/512)
- Preprocess options
- Still mode
- Batch size
- Face enhancer

## 🎨 CSS Features

### Gradient Animation
```css
@keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
```

### Floating Effect
```css
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}
```

### Glow Button
```css
@keyframes glow {
    0% { box-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #e60073; }
    50% { box-shadow: 0 0 10px #fff, 0 0 20px #ff4da6, 0 0 30px #ff4da6; }
    100% { box-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #e60073; }
}
```

## 📱 Responsive Design

Giao diện được tối ưu cho:
- Desktop (1920x1080+)
- Tablet (768px+)
- Mobile (320px+)

## 🎯 Hướng dẫn phát triển

### Thêm tab mới
```python
with gr.TabItem("Tab Name", id=2):
    # Tab content here
```

### Thay đổi màu sắc
Chỉnh sửa biến CSS trong `custom_css`:
```css
.gradient-bg {
    background: linear-gradient(-45deg, #your-color1, #your-color2, #your-color3, #your-color4);
}
```

### Thêm animation mới
```css
@keyframes your-animation {
    0% { /* start state */ }
    100% { /* end state */ }
}

.your-class {
    animation: your-animation 2s ease infinite;
}
```

## 🚀 Deployment

### Local Development
```bash
python app_with_home.py
```

### Production
```bash
python app_with_home.py --server-name 0.0.0.0 --server-port 7860
```

## 📝 Lưu ý

- Đảm bảo đã cài đặt tất cả dependencies
- Checkpoints và models phải được download đầy đủ
- GPU được khuyến nghị để tăng tốc độ xử lý

## 🎨 Customization

Bạn có thể tùy chỉnh:
- Màu sắc gradient
- Animation speed
- Font sizes
- Button styles
- Card layouts

Chỉ cần chỉnh sửa CSS variables trong `custom_css` string.

---

**Made with ❤️ for creative content creators** 