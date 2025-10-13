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
                # Nút quay lại trang chủ - nút mũi tên cong đẹp mắt
                back_btn = gr.HTML("""
                    <style>
                    .back-btn {
                        position: fixed;
                        top: 10px;           /* cao hơn */
                        left: 20px;
                        z-index: 1000;
                        background: none;    /* không viền, không nền */
                        border: none;
                        cursor: pointer;
                        padding: 8px;
                        opacity: 0.6;        /* mờ mặc định */
                        transition: opacity 0.25s ease, transform 0.2s ease;
                    }

                    .back-btn:hover {
                        opacity: 1;          /* sáng rõ khi hover */
                        transform: translateY(-1px);
                    }

                    .back-btn svg {
                        width: 28px;
                        height: 28px;
                    }
                    </style>

                    <button class="back-btn" id="back-home-btn"
                            aria-label="Quay lại"
                            onclick="document.querySelector('#back-home-btn-gradio').click();">
                    <svg viewBox="0 0 24 24" fill="none"
                        xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 12H5M12 19L5 12L12 5"
                            stroke="#E5E7EB" stroke-width="2.5"
                            stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    </button>
                    """)

                
                # Button ẩn để trigger event Gradio
                back_btn_gradio = gr.Button("Back to Home", elem_id="back-home-btn-gradio", visible=False)

                # Tạo giao diện input
                input_components = create_lecture_input_interface()
                
                # Kết nối với output handler
                input_components['generate_btn'].click(
                    fn=lambda pptx, img, lang, voice_mode, cloned_voice, gender, builtin_voice,
                            cloned_lang, preprocess, still, enh, batch, size, pose:
                        generate_lecture_video_handler(
                            sad_talker, pptx, img, lang, voice_mode,
                            cloned_voice, gender, builtin_voice, cloned_lang,
                            preprocess, still, enh, batch, size, pose
                        ),
                    inputs=[
                        input_components['pptx_file'],             
                        input_components['source_image'],          
                        input_components['audio_language'],        
                        input_components['voice_mode'],            
                        input_components['cloned_voice_list'],     
                        input_components['builtin_gender'],        
                        input_components['builtin_voice'],         
                        input_components['cloned_voice_language'], 
                        input_components['preprocess_type'],       
                        input_components['is_still_mode'],         
                        input_components['enhancer'],              
                        input_components['batch_size'],            
                        input_components['size_of_image'],         
                        input_components['pose_style']             
                    ],
                    outputs=[input_components['final_video']]
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