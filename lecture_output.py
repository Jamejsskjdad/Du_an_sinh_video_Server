import os
import json
import gradio as gr
import tempfile
import time
import shutil
import gc
import re
import torch
from datetime import datetime
# MoviePy còn dùng cho fallback concat; không dùng cho overlay nữa
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
from lecture_input import extract_slides_from_pptx
from index import convert_text_to_audio  
from src.utils.xtts_clone import XTTSInference

# ffmpeg
import subprocess
import shutil as _shutil


def merge_user_text_with_ppt_images(user_slides, ppt_slides):
    """
    Gộp text do người dùng sửa (user_slides) với ảnh gốc từ PPT (ppt_slides).
    - Ưu tiên ghép theo slide_number nếu có.
    - Nếu không khớp số, ghép theo thứ tự (index).
    - Mặc định chỉ xử lý số lượng = len(user_slides) để không đọc phần dư.
    """
    if not user_slides:
        return ppt_slides or []

    if not ppt_slides:
        # không có PPT -> đành dùng ảnh tạo từ text
        return user_slides

    # map ảnh theo số slide
    by_num = {s.get('slide_number'): s for s in ppt_slides if s.get('slide_number') is not None}

    result = []
    for idx, us in enumerate(user_slides):
        # 1) thử theo số slide
        img_path = None
        if us.get('slide_number') in by_num:
            img_path = by_num[us['slide_number']].get('image_path')

        # 2) fallback theo thứ tự
        if img_path is None and idx < len(ppt_slides):
            img_path = ppt_slides[idx].get('image_path')

        result.append({
            'slide_number': us.get('slide_number', idx + 1),
            'text': us.get('text', ''),
            'image_path': img_path,               # <-- luôn lấy ảnh từ PPT nếu có
            'has_math_objects': False
        })
    return result

def parse_user_slides_text(user_text: str):
    """
    Parse văn bản do người dùng chỉnh sửa thành list slides:
    Hỗ trợ tiêu đề dạng:
      ## Slide 1
      Slide 1:
    Nếu không tìm thấy tiêu đề, coi toàn bộ là 1 slide.
    """
    slides = []
    if not user_text or not user_text.strip():
        return slides

    txt = user_text.replace("\r\n", "\n")
    # tìm các heading Slide N
    pattern = re.compile(r'(?im)^\s*(?:#+\s*)?slide\s+(\d+)\s*:?\s*$', re.MULTILINE)
    matches = list(pattern.finditer(txt))

    if not matches:
        slides.append({'slide_number': 1, 'text': txt.strip(), 'image_path': None, 'has_math_objects': False})
        return slides

    for idx, m in enumerate(matches):
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(txt)
        num = int(m.group(1))
        body = txt[start:end].strip()
        slides.append({'slide_number': num, 'text': body, 'image_path': None, 'has_math_objects': False})

    # sắp xếp theo số slide tăng dần
    slides.sort(key=lambda s: s['slide_number'])
    return slides

def cleanup_cuda_memory():
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        print("🧹 CUDA memory cleaned up")
    except Exception as e:
        print(f"⚠️ CUDA cleanup warning: {str(e)}")

def check_system_memory():
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        print(f"💾 Available RAM: {available_gb:.1f}GB")
        return available_gb
    except ImportError:
        print("⚠️ psutil not available, cannot check memory")
        return 8.0

def get_audio_duration(audio_path):
    try:
        if audio_path and os.path.exists(audio_path):
            clip = AudioFileClip(audio_path)
            d = clip.duration
            clip.close()
            return d
        return 0
    except Exception as e:
        print(f"Error getting audio duration: {str(e)}")
        return 0

def create_slide_image_with_text(text, output_path, width=1280, height=720):
    try:
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        try:
            # nên thay bằng path tới font Unicode đã cài (DejaVuSans.ttf/NotoSans.ttf/Asap.ttf…)
            font = ImageFont.truetype("DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()

        text_lines = (text or "").split('\n')
        y_position = height // 2 - (len(text_lines) * 50) // 2

        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x_position = (width - text_width) // 2
            draw.text((x_position, y_position), line, fill='black', font=font)
            y_position += text_height + 20

        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating slide image: {str(e)}")
        return None

def _find_reference_wav_by_display_name(display_name: str, voices_root: str = './cloned_voices'):
    try:
        if not os.path.isdir(voices_root):
            return None
        for voice_id in os.listdir(voices_root):
            vdir = os.path.join(voices_root, voice_id)
            cfg_path = os.path.join(vdir, 'config.json')
            if not os.path.isfile(cfg_path):
                continue
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            if cfg.get('display_name') == display_name:
                wav_name = cfg.get('reference_wav')
                if wav_name:
                    wav_path = os.path.join(vdir, wav_name)
                    return wav_path if os.path.isfile(wav_path) else None
    except Exception:
        return None
    return None

def _ensure_even_image(path):
    from PIL import Image
    im = Image.open(path)
    w, h = im.size
    new_w = w + (w & 1)   # +1 nếu lẻ
    new_h = h + (h & 1)
    if new_w != w or new_h != h:
        bg = Image.new(im.mode, (new_w, new_h), (255, 255, 255))
        bg.paste(im, (0, 0))
        bg.save(path)

# ===== NEW: overlay bằng ffmpeg (nhanh) =====
def pip_composite_ffmpeg(slide_png, teacher_mp4, out_mp4,
                         pip_ratio=0.10, margin=50, prefer_nvenc=True,
                         fps=25):
    import shutil as _shutil
    from PIL import Image

    if not _shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg không có trong PATH")

    # Ép ảnh slide về kích thước chẵn ngay từ gốc
    _ensure_even_image(slide_png)

    # Đọc kích thước slide để tính tỷ lệ PIP
    with Image.open(slide_png) as im:
        slide_w, slide_h = im.size
    teacher_target_w = max(1, int(slide_w * pip_ratio))

    vcodec = "h264_nvenc" if prefer_nvenc else "libx264"
    preset = "p5" if vcodec == "h264_nvenc" else "ultrafast"

    # Pad slide -> kích thước chẵn; scale teacher; overlay; ép về yuv420p; đặt nhãn [vout]
    filter_complex = (
        "[0:v]pad=ceil(iw/2)*2:ceil(ih/2)*2[bg];"
        f"[1:v]scale={teacher_target_w}:-2:flags=lanczos[face];"
        "[bg][face]overlay=W-w-{m}:{m},format=yuv420p[vout]"
    ).format(m=margin)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", slide_png,     # 0:v = ảnh (loop)
        "-i", teacher_mp4,                  # 1:v = video giáo viên
        "-filter_complex", filter_complex,
        "-map", "[vout]",                   # video đã overlay
        "-map", "1:a?",                     # audio từ teacher nếu có
        "-c:v", vcodec,
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-shortest",
        "-c:a", "copy",                     # nếu đôi khi lỗi, đổi thành: "aac"
        out_mp4
    ]

    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            if vcodec == "h264_nvenc":
                # fallback libx264
                return pip_composite_ffmpeg(slide_png, teacher_mp4, out_mp4,
                                            pip_ratio, margin, prefer_nvenc=False, fps=fps)
            else:
                err = p.stderr.decode("utf-8", errors="ignore")
                raise RuntimeError(f"ffmpeg overlay failed: {err}")
    except subprocess.CalledProcessError as e:
        if vcodec == "h264_nvenc":
            return pip_composite_ffmpeg(slide_png, teacher_mp4, out_mp4,
                                        pip_ratio, margin, prefer_nvenc=False, fps=fps)
        raise


def generate_video_for_text(
    sad_talker, source_image, text, language, voice_mode, cloned_voice_name, cloned_lang,
    preprocess_type, is_still_mode, enhancer, batch_size, size_of_image, pose_style,
    gender=None, builtin_voice=None,
    pre_synth_audio_path: str = None,  # NEW
    speech_rate: float = 1.0          # NEW
):
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            cleanup_cuda_memory()
            if not source_image or not os.path.exists(source_image):
                print(f"Source image not found: {source_image}")
                return None

            # === TTS (hoặc dùng audio có sẵn) ===
            audio_path = pre_synth_audio_path
            if not audio_path:
                if voice_mode == 'Giọng nhân bản' and cloned_voice_name:
                    ref_wav = _find_reference_wav_by_display_name(cloned_voice_name)
                    if ref_wav:
                        try:
                            xtts = XTTSInference()
                            lang_code = cloned_lang if cloned_lang else language
                            audio_path = xtts.synthesize(text, lang_code, ref_wav)
                        except Exception as e:
                            print(f"XTTS synthesis failed, fallback to gTTS: {e}")
                    if audio_path is None:
                        audio_path = convert_text_to_audio(text, language)
                else:
                    audio_path = convert_text_to_audio(
                        text=text,
                        language=language,
                        gender=gender,
                        preferred_voice=builtin_voice or None
                    )
            if not audio_path:
                print("Failed to convert text to audio")
                return None

            # === Áp dụng tốc độ đọc ===
            audio_path = adjust_audio_speed(audio_path, speech_rate)

            print(f"Generating video with image: {source_image}")
            print(f"Audio path: {audio_path}")
            print(f"Batch size: {batch_size} (attempt {retry_count + 1}/{max_retries})")

            # SadTalker
            video_path = sad_talker.test(
                source_image, audio_path, preprocess_type, is_still_mode,
                enhancer, batch_size, size_of_image, pose_style
            )

            # Xoá audio tạm (nếu audio được synth trong hàm này)
            if not pre_synth_audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

            if video_path and os.path.exists(video_path):
                print(f"✅ Video generated successfully: {video_path}")
                cleanup_cuda_memory()
                return video_path
            else:
                print(f"❌ Video generation failed or file not found: {video_path}")
                return None

        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                retry_count += 1
                print(f"❌ CUDA OOM ({retry_count}/{max_retries}) → giảm batch rồi thử lại")
                batch_size = max(1, batch_size // 2)
                cleanup_cuda_memory()
                time.sleep(2)
                continue
            else:
                print(f"❌ Runtime error: {e}")
                return None
        except Exception as e:
            print(f"❌ Error generating video for text: {e}")
            return None
    return None

def create_lecture_video(sad_talker, slides_data, source_image, language, voice_mode, cloned_voice_name, cloned_lang,
                         preprocess_type, is_still_mode, enhancer, batch_size, size_of_image, pose_style, gender=None, builtin_voice=None,speech_rate: float = 1.0):
    try:
        if not slides_data:
            return None, "❌ Không có slide nào để xử lý!"

        output_dir = os.path.join("results", f"lecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)
        print(f"Creating lecture video in: {output_dir}")

        if check_system_memory() < 2.0:
            print("⚠️ Warning: Low system memory detected.")

        # Ảnh giáo viên an toàn
        safe_image_path = os.path.join(output_dir, "source_image.png")
        if not source_image or not os.path.exists(source_image):
            return None, "❌ Không tìm thấy ảnh nguồn!"
        shutil.copy2(source_image, safe_image_path)
        print(f"✅ Source image copied: {safe_image_path}")

        total_duration = 0.0
        temp_teacher_videos = []     # SadTalker outputs
        final_piece_files = []       # slide_i.mp4 sau khi overlay PIP

        for i, slide_data in enumerate(slides_data):
            print(f"\n--- Processing slide {i+1}/{len(slides_data)} ---")

            if not os.path.exists(safe_image_path):
                if os.path.exists(source_image):
                    shutil.copy2(source_image, safe_image_path)
                else:
                    print("❌ Source image missing, abort.")
                    break

            # Tạo ảnh slide (hoặc copy ảnh gốc)
            slide_image_path = os.path.join(output_dir, f"slide_{i+1:02d}.png")
            original_image = slide_data.get('image_path')
            if original_image and os.path.exists(original_image):
                try:
                    shutil.copy2(original_image, slide_image_path)
                except Exception as e:
                    print(f"⚠️ Copy original slide failed: {e}")
                    if not create_slide_image_with_text(slide_data['text'], slide_image_path):
                        print(f"❌ Failed to create slide image for slide {i+1}")
                        continue
            else:
                if not create_slide_image_with_text(slide_data['text'], slide_image_path):
                    print(f"❌ Failed to create slide image for slide {i+1}")
                    continue

            # === Âm thanh slide (tạo 1 lần, có áp dụng speech_rate) ===
            if voice_mode == 'Giọng nhân bản' and cloned_voice_name:
                ref_wav = _find_reference_wav_by_display_name(cloned_voice_name)
                if ref_wav:
                    try:
                        xtts = XTTSInference()
                        lang_code = cloned_lang if cloned_lang else language
                        audio_path = xtts.synthesize(slide_data['text'], lang_code, ref_wav)
                    except Exception as e:
                        print(f"XTTS failed for slide {i+1}, fallback gTTS: {e}")
                        audio_path = convert_text_to_audio(slide_data['text'], language)
                else:
                    audio_path = convert_text_to_audio(slide_data['text'], language)
            else:
                audio_path = convert_text_to_audio(
                    text=slide_data['text'],
                    language=language,
                    gender=gender,
                    preferred_voice=builtin_voice or None
                )

            if not audio_path:
                print(f"❌ Failed TTS for slide {i+1}, create silent 3s")
                try:
                    from pydub import AudioSegment
                    silent_wav = os.path.join(output_dir, f"silent_{i+1:02d}.wav")
                    AudioSegment.silent(duration=3000).export(silent_wav, format="wav")
                    audio_path = silent_wav
                except Exception as e:
                    print(f"❌ Cannot create silent audio: {e}")
                    continue
            # Áp dụng tốc độ đọc
            audio_path = adjust_audio_speed(audio_path, speech_rate)
            audio_duration = get_audio_duration(audio_path)
            if audio_duration <= 0.1:
                audio_duration = 3.0
            print(f"Audio duration for slide {i+1}: {audio_duration:.2f}s")

            # === Sinh video teacher từ AUDIO ĐÃ ĐIỀU CHỈNH ===
            print("🎬 Generating teacher video…")
            teacher_video_path = generate_video_for_text(
                sad_talker, safe_image_path, slide_data['text'], language, voice_mode,
                cloned_voice_name, cloned_lang, preprocess_type, is_still_mode,
                enhancer, batch_size, size_of_image, pose_style,
                gender=gender, builtin_voice=builtin_voice,
                pre_synth_audio_path=audio_path,    # NEW
                speech_rate=speech_rate             # NEW (cho đồng bộ)
            )
            cleanup_cuda_memory()

            if not teacher_video_path or not os.path.exists(teacher_video_path):
                print(f"❌ Teacher video failed for slide {i+1}")
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                continue

            # Overlay bằng ffmpeg → file mp4 cho slide i
            slide_mp4 = os.path.abspath(os.path.join(output_dir, f"slide_{i+1:03d}.mp4"))
            try:
                pip_composite_ffmpeg(
                    slide_png=slide_image_path,
                    teacher_mp4=teacher_video_path,
                    out_mp4=slide_mp4,
                    pip_ratio=0.10,   # 10% rộng slide
                    margin=50,
                    prefer_nvenc=True,
                    fps=25
                )
            except Exception as e:
                print(f"❌ ffmpeg overlay failed on slide {i+1}: {e}")
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                continue

            final_piece_files.append(slide_mp4)
            temp_teacher_videos.append(teacher_video_path)
            total_duration += audio_duration

            # cleanup audio tạm
            time.sleep(0.3)
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass

            # có thể xóa ảnh slide để tiết kiệm dung lượng (tuỳ chọn)
            try:
                if os.path.exists(slide_image_path):
                    os.remove(slide_image_path)
            except Exception:
                pass

            print(f"✅ Slide {i+1} done → {os.path.basename(slide_mp4)}")

        if not final_piece_files:
            return None, "❌ Không thể tạo video cho bất kỳ slide nào!"

        print(f"\n--- Creating final lecture video (concat) ---")
        print(f"Total slides: {len(final_piece_files)}")
        print(f"Total duration (audio-based): {total_duration:.2f}s")

        final_video_path = os.path.join(output_dir, "lecture_final.mp4")

        # ffmpeg concat demuxer (siêu nhanh, không tái mã hoá)
        concat_list = os.path.join(output_dir, "concat_list.txt")
        with open(concat_list, "w", encoding="utf-8") as f:
            for p in final_piece_files:
                ap = os.path.abspath(p)
                # escape dấu nháy đơn nếu có (phòng hờ)
                ap = ap.replace("'", r"'\''")
                f.write(f"file '{ap}'\n")
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", concat_list, "-c", "copy", final_video_path]
        try:
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"❌ ffmpeg concat failed: {e} → fallback MoviePy (sẽ chậm hơn)")
            try:
                reopened = [VideoFileClip(p) for p in final_piece_files]
                final_clip = concatenate_videoclips(reopened, method="chain")
                final_clip.write_videofile(
                    final_video_path,
                    codec="libx264",
                    audio_codec="aac",
                    verbose=False,
                    logger=None,
                    preset="ultrafast",
                    ffmpeg_params=["-crf", "23"]
                )
                for rc in reopened:
                    try:
                        rc.close()
                    except Exception:
                        pass
            except Exception as concat_fallback_error:
                return None, f"❌ Failed to concatenate video clips: {concat_fallback_error}"

        # dọn concat list
        try:
            os.remove(concat_list)
        except Exception:
            pass

        # xoá teacher videos tạm
        for v in temp_teacher_videos:
            if os.path.exists(v):
                try:
                    os.remove(v)
                except Exception:
                    pass

        # dọn temp SadTalker dirs (uuid-like)
        temp_dirs_deleted = 0
        results_dir = "results"
        if os.path.exists(results_dir):
            for item in os.listdir(results_dir):
                p = os.path.join(results_dir, item)
                if os.path.isdir(p) and len(item) == 36 and '-' in item:
                    try:
                        shutil.rmtree(p)
                        temp_dirs_deleted += 1
                    except Exception:
                        pass
        cleanup_cuda_memory()
        print(f"✅ Lecture video created: {final_video_path}")
        status_text = f"✅ Hoàn thành! Đã tạo video bài giảng với {len(slides_data)} slide, tổng thời gian (ước tính): {total_duration:.1f}s"
        return final_video_path, status_text        

    except Exception as e:
        print(f"Error in create_lecture_video: {str(e)}")
        return None, f"❌ Lỗi tạo video bài giảng: {str(e)}"

def adjust_audio_speed(in_path: str, rate: float) -> str:
    """
    Dùng ffmpeg atempo để đổi tốc độ đọc (giữ cao độ).
    - rate=1.0: giữ nguyên
    - 0.5 <= rate <= 2.0: dùng 1 filter
    - Ngoài khoảng trên: xâu chuỗi nhiều filter atempo
    Trả về đường dẫn file .wav mới (không ghi đè bản gốc).
    """
    try:
        if not in_path or not os.path.exists(in_path) or abs(rate - 1.0) < 1e-3:
            return in_path

        base, ext = os.path.splitext(in_path)
        out_path = f"{base}_r{rate:.2f}{ext or '.wav'}"

        # Xây chuỗi atempo để mọi phân đoạn đều trong [0.5, 2.0]
        r = float(rate)
        filters = []
        while r > 2.0 + 1e-9:
            filters.append("atempo=2.0")
            r /= 2.0
        while r < 0.5 - 1e-9:
            filters.append("atempo=0.5")
            r /= 0.5
        filters.append(f"atempo={r:.3f}")
        atempo_chain = ",".join(filters)

        cmd = ["ffmpeg", "-y", "-i", in_path, "-filter:a", atempo_chain, out_path]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            err = p.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"ffmpeg atempo failed: {err}")

        return out_path if os.path.exists(out_path) else in_path
    except Exception as e:
        print(f"⚠️ adjust_audio_speed warning: {e}")
        return in_path


def generate_lecture_video_handler(
    sad_talker, pptx, img, lang, voice_mode, cloned_voice, gender, builtin_voice,
    cloned_lang, preprocess, still, enh, batch, size, pose,
    speech_rate,
    user_slides_text=None
):
    # Parse text người dùng (nếu có)
    user_slides = []
    if user_slides_text and str(user_slides_text).strip():
        user_slides = parse_user_slides_text(user_slides_text)

    ppt_slides = []
    if pptx:
        # dùng để lấy ảnh gốc (image_path); bỏ qua text trong PPT
        ppt_slides = extract_slides_from_pptx(pptx)

    if user_slides:
        # ==> dùng text người dùng + ảnh PPT
        slides_data = merge_user_text_with_ppt_images(user_slides, ppt_slides)
    else:
        # không có text người dùng -> fallback dùng PPT cả text lẫn ảnh
        if not ppt_slides:
            return None, "❌ Vui lòng chọn PowerPoint hoặc nhập nội dung slide!"
        slides_data = ppt_slides

    if not img:
        return None, "❌ Vui lòng chọn ảnh giáo viên!"
    if not slides_data:
        return None, "❌ Không có slide nào để xử lý!"

    return create_lecture_video(
        sad_talker, slides_data, img,
        lang or 'vi',
        voice_mode, cloned_voice, cloned_lang,
        preprocess, still, enh, batch, size, pose,
        gender=gender or 'Nữ',
        builtin_voice=builtin_voice,
        speech_rate=speech_rate
    )


