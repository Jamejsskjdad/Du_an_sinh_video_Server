import os, sys
import gradio as gr
from src.gradio_demo import SadTalker

# Import các module mới
from home import create_home_tab, custom_home_css
from lecture_input import create_lecture_input_interface
from lecture_output import generate_lecture_video_handler

try:
    import webui  # in webui
    in_webui = True
except:
    in_webui = False

def switch_to_lecture():
    """Chuyển sang trang tạo video bài giảng"""
    return gr.update(visible=False), gr.update(visible=True)

def switch_to_home():
    """Quay lại trang chủ"""
    return gr.update(visible=True), gr.update(visible=False)

def sadtalker_demo_with_home(checkpoint_path='checkpoints', config_path='src/config', warpfn=None):
    # Set CUDA memory management environment variables
    import os
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
    
    sad_talker = SadTalker(checkpoint_path, config_path, lazy_load=True)

    with gr.Blocks(analytics_enabled=False, title="SadTalker", css=custom_home_css()) as sadtalker_interface:
        # State để quản lý trang hiện tại
        current_page = gr.State("home")
        
        # Container chính
        with gr.Column(elem_classes=["main-container"]):
            # --- TRANG CHỦ ---
            with gr.Column(visible=True, elem_classes=["home-page"]) as home_page:
                # Tạo buttons Gradio thực sự - ẩn nhưng có thể trigger
                with gr.Row(visible=False):
                    start_btn = gr.Button("Start Creating Video", elem_id="start_btn", elem_classes=["hidden-start-btn"])
                
                # Gọi hàm tạo trang chủ và nhận button navigation
                nav_get_started_btn = create_home_tab()
            
            # --- TRANG TẠO VIDEO BÀI GIẢNG ---
            with gr.Column(visible=False, elem_classes=["lecture-page"]) as lecture_page:
                gr.HTML("""
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <h2 style="font-size: 2.5rem; font-weight: bold; color: #111827; margin-bottom: 1rem;">
                            🎓 SadTalker Lecture Video Generator
                        </h2>
                        <p style="font-size: 1.25rem; color: #6B7280; max-width: 48rem; margin: 0 auto;">
                            Tạo video bài giảng kết hợp slide PowerPoint và video giáo viên giảng bài
                        </p>
                    </div>
                """)

                # Nút quay lại trang chủ - nút mũi tên cong đẹp mắt
                back_btn = gr.HTML("""
                    <div style="position: fixed; top: 20px; left: 20px; z-index: 1000;">
                        <button id="back-home-btn" 
                                style="
                                    width: 48px; 
                                    height: 48px; 
                                    border-radius: 50%; 
                                    border: none; 
                                    background: rgba(255, 255, 255, 0.9); 
                                    backdrop-filter: blur(10px);
                                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                                    cursor: pointer;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    transition: all 0.3s ease;
                                "
                                onmouseover="this.style.transform='scale(1.1)'; this.style.background='rgba(255, 255, 255, 1)'; this.style.boxShadow='0 6px 20px rgba(0, 0, 0, 0.2)';"
                                onmouseout="this.style.transform='scale(1)'; this.style.background='rgba(255, 255, 255, 0.9)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.15)';"
                                onclick="document.querySelector('#back-home-btn-gradio').click();">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M19 12H5M12 19L5 12L12 5" 
                                      stroke="#374151" 
                                      stroke-width="2.5" 
                                      stroke-linecap="round" 
                                      stroke-linejoin="round"
                                      style="filter: drop-shadow(0 1px 2px rgba(0,0,0,0.1));"/>
                            </svg>
                        </button>
                    </div>
                """)
                
                # Button ẩn để trigger event Gradio
                back_btn_gradio = gr.Button("Back to Home", elem_id="back-home-btn-gradio", visible=False)

                # Tạo giao diện input
                input_components = create_lecture_input_interface()
                
                # Kết nối với output handler
                input_components['generate_btn'].click(
                    fn=lambda pptx, img, lang, voice_mode, cloned_voice, cloned_lang, preprocess, still, enh, batch, size, pose: generate_lecture_video_handler(
                        sad_talker, pptx, img, lang, voice_mode, cloned_voice, cloned_lang, preprocess, still, enh, batch, size, pose
                    ),
                    inputs=[
                        input_components['pptx_file'], 
                        input_components['source_image'], 
                        input_components['audio_language'],
                        input_components['voice_mode'],
                        input_components['cloned_voice_list'],
                        input_components['cloned_voice_language'],
                        input_components['preprocess_type'], 
                        input_components['is_still_mode'], 
                        input_components['enhancer'], 
                        input_components['batch_size'], 
                        input_components['size_of_image'], 
                        input_components['pose_style']
                    ],
                    outputs=[input_components['final_video'], input_components['status']]
                )
        
        # Kết nối events để chuyển đổi trang
        start_btn.click(
            fn=switch_to_lecture,
            outputs=[home_page, lecture_page]
        )
        
        # Kết nối button navigation
        nav_get_started_btn.click(
            fn=switch_to_lecture,
            outputs=[home_page, lecture_page]
        )
        
        back_btn_gradio.click(
            fn=switch_to_home,
            outputs=[home_page, lecture_page]
        )
    
    return sadtalker_interface

if __name__ == "__main__":
    demo = sadtalker_demo_with_home()
    demo.launch(
        server_name='127.0.0.1',
        server_port=7862,
        show_error=True,
        quiet=False,
        share=False,
        inbrowser=True
    )