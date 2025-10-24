# /home/dunghm/Du_an_sinh_video_main_goloi/app_sadtalker_simple.py

import os, sys
import gradio as gr
from src.gradio_demo import SadTalker

# thêm import
from home import create_home_tab, custom_home_css, create_global_navbar
from lecture_output import generate_lecture_video_handler

from index import create_index_interface
from lecture_input import create_lecture_editor_interface

def switch_to(target, home, index, editor):
    vis = {
        "home": (True, False, False),
        "index": (False, True, False),
        "editor": (False, False, True),
    }[target]
    return [gr.update(visible=vis[0]), gr.update(visible=vis[1]), gr.update(visible=vis[2])]

def sadtalker_demo_with_home(checkpoint_path='checkpoints', config_path='src/config', warpfn=None):
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
    sad_talker = SadTalker(checkpoint_path, config_path, lazy_load=True)

    with gr.Blocks(analytics_enabled=False, title="SadTalker", css=custom_home_css()) as ui:
        app_state = gr.State({})

        # Navbar chung
        nav = create_global_navbar()

        with gr.Column(elem_classes=["main-container"]):
            # HOME (không navbar ở trong)
            with gr.Column(visible=True, elem_classes=["home-page"]) as home_page:
                nav_get_started_btn = create_home_tab()

            # INDEX
            with gr.Column(visible=False, elem_classes=["index-page"]) as index_page:
                index_cmp = create_index_interface(app_state)

            # EDITOR
            with gr.Column(visible=False, elem_classes=["editor-page"]) as editor_page:
                editor_cmp = create_lecture_editor_interface(app_state)

                def _generate_from_editor(state, slides_text, pose, size, prep, still, enh, batch, rate):
                    return generate_lecture_video_handler(
                        sad_talker,
                        state.get("pptx_file"),
                        state.get("source_image"),
                        (state.get("audio_language") or "vi"),
                        state.get("voice_mode"),
                        state.get("cloned_voice"),
                        (state.get("builtin_gender") or "Nữ"),
                        state.get("builtin_voice"),
                        (state.get("cloned_lang") or "vi"),
                        prep, still, enh, batch, size, pose, rate,
                        user_slides_text=slides_text
                    )

                editor_cmp["generate_btn"].click(
                    fn=_generate_from_editor,
                    inputs=[app_state, editor_cmp["slides_text"], editor_cmp["pose_style"],
                            editor_cmp["size_of_image"], editor_cmp["preprocess_type"],
                            editor_cmp["is_still_mode"], editor_cmp["enhancer"],
                            editor_cmp["batch_size"], editor_cmp["speech_rate"]],
                    outputs=[editor_cmp["final_video"], editor_cmp["info"]],
                )

        # ĐIỀU HƯỚNG NAVBAR
        nav["nav_home_btn"].click(  lambda: switch_to("home",  None, None, None), outputs=[home_page, index_page, editor_page])
        nav["nav_index_btn"].click( lambda: switch_to("index", None, None, None), outputs=[home_page, index_page, editor_page])
        nav["nav_submit_btn"].click(lambda: switch_to("editor",None, None, None), outputs=[home_page, index_page, editor_page])

        # Nút “Bắt đầu” trong trang Home → Index
        nav_get_started_btn.click(lambda: switch_to("index", None, None, None), outputs=[home_page, index_page, editor_page])

        # Nếu Index có nút “Tiếp tục” → Editor
        if "proceed_btn" in index_cmp:
            index_cmp["proceed_btn"].click(lambda: switch_to("editor", None, None, None),
                                           outputs=[home_page, index_page, editor_page])

    return ui

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
