import os
import zipfile
import subprocess
import tempfile
import logging

import gradio as gr
import xml.etree.ElementTree as ET
from shutil import which

from gtts import gTTS
from pptx import Presentation
from pdf2image import convert_from_path
from src.utils.math_formula_processor import MathFormulaProcessor, process_math_text
from src.utils.xtts_clone import create_cloned_voice, list_supported_languages

# Thiết lập logging
logger = logging.getLogger(__name__)



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

def convert_text_to_audio(text, language='vi'):
    """
    Convert text to audio using gTTS
    Returns the path to the generated audio file
    """
    try:
        if not text or text.strip() == "":
            return None
        
        # Create a temporary file for the audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()
        
        # Convert text to speech
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(temp_path)
        
        # Return the audio file path directly for Gradio Audio component
        return temp_path
    except Exception as e:
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

def extract_slides_from_pptx(pptx_file):
    slides_data = []
    image_paths = convert_pptx_to_images(pptx_file.name, dpi=220)
    
    # Sử dụng MathFormulaProcessor để xử lý toàn bộ PowerPoint
    math_processor = MathFormulaProcessor()
    processed_result = math_processor.process_powerpoint_text(pptx_file.name)
    
    if processed_result.get('error'):
        # Nếu có lỗi, fallback về phương pháp cũ
        logger.warning(f"Lỗi xử lý công thức toán học: {processed_result['error']}, sử dụng phương pháp cũ")
        prs = Presentation(pptx_file.name)
        
        for i, slide in enumerate(prs.slides):
            text_chunks = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    text_chunks.append(shape.text.strip())
            text = " ".join(filter(None, text_chunks))
            
            # Vẫn xử lý ký tự đặc biệt cơ bản
            processed_text = process_math_text(text.strip())
            
            slides_data.append({
                'slide_number': i + 1,
                'text': processed_text,
                'image_path': image_paths[i] if i < len(image_paths) else None,
                'has_math_objects': False
            })
    else:
        # Sử dụng kết quả đã xử lý
        for slide_info in processed_result['slides']:
            slides_data.append({
                'slide_number': slide_info['slide_number'],
                'text': slide_info['processed_text'],
                'image_path': image_paths[slide_info['slide_number'] - 1] if slide_info['slide_number'] - 1 < len(image_paths) else None,
                'has_math_objects': slide_info['has_math_objects']
            })
    
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

            # Cloned voice block placeholder
            cloned_block = gr.Group(visible=False)
            with cloned_block:
                gr.Markdown("### 🧬 Sử dụng giọng đọc nhân bản (XTTS‑v2)")
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
                # Language for XTTS‑v2 content generation (full list later)
                cloned_voice_lang = gr.Dropdown(
                    choices=list_supported_languages(),
                    value=None,
                    label="Ngôn ngữ nội dung (XTTS‑v2)",
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
                variant='primary'
            )
            
            # Status
            lecture_status = gr.Textbox(
                label="Trạng thái xử lý",
                interactive=False,
                elem_id="lecture_status"
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
                lecture_final_video = gr.Video(label="Video bài giảng hoàn chỉnh", format="mp4").style(width=512)
                
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
        'status': lecture_status,
        'pose_style': lecture_pose_style,
        'size_of_image': lecture_size_of_image,
        'preprocess_type': lecture_preprocess_type,
        'is_still_mode': lecture_is_still_mode,
        'batch_size': lecture_batch_size,
        'enhancer': lecture_enhancer,
        'fast_mode_btn': lecture_fast_mode_btn,
        'final_video': lecture_final_video,
        'info': lecture_info
    }
