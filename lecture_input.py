import os
import zipfile
import subprocess
import tempfile
import logging

import gradio as gr
import xml.etree.ElementTree as ET
import re
from pptx.enum.shapes import MSO_SHAPE_TYPE
from shutil import which

from gtts import gTTS
from PIL import Image
try:
    import pytesseract
except Exception:
    pytesseract = None
from pptx import Presentation
from pdf2image import convert_from_path
from src.utils.math_formula_processor import MathFormulaProcessor, process_math_text
from src.utils.xtts_clone import create_cloned_voice, list_supported_languages
import unicodedata
import asyncio
try:
    import edge_tts  # cho chọn voice nam/nữ
except Exception:
    edge_tts = None

# Thiết lập logging
logger = logging.getLogger(__name__)
# Voice mẫu phổ biến, bạn có thể bổ sung thêm
EDGE_VOICE_BY_LANG_GENDER = {
    "vi": {"Nữ": "vi-VN-HoaiMyNeural",      "Nam": "vi-VN-NamMinhNeural"},
    "en": {"Nữ": "en-US-JennyNeural",        "Nam": "en-US-GuyNeural"},
    "zh": {"Nữ": "zh-CN-XiaoxiaoNeural",     "Nam": "zh-CN-YunxiNeural"},
    "ja": {"Nữ": "ja-JP-NanamiNeural",       "Nam": "ja-JP-KeitaNeural"},
    "ko": {"Nữ": "ko-KR-SunHiNeural",        "Nam": "ko-KR-InJoonNeural"},
    "fr": {"Nữ": "fr-FR-DeniseNeural",       "Nam": "fr-FR-HenriNeural"},
    "de": {"Nữ": "de-DE-KatjaNeural",        "Nam": "de-DE-ConradNeural"},
    "es": {"Nữ": "es-ES-ElviraNeural",       "Nam": "es-ES-AlvaroNeural"},
    "it": {"Nữ": "it-IT-ElsaNeural",         "Nam": "it-IT-IsmaelNeural"},
    "pt": {"Nữ": "pt-BR-FranciscaNeural",    "Nam": "pt-BR-AntonioNeural"},
}
def get_edge_voice(lang_code: str, gender_label: str) -> str | None:
    try:
        return EDGE_VOICE_BY_LANG_GENDER.get(lang_code, {}).get(gender_label)
    except Exception:
        return None
async def _edge_tts_save(text: str, voice: str, out_path: str):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+0%", volume="+0%")
    await communicate.save(out_path)


def _get_cloned_voice_options(root_dir='./cloned_voices'):
    """Scan cloned voices and return display names from config.json.

    Fallback to mp3 filename if config is missing.
    Layout: ./cloned_voices/<voice_id>/{config.json, reference.mp3, reference_16k_mono.wav}
    """
    options = []
    try:
        if not os.path.isdir(root_dir):
            return options
        for voice_id in sorted(os.listdir(root_dir)):
            dir_path = os.path.join(root_dir, voice_id)
            if not os.path.isdir(dir_path):
                continue
            cfg_path = os.path.join(dir_path, 'config.json')
            if os.path.isfile(cfg_path):
                try:
                    import json
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                    name = cfg.get('display_name')
                    if name:
                        options.append(name)
                        continue
                except Exception:
                    pass
            # fallback: use first mp3 filename
            for fname in os.listdir(dir_path):
                if fname.lower().endswith('.mp3'):
                    options.append(os.path.splitext(fname)[0])
                    break
    except Exception:
        pass
    return options

def _on_voice_mode_change(mode):
    """Return visibility updates for the two blocks based on selected mode."""
    use_builtin = mode == 'Ngôn ngữ có sẵn'
    use_clone = mode == 'Giọng nhân bản'
    return gr.update(visible=use_builtin), gr.update(visible=use_clone)

def _handle_create_clone(file):
    """Handle creating a cloned voice from uploaded mp3.

    Returns status text and refreshed dropdown choices.
    """
    if file is None:
        return "❌ Vui lòng tải lên file mp3 giọng mẫu", gr.update()
    ok, name, err = create_cloned_voice(file.name, voices_root='./cloned_voices')
    if not ok:
        return f"❌ Tạo giọng clone thất bại: {err}", gr.update()
    # Refresh options after successful creation
    options = _get_cloned_voice_options()
    # Try to select the newly created display name if present
    new_value = name if name in options else None
    return f"✅ Đã tạo giọng clone: {name}", gr.update(choices=options, value=new_value)

def convert_pptx_to_images(pptx_path, dpi=220):
    # Kiểm tra LibreOffice
    if which("/home/dunghm/LibreOffice-still.basic-x86_64.AppImage") is None:
        raise RuntimeError("Không tìm thấy LibreOffice (soffice). Vui lòng cài LibreOffice để chuyển PPTX -> PDF.")

    tmpdir = tempfile.mkdtemp(prefix="pptx2img_")
    # Chuyển PPTX -> PDF
    try:
        subprocess.run(
            ["/home/dunghm/LibreOffice-still.basic-x86_64.AppImage", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, pptx_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Chuyển PPTX sang PDF thất bại: {e}")

    pdf_path = os.path.join(tmpdir, os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError("Không tạo được PDF từ PPTX. Kiểm tra file đầu vào.")

    # PDF -> PNG (cần Poppler)
    try:
        images = convert_from_path(pdf_path, dpi=dpi, output_folder=tmpdir, fmt='png')
    except Exception as e:
        raise RuntimeError("Lỗi convert PDF -> ảnh. Có thể thiếu Poppler (poppler-utils).") from e

    img_paths = []
    for i, img in enumerate(images, 1):
        img_path = os.path.join(tmpdir, f"slide-{i:02d}.png")
        img.save(img_path)
        img_paths.append(img_path)

    # Trả về danh sách đường dẫn ảnh theo thứ tự slide
    return img_paths

def convert_text_to_audio(text, language='vi', gender='Nữ', preferred_voice: str | None = None):
    try:
        language = language or 'vi'  # 🔧 Bổ sung dòng này
        if not text or text.strip() == "":
            return None

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        out_path = tmp.name
        tmp.close()

        voice = preferred_voice or get_edge_voice(language, gender)
        if edge_tts is not None and voice:
            print(f"[TTS] Using Edge TTS voice: {voice} (lang={language}, gender={gender})")
            try:
                asyncio.run(_edge_tts_save(text, voice, out_path))
                return out_path
            except Exception as e:
                logger.warning(f"Edge TTS failed, fallback gTTS. Reason: {e}")

        print(f"[TTS] Using gTTS (no voice/gender control). lang={language}")
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(out_path)
        return out_path
    except Exception as e:
        logger.exception(f"TTS error: {e}")
        return None


def read_text_file(file):
    """
    Read text content from uploaded file
    """
    if file is None:
        return "", "❌ Vui lòng chọn file văn bản!"
    
    try:
        # Get file extension
        file_path = file.name
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check if it's a supported file type
        if file_ext not in ['.txt', '.md', '.doc', '.docx', '.rtf']:
            return "", "❌ Chỉ hỗ trợ file văn bản (.txt, .md, .doc, .docx, .rtf)"
        
        content = ""
        
        # Handle different file types
        if file_ext == '.docx':
            # For .docx files, we need to extract text properly
            try:
                import zipfile
                import xml.etree.ElementTree as ET
                
                # .docx is a ZIP file containing XML
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    # Find the document.xml file
                    if 'word/document.xml' in zip_file.namelist():
                        xml_content = zip_file.read('word/document.xml')
                        root = ET.fromstring(xml_content)
                        
                        # Extract text from all text elements
                        text_elements = []
                        for elem in root.iter():
                            if elem.text and elem.text.strip():
                                text_elements.append(elem.text.strip())
                        
                        content = ' '.join(text_elements)
                    else:
                        return "", "❌ Không thể đọc nội dung từ file .docx"
                        
            except Exception as e:
                return "", f"❌ Lỗi đọc file .docx: {str(e)}"
        
        elif file_ext == '.doc':
            # For .doc files, we'll try to read as text but warn user
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    return "", "❌ Không thể đọc file .doc. Vui lòng chuyển đổi sang .txt hoặc .docx"
        
        else:
            # For .txt, .md, .rtf files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        # Clean content - remove null bytes and other control characters
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        
        # Strip whitespace and check if empty
        content = content.strip()
        if not content:
            return "", "❌ File văn bản trống hoặc chỉ chứa ký tự đặc biệt!"
        
        return content, f"✅ Đã đọc thành công file: {os.path.basename(file_path)} ({len(content)} ký tự thực tế)"
    
    except Exception as e:
        return "", f"❌ Lỗi đọc file: {str(e)}"

# ---------- helpers for robust reading order ----------
_NUM_BADGE = re.compile(r"^\s*\d{1,3}[.)-]?\s*$")

def _is_numeric_badge(txt: str) -> bool:
    return bool(_NUM_BADGE.match((txt or "").strip()))

def _median(vals):
    vals = sorted(int(v) for v in vals if v is not None and v > 0)
    if not vals:
        return 0
    n = len(vals)
    return vals[n//2] if n % 2 else (vals[n//2 - 1] + vals[n//2]) // 2

def _iter_text_shapes(shapes, dx=0, dy=0):
    """
    Flatten shapes (including grouped shapes) and yield dicts:
    {'text','left','top','width','height'}
    dx/dy accumulate offsets for grouped shapes.
    """
    for shp in shapes:
        try:
            st = shp.shape_type
        except Exception:
            st = None

        if st == MSO_SHAPE_TYPE.GROUP:
            ox, oy = int(getattr(shp, "left", 0)), int(getattr(shp, "top", 0))
            yield from _iter_text_shapes(shp.shapes, dx + ox, dy + oy)
            continue

        # get text
        txt = ""
        if getattr(shp, "has_text_frame", False) and getattr(shp, "text_frame", None) is not None:
            txt = shp.text_frame.text or ""
        elif hasattr(shp, "text"):
            txt = shp.text or ""
        txt = (txt or "").strip()
        if not txt:
            continue

        yield {
            "text": txt,
            "left": int(getattr(shp, "left", 0)) + dx,
            "top": int(getattr(shp, "top", 0)) + dy,
            "width": int(getattr(shp, "width", 0)),
            "height": int(getattr(shp, "height", 0)),
        }

def _group_columns(items, col_thr):
    """Group items into columns by proximity in X (left)."""
    cols = []
    for s in sorted(items, key=lambda a: a["left"]):
        placed = False
        for c in cols:
            # compare against column representative x
            if abs(s["left"] - c["x"]) <= col_thr:
                c["items"].append(s)
                # update running avg x
                c["x"] = (c["x"] * (len(c["items"]) - 1) + s["left"]) // len(c["items"])
                placed = True
                break
        if not placed:
            cols.append({"x": s["left"], "items": [s]})
    return cols

def _group_rows(items, row_thr):
    """Group items into rows by proximity in Y (center y)."""
    rows = []
    for s in sorted(items, key=lambda a: a["top"]):
        cy = s["top"] + max(1, s.get("height", 0)) // 2
        placed = False
        for r in rows:
            if abs(cy - r["cy"]) <= row_thr:
                r["items"].append(s)
                r["cy"] = (r["cy"] * (len(r["items"]) - 1) + cy) // len(r["items"])
                placed = True
                break
        if not placed:
            rows.append({"cy": cy, "items": [s]})
    return rows

def _compose_row_text(row_items):
    """
    Compose a single row's textual representation.
    - sort left->right
    - if exists numeric badge and other text, put the first numeric badge before the combined text
    """
    row_items = sorted(row_items, key=lambda s: s["left"])
    nums = [s for s in row_items if _is_numeric_badge(s["text"])]
    others = [s for s in row_items if not _is_numeric_badge(s["text"])]

    if nums and others:
        # take first numeric badge (if multiple), then all other text items in left->right order
        badge = nums[0]["text"].strip()
        other_text = " ".join(s["text"].strip() for s in others if s["text"].strip())
        if other_text:
            return badge + " " + other_text
        else:
            return badge
    # else join everything left->right
    return " ".join(s["text"].strip() for s in row_items if s["text"].strip())

# ---------- end helpers ----------


def extract_slides_from_pptx(pptx_file):
    """
    Robust slide text extractor:
    - tries MathFormulaProcessor first (existing flow)
    - if fallback, uses pptx Presentation reading with:
        * flattening groups
        * grouping into columns then rows
        * composing rows with numeric-badge-first rule
    - keeps original image conversion + OCR fallback (pytesseract) afterwards
    """
    slides_data = []
    image_paths = convert_pptx_to_images(pptx_file.name, dpi=220)

    # Use MathFormulaProcessor first (original flow)
    math_processor = MathFormulaProcessor()
    processed_result = math_processor.process_powerpoint_text(pptx_file.name)

    if processed_result.get('error'):
        logger.warning(f"Lỗi xử lý công thức toán học: {processed_result['error']}, sử dụng phương pháp cũ")
        prs = Presentation(pptx_file.name)

        for i, slide in enumerate(prs.slides):
            # flatten shapes & collect candidate text shapes
            items = list(_iter_text_shapes(slide.shapes))

            if items:
                            # compute thresholds using medians to adapt to different slide sizes
                h_med = _median([s["height"] for s in items if s.get("height", 0) > 0]) or max(1, prs.slide_height // 30)
                w_med = _median([s["width"] for s in items if s.get("width", 0) > 0]) or max(1, prs.slide_width // 10)

                # thresholds (tunable) - further lower column threshold to avoid over-merging columns
                # This helps slides with a left title (e.g., "Nội Dung") and a right list become two columns
                row_thr = max(int(h_med * 0.6), int(prs.slide_height / 90))
                col_thr = max(int(w_med * 0.4), int(prs.slide_width / 80))

                # 1) group into columns left->right
                cols = _group_columns(items, col_thr)
                cols.sort(key=lambda c: c["x"])

                # If grouping produced a single column but items are widely spread horizontally,
                # split into two columns using a median X cut (simple heuristic, more aggressive).
                if len(cols) == 1 and items:
                    lefts = [s["left"] for s in items]
                    spread = max(lefts) - min(lefts)
                    if spread > (prs.slide_width * 0.18):  # if items span >18% of slide width, attempt split
                        mid_x = (min(lefts) + max(lefts)) // 2
                        left_items = [s for s in items if s["left"] <= mid_x]
                        right_items = [s for s in items if s["left"] > mid_x]
                        if left_items and right_items:
                            cols = [
                                {"x": int(_median([s["left"] for s in left_items]) or min(lefts)), "items": left_items},
                                {"x": int(_median([s["left"] for s in right_items]) or max(lefts)), "items": right_items},
                            ]
                            cols.sort(key=lambda c: c["x"])

                # 2) for each column, group into rows top->bottom and compose row text
                #    Keep track of an x-position per line for later block ordering
                line_objs = []  # [{text, x, y}]
                for col in cols:
                    rows = _group_rows(col["items"], row_thr)
                    rows.sort(key=lambda r: r["cy"])
                    for r in rows:
                        line = _compose_row_text(r["items"])
                        if line:
                            min_left = min(s["left"] for s in r["items"]) if r["items"] else 0
                            line_objs.append({"text": line, "x": min_left, "y": r["cy"]})


                # 3) Global left->right then top->bottom ordering of all line blocks
                #    ensures left title (e.g., "Nội Dung") appears before right list
                lines = [lo["text"] for lo in sorted(line_objs, key=lambda lo: (lo["x"], lo["y"]))]
                if line_objs:
                    def _norm(s: str) -> str:
                        base = unicodedata.normalize('NFKD', (s or '')).encode('ASCII', 'ignore').decode('ASCII')
                        return base.lower()

                    # Identify badge lines (e.g., "01 ...")
                    badge_los = [lo for lo in line_objs if _is_numeric_badge(lo["text"]) or _norm(lo["text"]).startswith(tuple([f"{i:02d}" for i in range(1, 10)]))]
                    non_badge_los = [lo for lo in line_objs if lo not in badge_los]
                    # If a clearly left-side non-badge block exists, force it to the front
                    if badge_los and non_badge_los:
                        min_badge_x = min(lo["x"] for lo in badge_los)
                        left_block = [lo for lo in non_badge_los if lo["x"] < min_badge_x - int(prs.slide_width * 0.05)]
                        if left_block:
                            left_block = sorted(left_block, key=lambda lo: (lo["x"], lo["y"]))
                            others = [lo for lo in sorted(line_objs, key=lambda lo: (lo["x"], lo["y"])) if lo not in left_block]
                            lines = [lo["text"] for lo in (left_block + others)]

                    # Title prioritization (accent-insensitive)
                    title_keywords = ("noi dung", "muc luc")
                    title_los = [lo for lo in line_objs if any(kw in _norm(lo["text"]) for kw in title_keywords)]
                    if title_los:
                        title_set = set(id(lo) for lo in title_los)
                        rest = [lo for lo in line_objs if id(lo) not in title_set]
                        line_order = sorted(title_los, key=lambda lo: lo["y"]) + sorted(rest, key=lambda lo: (lo["x"], lo["y"]))
                        lines = [lo["text"] for lo in line_order]

                    # If exactly one numeric-only line exists (like "01"), move it to the very front
                    numeric_only_lines = [lo for lo in line_objs if _is_numeric_badge(lo["text"]) and len(lo["text"].strip()) <= 4]
                    if len(numeric_only_lines) == 1:
                        badge = numeric_only_lines[0]["text"]
                        remaining = [t for t in lines if t is not badge]
                        lines = [badge] + remaining

                # Final safety: ensure title-like lines are at the beginning
                if lines:
                    def _norm2(s: str) -> str:
                        return unicodedata.normalize('NFKD', (s or '')).encode('ASCII', 'ignore').decode('ASCII').lower()
                    title_keywords2 = ("noi dung", "muc luc")
                    titles = [ln for ln in lines if any(kw in _norm2(ln) for kw in title_keywords2)]
                    if titles:
                        rest = [ln for ln in lines if ln not in titles]
                        lines = titles + rest

                # join lines with newlines to preserve vertical structure
                text = "\n".join(lines).strip()
            else:
                text = ""

            processed_text = process_math_text(text)
            slides_data.append({
                'slide_number': i + 1,
                'text': processed_text,
                'image_path': image_paths[i] if i < len(image_paths) else None,
                'has_math_objects': False
            })
    else:
        # use math_processor result if successful
        for slide_info in processed_result['slides']:
            slides_data.append({
                'slide_number': slide_info['slide_number'],
                'text': slide_info['processed_text'],
                'image_path': image_paths[slide_info['slide_number'] - 1] if slide_info['slide_number'] - 1 < len(image_paths) else None,
                'has_math_objects': slide_info['has_math_objects']
            })

    # OCR fallback: nếu text rỗng, thử nhận diện từ ảnh slide (giữ như cũ)
    try:
        if pytesseract is not None:
            for i, s in enumerate(slides_data):
                if not s['text'] or s['text'].strip() == "":
                    img_path = s.get('image_path') or (image_paths[i] if i < len(image_paths) else None)
                    if img_path and os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            ocr_text = pytesseract.image_to_string(img, lang='vie+eng')
                        except Exception:
                            ocr_text = ''
                        ocr_text = (ocr_text or '').strip()
                        if ocr_text:
                            s['text'] = process_math_text(ocr_text)
        else:
            logger.warning("pytesseract chưa được cài, bỏ qua OCR fallback.")
    except Exception as e:
        logger.warning(f"Lỗi OCR fallback: {e}")

    return slides_data


def extract_lecture_slides(file):
    """Handler function for extracting slides from PowerPoint"""
    if file:
        slides_data = extract_slides_from_pptx(file)
        if slides_data:
            slides_text = []
            total_math_slides = 0
            
            for i, slide in enumerate(slides_data):
                slide_num = slide['slide_number']
                text_preview = slide['text'][:100] + "..." if len(slide['text']) > 100 else slide['text']
                
                # Thêm thông tin về công thức toán học
                if slide.get('has_math_objects', False):
                    slides_text.append(f"Slide {slide_num}: {text_preview} [📐 Có công thức toán học]")
                    total_math_slides += 1
                else:
                    slides_text.append(f"Slide {slide_num}: {text_preview}")
            
            # Thêm thống kê
            summary = f"\n\n📊 Thống kê: {len(slides_data)} slides, {total_math_slides} slides có công thức toán học"
            if total_math_slides > 0:
                summary += "\n✅ Đã xử lý thành công các ký tự đặc biệt và công thức toán học!"
            
            return "\n\n".join(slides_text) + summary
    return "❌ Vui lòng chọn file PowerPoint!"

def set_lecture_fast_mode():
    """Set fast mode preset for lecture generation"""
    return 256, 'crop', False, 2, False, 0

def _list_edge_voices_for(lang_code: str, gender: str):
    v = EDGE_VOICE_BY_LANG_GENDER.get(lang_code or "", {})
    if not v:
        return []
    if gender in ("Nam","Nữ"):
        return [v.get(gender)] if v.get(gender) else []
    # không xảy ra, nhưng giữ phòng hờ
    return list(v.values())

def _on_builtin_lang_or_gender_change(lang, gender):
    voices = _list_edge_voices_for(lang, gender)
    # auto select giọng tương ứng (nếu có)
    value = voices[0] if voices else None
    return gr.update(choices=voices, value=value)



def create_lecture_input_interface():
    """Tạo giao diện input cho lecture"""
    
    with gr.Row().style(equal_height=False):
        with gr.Column(variant='panel'):
            # Source image upload
            gr.Markdown("### 👨‍🏫 Ảnh Giáo Viên")
            lecture_source_image = gr.Image(label="Ảnh khuôn mặt giáo viên", source="upload", type="filepath", elem_id="lecture_source_image").style(width=512)
            
            # PowerPoint file upload
            gr.Markdown("### 📊 File PowerPoint Bài Giảng")
            lecture_pptx_file = gr.File(
                label="Chọn file PowerPoint (.pptx)",
                file_types=[".pptx"],
                elem_id="lecture_pptx_file"
            )
            
            # Voice mode switcher
            gr.Markdown("### 🔊 Chọn chế độ giọng đọc")
            lecture_voice_mode = gr.Radio(
                choices=["Ngôn ngữ có sẵn", "Giọng nhân bản"],
                label="Chế độ giọng đọc",
                value=None,
                elem_id="lecture_voice_mode"
            )

            # Built-in language block (hidden by default until user selects)
            builtin_block = gr.Group(visible=False)
            with builtin_block:
                lecture_audio_language = gr.Dropdown(
                    choices=["vi", "en", "zh", "ja", "ko", "fr", "de", "es", "it", "pt"],
                    value=None,
                    label="Ngôn ngữ giảng bài",
                    elem_id="lecture_audio_language"
                )
                # NEW: chọn giới tính
                lecture_builtin_gender = gr.Radio(
                    choices=["Nữ", "Nam"], value="Nữ",
                    label="Giọng đọc"
                )

                # NEW: chọn voice cụ thể (tự đổi theo language + gender)
                lecture_builtin_voice = gr.Dropdown(
                    choices=[], value=None,
                    label="Giọng cụ thể (tùy chọn)",
                    info="Nếu để trống sẽ dùng voice mặc định theo ngôn ngữ + giới tính."
                )
                lecture_audio_language.change(
                    fn=_on_builtin_lang_or_gender_change,
                    inputs=[lecture_audio_language, lecture_builtin_gender],
                    outputs=[lecture_builtin_voice]
                )
                lecture_builtin_gender.change(
                    fn=_on_builtin_lang_or_gender_change,
                    inputs=[lecture_audio_language, lecture_builtin_gender],
                    outputs=[lecture_builtin_voice]
                )
            # Cloned voice block (accordion thu nhỏ)
            cloned_block = gr.Accordion("🧬 Sử dụng giọng đọc nhân bản (XTTS-v2)", open=False, visible=False)
            with cloned_block:
                clone_upload = gr.File(
                    label="Tải lên file mp3 giọng mẫu (để tạo bản clone)",
                    file_types=[".mp3"],
                    elem_id="clone_reference_mp3"
                )
                clone_create_btn = gr.Button("Tạo bản giọng clone")
                cloned_voice_list = gr.Dropdown(
                    choices=_get_cloned_voice_options(),
                    label="Chọn bản giọng clone",
                    value=None,
                    elem_id="cloned_voice_list"
                )
                cloned_voice_lang = gr.Dropdown(
                    choices=list_supported_languages(),
                    value=None,
                    label="Ngôn ngữ nội dung (XTTS-v2)",
                    elem_id="cloned_voice_language"
                )
                clone_status = gr.Textbox(label="Trạng thái giọng nhân bản", interactive=False)

            # Preview extracted slides
            gr.Markdown("### 📝 Nội dung từ PowerPoint")
            lecture_slides_preview = gr.Textbox(
                label="Nội dung đã trích xuất từ các slide",
                lines=8,
                interactive=False,
                elem_id="lecture_slides_preview"
            )
            
            # Extract slides button
            extract_lecture_slides_btn = gr.Button(
                '📂 Trích xuất nội dung từ PowerPoint',
                elem_id="extract_lecture_slides_btn",
                variant='secondary'
            )
            
            # Generate lecture video button
            generate_lecture_btn = gr.Button(
                '🎬 Tạo Video Bài Giảng',
                elem_id="generate_lecture_btn",
                variant='primary',
                js="() => { document.getElementById('lecture_final_video1').scrollIntoView({behavior: 'smooth'}); }"
            )
                       
        
        with gr.Column(variant='panel'):
            # Settings
            with gr.Tabs(elem_id="lecture_settings"):
                with gr.TabItem('⚙️ Cài đặt'):
                    gr.Markdown("Cài đặt cho video bài giảng")
                    with gr.Column(variant='panel'):
                        lecture_pose_style = gr.Slider(minimum=0, maximum=46, step=1, label="Pose style", value=0)
                        lecture_size_of_image = gr.Radio([256, 512], value=256, label='Độ phân giải ảnh', info="256 = Nhanh, 512 = Chất lượng cao")
                        lecture_preprocess_type = gr.Radio(['crop', 'resize','full', 'extcrop', 'extfull'], value='crop', label='Xử lý ảnh', info="crop = Nhanh nhất")
                        lecture_is_still_mode = gr.Checkbox(label="Still Mode (ít chuyển động đầu)")
                        lecture_batch_size = gr.Slider(label="Batch size", step=1, maximum=10, value=1, info="1 = Tiết kiệm VRAM, 2-4 = Nhanh hơn nhưng tốn VRAM")
                        lecture_enhancer = gr.Checkbox(label="GFPGAN làm Face enhancer (chậm hơn)")
                        
                        # Fast mode preset button
                        lecture_fast_mode_btn = gr.Button(
                            '⚡ Chế độ nhanh (256px, batch=2, không enhancer)',
                            elem_id="lecture_fast_mode_btn",
                            variant='secondary'
                        )
                        
                        lecture_fast_mode_btn.click(
                            fn=set_lecture_fast_mode,
                            outputs=[lecture_size_of_image, lecture_preprocess_type, lecture_is_still_mode, lecture_batch_size, lecture_enhancer, lecture_pose_style]
                        )
            
            # Results placeholder (will be connected to output module)
            with gr.Tabs(elem_id="lecture_results"):
                gr.Markdown("### 🎬 Video Bài Giảng")
                lecture_final_video = gr.Video(label="Video bài giảng hoàn chỉnh", elem_id="lecture_final_video1", format="mp4").style(width=512)
                
                gr.Markdown("### 📊 Thông tin Video")
                lecture_info = gr.Textbox(
                    label="Thông tin chi tiết",
                    lines=4,
                    interactive=False,
                    elem_id="lecture_info"
                )
    
    # Event handlers
    extract_lecture_slides_btn.click(
        fn=extract_lecture_slides,
        inputs=[lecture_pptx_file],
        outputs=[lecture_slides_preview]
    )
    lecture_voice_mode.change(
        fn=_on_voice_mode_change,
        inputs=[lecture_voice_mode],
        outputs=[builtin_block, cloned_block]
    )
    clone_create_btn.click(
        fn=_handle_create_clone,
        inputs=[clone_upload],
        outputs=[clone_status, cloned_voice_list]
    )
    
    # Return all components for connection with output module
    return {
        'source_image': lecture_source_image,
        'pptx_file': lecture_pptx_file,
        'audio_language': lecture_audio_language,
        'voice_mode': lecture_voice_mode,
        'builtin_block': builtin_block,
        'cloned_block': cloned_block,
        'cloned_voice_list': cloned_voice_list,
        'cloned_voice_language': cloned_voice_lang,
        'clone_upload': clone_upload,
        'clone_create_btn': clone_create_btn,
        'clone_status': clone_status,
        'slides_preview': lecture_slides_preview,
        'extract_btn': extract_lecture_slides_btn,
        'generate_btn': generate_lecture_btn,
        'pose_style': lecture_pose_style,
        'size_of_image': lecture_size_of_image,
        'preprocess_type': lecture_preprocess_type,
        'is_still_mode': lecture_is_still_mode,
        'batch_size': lecture_batch_size,
        'enhancer': lecture_enhancer,
        'fast_mode_btn': lecture_fast_mode_btn,
        'final_video': lecture_final_video,
        'info': lecture_info,
        'builtin_gender': lecture_builtin_gender,
        'builtin_voice': lecture_builtin_voice
    }
