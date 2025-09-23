import os
import json
import gradio as gr
import tempfile
import time
import shutil
import gc
import torch
from datetime import datetime
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
from lecture_input import convert_text_to_audio, extract_slides_from_pptx
from src.utils.xtts_clone import XTTSInference

def cleanup_cuda_memory():
    """
    Clean up CUDA memory to prevent VRAM overflow
    """
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        print("🧹 CUDA memory cleaned up")
    except Exception as e:
        print(f"⚠️ CUDA cleanup warning: {str(e)}")

def check_system_memory():
    """
    Check available system memory
    """
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        print(f"💾 Available RAM: {available_gb:.1f}GB")
        return available_gb
    except ImportError:
        print("⚠️ psutil not available, cannot check memory")
        return 8.0  # Assume 8GB if we can't check

def get_audio_duration(audio_path):
    """
    Get duration of audio file in seconds
    """
    try:
        if audio_path and os.path.exists(audio_path):
            # Use AudioFileClip instead of VideoFileClip for audio files
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            audio_clip.close()
            return duration
        return 0
    except Exception as e:
        print(f"Error getting audio duration: {str(e)}")
        return 0

def create_slide_image_with_text(text, output_path, width=1280, height=720):
    """
    Create a slide image with text (placeholder for actual slide rendering)
    """
    try:
        # Create a white background image
        img = Image.new('RGB', (width, height), color='white')
        
        # For now, we'll create a simple text image
        # In a real implementation, you'd render the actual PowerPoint slide
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Draw text in the center
        text_lines = text.split('\n')
        y_position = height // 2 - (len(text_lines) * 50) // 2
        
        for line in text_lines:
            # Get text size
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position to center text
            x_position = (width - text_width) // 2
            
            # Draw text
            draw.text((x_position, y_position), line, fill='black', font=font)
            y_position += text_height + 20
        
        # Save image
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


def generate_video_for_text(sad_talker, source_image, text, language, voice_mode, cloned_voice_name, cloned_lang,
                            preprocess_type, is_still_mode, enhancer, batch_size, size_of_image, pose_style):
    """
    Generate video for a single text using SadTalker with CUDA memory management
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Clean up CUDA memory before each attempt
            cleanup_cuda_memory()
            
            # Verify source image exists
            if not source_image or not os.path.exists(source_image):
                print(f"Source image not found: {source_image}")
                return None
            
            # Convert text to audio
            audio_path = None
            if voice_mode == 'Giọng nhân bản' and cloned_voice_name:
                # Use XTTS with reference voice
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
                audio_path = convert_text_to_audio(text, language)
            if not audio_path:
                print("Failed to convert text to audio")
                return None
            
            print(f"Generating video with image: {source_image}")
            print(f"Image exists: {os.path.exists(source_image)}")
            print(f"Audio path: {audio_path}")
            print(f"Batch size: {batch_size} (attempt {retry_count + 1}/{max_retries})")
            
            # Generate video using the same method as the main interface
            video_path = sad_talker.test(
                source_image, audio_path, preprocess_type, is_still_mode, 
                enhancer, batch_size, size_of_image, pose_style
            )
            
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            if video_path and os.path.exists(video_path):
                print(f"✅ Video generated successfully: {video_path}")
                # Clean up CUDA memory after successful generation
                cleanup_cuda_memory()
                return video_path
            else:
                print(f"❌ Video generation failed or file not found: {video_path}")
                return None
                
        except RuntimeError as e:
            error_msg = str(e)
            if "CUDA out of memory" in error_msg:
                retry_count += 1
                print(f"❌ CUDA out of memory (attempt {retry_count}/{max_retries}): {error_msg}")
                
                if retry_count < max_retries:
                    # Reduce batch size and try again
                    batch_size = max(1, batch_size // 2)
                    print(f"🔄 Reducing batch size to {batch_size} and retrying...")
                    
                    # Clean up memory more aggressively
                    cleanup_cuda_memory()
                    time.sleep(2)  # Wait a bit for memory to be freed
                    continue
                else:
                    print(f"❌ Failed after {max_retries} attempts with CUDA memory error")
                    return None
            else:
                print(f"❌ Runtime error: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ Error generating video for text: {str(e)}")
            return None
    
    return None

def create_lecture_video(sad_talker, slides_data, source_image, language, voice_mode, cloned_voice_name, cloned_lang,
                         preprocess_type, is_still_mode, enhancer, batch_size, size_of_image, pose_style):
    """
    Create a lecture video combining slides and teacher video
    """
    try:
        if not slides_data:
            return None, "❌ Không có slide nào để xử lý!"
        
        # Create output directory
        output_dir = os.path.join("results", f"lecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Creating lecture video in: {output_dir}")
        
        # Check system memory before starting
        available_ram = check_system_memory()
        if available_ram < 2.0:
            print("⚠️ Warning: Low system memory detected. Video creation may fail.")
        
        # Copy source image to safe location
        safe_image_path = os.path.join(output_dir, "source_image.png")
        if not source_image or not os.path.exists(source_image):
            return None, "❌ Không tìm thấy ảnh nguồn!"
        
        shutil.copy2(source_image, safe_image_path)
        print(f"✅ Source image copied to safe location: {safe_image_path}")
        
        # Process each slide
        slide_clips = []
        total_duration = 0
        temp_video_files = []  # Track temporary video files for cleanup
        
        for i, slide_data in enumerate(slides_data):
            print(f"\n--- Processing slide {i+1}/{len(slides_data)} ---")
            
            # Verify source image exists before each slide processing
            if not os.path.exists(safe_image_path):
                print(f"⚠️ Source image lost, copying again...")
                if os.path.exists(source_image):
                    shutil.copy2(source_image, safe_image_path)
                    print(f"✅ Source image re-copied")
                else:
                    print(f"❌ Original source image also lost, stopping process")
                    break
            
            # Determine slide image: use original if available, otherwise generate from text
            slide_image_path = os.path.join(output_dir, f"slide_{i+1:02d}.png")
            original_image = slide_data.get('image_path')
            if original_image and os.path.exists(original_image):
                # Copy the original slide image into the output directory
                try:
                    shutil.copy2(original_image, slide_image_path)
                except Exception as e:
                    print(f"⚠️ Could not copy original slide image for slide {i+1}: {e}")
                    # Fallback: create a placeholder image with text
                    generated = create_slide_image_with_text(slide_data['text'], slide_image_path)
                    if not generated:
                        print(f"❌ Failed to create slide image for slide {i+1}")
                        continue
            else:
                # No original image available; create a placeholder image from text
                generated = create_slide_image_with_text(slide_data['text'], slide_image_path)
                if not generated:
                    print(f"❌ Failed to create slide image for slide {i+1}")
                    continue

            
            # Generate audio for slide text
            if voice_mode == 'Giọng nhân bản' and cloned_voice_name:
                ref_wav = _find_reference_wav_by_display_name(cloned_voice_name)
                if ref_wav:
                    try:
                        xtts = XTTSInference()
                        lang_code = cloned_lang if cloned_lang else language
                        audio_path = xtts.synthesize(slide_data['text'], lang_code, ref_wav)
                    except Exception as e:
                        print(f"XTTS synthesis failed for slide {i+1}, fallback to gTTS: {e}")
                        audio_path = convert_text_to_audio(slide_data['text'], language)
                else:
                    audio_path = convert_text_to_audio(slide_data['text'], language)
            else:
                audio_path = convert_text_to_audio(slide_data['text'], language)
            if not audio_path:
                print(f"❌ Failed to generate audio for slide {i+1} - tạo âm thanh im lặng thay thế")
                # Tạo file wav im lặng tối thiểu 3 giây để không bỏ qua slide
                try:
                    silent_seconds = 3
                    silent_wav = os.path.join(output_dir, f"silent_{i+1:02d}.wav")
                    from pydub import AudioSegment
                    AudioSegment.silent(duration=silent_seconds*1000).export(silent_wav, format="wav")
                    audio_path = silent_wav
                except Exception as e:
                    print(f"❌ Không tạo được âm thanh im lặng: {e}")
                    continue
            
            # Get audio duration
            audio_duration = get_audio_duration(audio_path)
            print(f"Audio duration for slide {i+1}: {audio_duration:.2f} seconds")
            
            # If audio duration is 0 or very short, set a minimum duration
            if audio_duration <= 0.1:
                audio_duration = 3.0  # Minimum 3 seconds per slide
                print(f"⚠️ Audio duration too short, setting to minimum: {audio_duration}s")
            
            # Generate teacher video with memory management
            print(f"🎬 Generating teacher video for slide {i+1}...")
            teacher_video_path = generate_video_for_text(
                sad_talker, safe_image_path, slide_data['text'], language, voice_mode, cloned_voice_name, cloned_lang,
                preprocess_type, is_still_mode, enhancer, batch_size, size_of_image, pose_style
            )
            
            # Clean up CUDA memory after each slide
            cleanup_cuda_memory()
            
            if not teacher_video_path or not os.path.exists(teacher_video_path):
                print(f"❌ Failed to generate teacher video for slide {i+1}")
                # Clean up audio
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                continue
            
            # Add small delay to ensure file is fully written
            time.sleep(1)
            
            # Load teacher video clip with error handling
            try:
                teacher_clip = VideoFileClip(teacher_video_path)
            except Exception as e:
                print(f"❌ Error loading teacher video for slide {i+1}: {str(e)}")
                # Clean up audio
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                continue
            
            # Create slide video clip (static image) and align its duration to teacher clip
            # để tránh trường hợp ảnh slide kết thúc sớm hơn video giáo viên
            composite_duration = max(audio_duration, getattr(teacher_clip, 'duration', audio_duration))
            slide_clip = ImageClip(slide_image_path, duration=composite_duration)
            
            # Resize teacher video to fit in bottom-right corner (picture-in-picture)
            # Calculate size: 25% of slide width, maintain aspect ratio
            slide_width, slide_height = slide_clip.size
            teacher_width = int(slide_width * 0.10)
            teacher_height = int(teacher_width * teacher_clip.h / teacher_clip.w)
            
            # Resize teacher video with memory optimization
            teacher_clip = teacher_clip.resize((teacher_width, teacher_height))
            
            # Đặt video người nói ở góc trên bên phải với lề 50 px
            teacher_x = slide_width - teacher_width - 50
            teacher_y = 50  # lề 50 px tính từ mép trên
            teacher_clip = teacher_clip.set_position((teacher_x, teacher_y))
            
            # Composite slide and teacher video
            composite_clip = CompositeVideoClip([slide_clip, teacher_clip])
            # Bảo đảm audio là của teacher clip
            if getattr(teacher_clip, 'audio', None) is not None:
                composite_clip = composite_clip.set_audio(teacher_clip.audio)
            
            # Add to clips list
            slide_clips.append(composite_clip)
            total_duration += audio_duration
            
            # Track video file for later cleanup
            temp_video_files.append(teacher_video_path)
            
            print(f"✅ Slide {i+1} processed: {audio_duration:.2f}s")
            
            # Clean up temporary files with delay
            time.sleep(0.5)  # Small delay before cleanup
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception as e:
                    print(f"⚠️ Could not remove audio file: {str(e)}")
            
            # Don't delete teacher video file immediately - it might still be in use
            # We'll clean it up later in the final cleanup
            print(f"📁 Teacher video saved for slide {i+1}: {os.path.basename(teacher_video_path)}")
            
            # Do NOT close clips here; they are still referenced by composite and final concatenation
            # Cleanup is deferred until after the final video is written
        
        if not slide_clips:
            return None, "❌ Không thể tạo video cho bất kỳ slide nào!"
        
        print(f"\n--- Creating final lecture video ---")
        print(f"Total slides: {len(slide_clips)}")
        print(f"Total duration: {total_duration:.2f} seconds")
        
        # Concatenate all slide clips with memory management
        final_video_path = os.path.join(output_dir, "lecture_final.mp4")
        
        print(f"Writing final video to: {final_video_path}")
        print(f"Processing {len(slide_clips)} clips with total duration: {total_duration:.2f}s")
        
        try:
            # Process clips in smaller batches to avoid memory issues
            if len(slide_clips) > 1:
                # Process clips in batches of 2 to reduce memory usage
                batch_size = 2
                processed_clips = []
                
                for i in range(0, len(slide_clips), batch_size):
                    batch_clips = slide_clips[i:i+batch_size]
                    print(f"Processing batch {i//batch_size + 1}/{(len(slide_clips)-1)//batch_size + 1}")
                    
                    if len(batch_clips) == 1:
                        processed_clips.append(batch_clips[0])
                    else:
                        batch_video = concatenate_videoclips(batch_clips, method="compose")
                        processed_clips.append(batch_video)
                    
                    # Do NOT close batch clips here; processed_clips may still reference them downstream
                    # Cleanup is deferred until after the final video is written
                    
                    # Force garbage collection
                    gc.collect()
                
                # Final concatenation
                if len(processed_clips) == 1:
                    final_video = processed_clips[0]
                else:
                    final_video = concatenate_videoclips(processed_clips, method="compose")
            else:
                final_video = slide_clips[0]
            
            # Write video with memory-efficient settings
            final_video.write_videofile(
                final_video_path, 
                codec='libx264', 
                audio_codec='aac', 
                verbose=False, 
                logger=None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset='medium',  # Balance between speed and compression
                ffmpeg_params=['-crf', '23']  # Good quality with reasonable file size
            )
            
        except MemoryError as e:
            print(f"❌ Memory error during video creation: {str(e)}")
            print("🔄 Trying with lower quality settings...")
            
            # Fallback: Create video with lower quality
            try:
                # Resize all clips to reduce memory usage
                resized_clips = []
                for clip in slide_clips:
                    # Resize to 1280x720 to reduce memory usage
                    resized_clip = clip.resize((1280, 720))
                    resized_clips.append(resized_clip)
                
                final_video = concatenate_videoclips(resized_clips, method="compose")
                final_video.write_videofile(
                    final_video_path, 
                    codec='libx264', 
                    audio_codec='aac', 
                    verbose=False, 
                    logger=None,
                    preset='fast',  # Faster encoding
                    ffmpeg_params=['-crf', '28']  # Lower quality but smaller file
                )
                print("✅ Video created with reduced quality due to memory constraints")
                
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {str(fallback_error)}")
                return None, f"❌ Không thể tạo video do thiếu RAM. Thử giảm số lượng slide hoặc độ phân giải."
        
        # Clean up clips
        for clip in slide_clips:
            try:
                clip.close()
            except Exception as e:
                print(f"⚠️ Could not close clip: {str(e)}")
        try:
            final_video.close()
        except Exception as e:
            print(f"⚠️ Could not close final video: {str(e)}")
        
        # Add delay before cleanup
        time.sleep(1)
        
        # Clean up temporary slide images
        for i in range(len(slides_data)):
            slide_image_path = os.path.join(output_dir, f"slide_{i+1:02d}.png")
            if os.path.exists(slide_image_path):
                try:
                    os.remove(slide_image_path)
                except Exception as e:
                    print(f"⚠️ Could not remove slide image {i+1}: {str(e)}")
        
        # Clean up source image copy
        if os.path.exists(safe_image_path):
            try:
                os.remove(safe_image_path)
            except Exception as e:
                print(f"⚠️ Could not remove source image copy: {str(e)}")
        
        # Clean up temporary video files
        print("🧹 Cleaning up temporary video files...")
        for video_file in temp_video_files:
            if os.path.exists(video_file):
                try:
                    os.remove(video_file)
                    print(f"  ✅ Deleted: {os.path.basename(video_file)}")
                except Exception as e:
                    print(f"  ❌ Could not delete {os.path.basename(video_file)}: {str(e)}")
        
        # Also clean up temporary SadTalker directories
        print("🗂️ Cleaning up temporary SadTalker directories...")
        temp_dirs_deleted = 0
        results_dir = "results"
        if os.path.exists(results_dir):
            for item in os.listdir(results_dir):
                item_path = os.path.join(results_dir, item)
                # Check if it's a directory with UUID-like name (temporary SadTalker dirs)
                if os.path.isdir(item_path) and len(item) == 36 and '-' in item:
                    try:
                        shutil.rmtree(item_path)
                        print(f"  ✅ Deleted temp directory: {item}")
                        temp_dirs_deleted += 1
                    except Exception as e:
                        print(f"  ❌ Failed to delete temp directory {item}: {str(e)}")
        
        print(f"🗂️ Cleanup completed: {temp_dirs_deleted} temporary directories deleted")
        
        # Final CUDA memory cleanup
        cleanup_cuda_memory()
        
        print(f"✅ Lecture video created successfully: {final_video_path}")
        
        return final_video_path, f"✅ Hoàn thành! Đã tạo video bài giảng với {len(slides_data)} slide, tổng thời gian: {total_duration:.1f}s"
        
    except Exception as e:
        print(f"Error in create_lecture_video: {str(e)}")
        return None, f"❌ Lỗi tạo video bài giảng: {str(e)}"

def generate_lecture_video_handler(sad_talker, pptx, img, lang, voice_mode, cloned_voice, cloned_lang, preprocess, still, enh, batch, size, pose):
    """Handler function for generating lecture video"""
    if not pptx or not img:
        return None, "❌ Vui lòng chọn file PowerPoint và ảnh giáo viên!"
    
    slides_data = extract_slides_from_pptx(pptx)
    if not slides_data:
        return None, "❌ Không thể trích xuất nội dung từ PowerPoint!"
    
    return create_lecture_video(
        sad_talker, slides_data, img, lang, voice_mode, cloned_voice, cloned_lang, preprocess, still, enh, batch, size, pose
    )
