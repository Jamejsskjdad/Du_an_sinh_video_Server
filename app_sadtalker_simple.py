# /home/dunghm/Du_an_sinh_video_main_goloi/app_sadtalker_simple.py
import os, sys
import gradio as gr
from src.gradio_demo import SadTalker

from home import create_home_tab, custom_home_css
from lecture_output import generate_lecture_video_handler

# MỚI: import Index + Editor
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
        # State chia sẻ giữa trang
        app_state = gr.State({})

        with gr.Column(elem_classes=["main-container"]):
            # HOME
            with gr.Column(visible=True, elem_classes=["home-page"]) as home_page:
                hidden_start = gr.Button("Start", visible=False)
                nav_get_started_btn = create_home_tab()

            # INDEX (nhập liệu)
            with gr.Column(visible=False, elem_classes=["index-page"]) as index_page:
                index_cmp = create_index_interface(app_state)
                # Nút điều hướng xuống cuối trang Index
                goto_editor_btn = gr.Button("➡️ Sang trang Editor để chỉnh sửa", variant="primary")

            # EDITOR (Editor + Generate)
            # EDITOR (Editor + Generate)
            with gr.Column(visible=False, elem_classes=["editor-page"]) as editor_page:
                editor_cmp = create_lecture_editor_interface(app_state)

                # ==== NỐI GENERATE ====
                # 1) ĐỊNH NGHĨA HÀM TRƯỚC
                def _generate_from_editor(
                    state, slides_text, pose, size, prep, still, enh, batch, rate
                ):
                    return generate_lecture_video_handler(
                        sad_talker,
                        # ---- các tham số lấy từ state do index.py đã lưu ----
                        state.get("pptx_file"),
                        state.get("source_image"),
                        (state.get("audio_language") or "vi"),
                        state.get("voice_mode"),
                        state.get("cloned_voice"),
                        (state.get("builtin_gender") or "Nữ"),
                        state.get("builtin_voice"),
                        (state.get("cloned_lang") or "vi"),
                        # ---- các tham số từ Editor (settings) ----
                        prep, still, enh, batch, size, pose, rate,
                        # ---- text đã chỉnh sửa ----
                        user_slides_text=slides_text
                    )

                # 2) SAU ĐÓ MỚI GẮN VỚI BUTTON
                editor_cmp["generate_btn"].click(
                    fn=_generate_from_editor,
                    inputs=[
                        app_state,
                        editor_cmp["slides_text"],
                        editor_cmp["pose_style"],
                        editor_cmp["size_of_image"],
                        editor_cmp["preprocess_type"],
                        editor_cmp["is_still_mode"],
                        editor_cmp["enhancer"],
                        editor_cmp["batch_size"],
                        editor_cmp["speech_rate"],
                    ],
                    outputs=[editor_cmp["final_video"], editor_cmp["info"]],
                )

                # NOTE: Nếu môi trường của bạn không cho phép trick outputs như trên,
                # thay bằng cách gọi generate_lecture_video_handler trong một wrapper trực tiếp:
                # editor_cmp["generate_btn"].click(
                #   fn=lambda s, st, pose, size, prep, still, enh, batch, rate:
                #       generate_lecture_video_handler(
                #           sad_talker,
                #           s.get("pptx_file"),
                #           s.get("source_image"),
                #           s.get("audio_language") or "vi",
                #           s.get("voice_mode"),
                #           s.get("cloned_voice"),
                #           s.get("builtin_gender") or "Nữ",
                #           s.get("builtin_voice"),
                #           s.get("cloned_lang") or "vi",
                #           prep, still, enh, batch, size, pose, rate,
                #           user_slides_text=st
                #       ),
                #   inputs=[app_state, editor_cmp["slides_text"], editor_cmp["pose_style"], editor_cmp["size_of_image"],
                #           editor_cmp["preprocess_type"], editor_cmp["is_still_mode"], editor_cmp["enhancer"],
                #           editor_cmp["batch_size"], editor_cmp["speech_rate"]],
                #   outputs=[editor_cmp["final_video"], editor_cmp["info"]],
                # )

        # ==== ĐIỀU HƯỚNG ====
        # từ Home → Index
        for btn in (hidden_start, nav_get_started_btn):
            btn.click(lambda: switch_to("index", None, None, None), outputs=[home_page, index_page, editor_page])

        # từ Index → Editor: dùng 2 nút (proceed_btn trong index + goto_editor_btn)
        index_cmp["proceed_btn"].click(lambda: switch_to("editor", None, None, None), outputs=[home_page, index_page, editor_page])
        goto_editor_btn.click(lambda: switch_to("editor", None, None, None), outputs=[home_page, index_page, editor_page])

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
