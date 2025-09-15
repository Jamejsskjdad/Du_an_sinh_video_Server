# Giải thích: Tại sao tạo ra 2 phiên bản video khi chọn preprocess='full'

## 🚨 **Vấn đề bạn gặp:**
- Chọn `preprocess='full'` 
- Nhưng vẫn tạo ra 2 file MP4:
  - File 1: `image##xin_chao_cac_ban_minh_la_tien_...mp4` (989 KB) - **Chỉ có mặt**
  - File 2: `image##xin_chao_cac_ban_minh_la_tien_..._full.mp4` (2,371 KB) - **Full ảnh**

## 🔍 **Nguyên nhân:**

### **Logic trong `src/facerender/animate.py` (dòng 210-220):**

```python
# LUÔN tạo video chỉ có mặt trước
video_name = x['video_name'] + '.mp4'
path = os.path.join(video_save_dir, 'temp_'+video_name)
imageio.mimsave(path, result, fps=float(25))

av_path = os.path.join(video_save_dir, video_name)
save_video_with_watermark(path, new_audio_path, av_path, watermark=False)
print(f'The generated video is named {video_save_dir}/{video_name}') 

# NẾU preprocess='full' thì tạo thêm video full
if 'full' in preprocess.lower():
    video_name_full = x['video_name'] + '_full.mp4'
    full_video_path = os.path.join(video_save_dir, video_name_full)
    return_path = full_video_path
    paste_pic(path, pic_path, crop_info, new_audio_path, full_video_path, extended_crop=True if 'ext' in preprocess.lower() else False)
    print(f'The generated video is named {video_save_dir}/{video_name_full}') 
```

## 📋 **Quy trình tạo video:**

### **Bước 1: Tạo video chỉ có mặt (LUÔN xảy ra)**
```python
# Tạo video 256x256 chỉ có mặt
video_name = x['video_name'] + '.mp4'  # image##xin_chao_cac_ban_minh_la_tien_...mp4
save_video_with_watermark(path, new_audio_path, av_path, watermark=False)
```

### **Bước 2: Tạo video full (CHỈ khi preprocess='full')**
```python
if 'full' in preprocess.lower():
    # Tạo video full bằng cách paste mặt vào ảnh gốc
    video_name_full = x['video_name'] + '_full.mp4'  # image##xin_chao_cac_ban_minh_la_tien_..._full.mp4
    paste_pic(path, pic_path, crop_info, new_audio_path, full_video_path, extended_crop=False)
```

## 🎯 **Tại sao thiết kế như vậy:**

### **1. Video chỉ có mặt (989 KB):**
- **Mục đích**: Kiểm tra chất lượng animation mặt
- **Kích thước**: 256x256 hoặc 512x512
- **Nội dung**: Chỉ có khuôn mặt được animate
- **Dùng để**: Debug, kiểm tra chất lượng

### **2. Video full (2,371 KB):**
- **Mục đích**: Kết quả cuối cùng cho người dùng
- **Kích thước**: Giữ nguyên kích thước ảnh gốc
- **Nội dung**: Mặt được paste vào ảnh gốc
- **Dùng để**: Kết quả cuối cùng

## 🔧 **Cách hoạt động của `paste_pic()`:**

```python
def paste_pic(video_path, pic_path, crop_info, audio_path, out_path, extended_crop=False):
    # 1. Đọc video chỉ có mặt
    # 2. Đọc ảnh gốc
    # 3. Paste mặt đã animate vào vị trí đúng trong ảnh gốc
    # 4. Thêm audio
    # 5. Lưu thành video full
```

## 📊 **So sánh 2 phiên bản:**

| Thuộc tính | Video chỉ mặt | Video full |
|------------|---------------|------------|
| **Kích thước** | 256x256 | Giữ nguyên ảnh gốc |
| **Nội dung** | Chỉ khuôn mặt | Mặt + background |
| **File size** | 989 KB | 2,371 KB |
| **Mục đích** | Debug/Test | Kết quả cuối |
| **Tên file** | `name.mp4` | `name_full.mp4` |

## ✅ **Hành vi sau khi sửa:**

### **Khi chọn `preprocess='crop'` hoặc `'resize'`:**
- Chỉ tạo 1 file: `name.mp4` (video chỉ có mặt)

### **Khi chọn `preprocess='full'` hoặc `'extfull'`:**
- **Chỉ tạo 1 file**: `name.mp4` (video full - kết quả cuối)
- **Đã loại bỏ**: File debug chỉ có mặt

## 🎯 **Kết quả sau khi sửa:**

**Tất cả preprocess types đều chỉ tạo 1 file duy nhất:**

| Preprocess | File tạo ra | Nội dung |
|------------|-------------|----------|
| `crop` | `name.mp4` | Video chỉ có mặt |
| `resize` | `name.mp4` | Video chỉ có mặt |
| `full` | `name.mp4` | **Video full (mặt + background)** |
| `extcrop` | `name.mp4` | Video chỉ có mặt |
| `extfull` | `name.mp4` | **Video full (mặt + background)** |

**Không còn file debug nào được tạo ra!** 🎉

## 💡 **Lời khuyên sau khi sửa:**

1. **Tất cả preprocess types đều chỉ tạo 1 file duy nhất**
2. **Không còn file debug nào được tạo ra**
3. **Khi chọn `preprocess='full'` hoặc `'extfull'`**: Kết quả là video full (mặt + background)
4. **Khi chọn `preprocess='crop'`, `'resize'`, `'extcrop'`**: Kết quả là video chỉ có mặt

## 🔧 **Thay đổi đã thực hiện:**

### **Trong `src/facerender/animate.py`:**
```python
if 'full' in preprocess.lower():
    # Chỉ tạo file full, không tạo file chỉ có mặt
    video_name_full = x['video_name'] + '.mp4'  # Đổi tên thành .mp4 thay vì _full.mp4
    full_video_path = os.path.join(video_save_dir, video_name_full)
    return_path = full_video_path
    paste_pic(path, pic_path, crop_info, new_audio_path, full_video_path, extended_crop=True if 'ext' in preprocess.lower() else False)
    print(f'The generated video is named {video_save_dir}/{video_name_full}') 
else:
    # Cho các preprocess khác, tạo file chỉ có mặt như bình thường
    av_path = os.path.join(video_save_dir, video_name)
    return_path = av_path
    save_video_with_watermark(path, new_audio_path, av_path, watermark=False)
    print(f'The generated video is named {video_save_dir}/{video_name}') 
    full_video_path = av_path
```

**Kết luận: Đã sửa thành công! Bây giờ tất cả preprocess types đều chỉ tạo 1 file duy nhất!** 🎉 