import gradio as gr

def create_home_tab():
    """Tạo tab Home với Gradio + HTML/CSS/JS thuần (có hiệu ứng hover + tilt 3D)"""
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SadTalker - Tạo Video Nói Chuyện Từ Ảnh</title>
        <style>
            :root{
              --violet:#8B5CF6; --blue:#3B82F6;
              --radius:16px;
              --shadow-sm:0 6px 16px rgba(17,24,39,.10);
              --shadow-md:0 12px 28px rgba(17,24,39,.14);
              --glow:0 0 0 rgba(139,92,246,0);
              --glow-hover:0 8px 28px rgba(139,92,246,.35), 0 2px 10px rgba(59,130,246,.25);
              --transition:150ms cubic-bezier(.2,.6,.2,1);
            }

            /* reduce-motion */
            @media (prefers-reduced-motion: reduce){
              * { animation: none !important; transition: none !important; }
            }

            /* -------- Buttons -------- */
            .btnfx{
              position: relative; border-radius: 12px; transform: translateZ(0);
              transition: transform var(--transition), box-shadow var(--transition), filter var(--transition), background-position var(--transition);
              box-shadow: var(--shadow-sm);
              cursor: pointer;
            }
            .btnfx:hover, .btnfx:focus-visible{
              transform: translateY(-2px) scale(1.02);
              box-shadow: var(--glow-hover);
              filter: saturate(1.05);
              outline: none;
            }
                         /* gradient shift */
             .btnfx[data-variant="gradient"]{
               background: linear-gradient(135deg,var(--violet),var(--blue));
               color:#fff;
             }

                         /* viền/gradient chạy viền */
             .btnfx[data-border="flow"] {
                 --_b:2px;
                 background:
                     linear-gradient(transparent,transparent) padding-box,
                     conic-gradient(from 0turn, var(--violet), var(--blue), var(--violet)) border-box;
                 border: var(--_b) solid transparent;
                 }
                 /* Giữ màu hiện tại của phần tử, không override color */
                 .btnfx[data-border="flow"]:hover{
                 background:
                     linear-gradient(#fff,#fff) padding-box,
                     conic-gradient(from 0turn, var(--violet), var(--blue), var(--violet)) border-box;
                 }

             /* Button đặc biệt - không đổi background khi hover */
             .btnfx.btn-special {
                 background: linear-gradient(135deg,var(--violet),var(--blue)) !important;
                 color: #fff !important;
                 border: none !important;
             }
             .btnfx.btn-special:hover {
                 background: linear-gradient(135deg,var(--violet),var(--blue)) !important;
                 color: #fff !important;
             }


            /* -------- Navbar links -------- */
            .navfx{
              position: relative; padding-bottom: 2px; transition: color var(--transition);
              text-decoration: none; color: #111827;
            }
            .navfx::after{
              content:""; position:absolute; left:0; bottom:-4px; height:2px; width:0;
              background: linear-gradient(90deg,var(--violet),var(--blue));
              transition: width var(--transition);
              border-radius: 2px;
            }
            .navfx:hover{ color:#111827; }
            .navfx:hover::after{ width:100%; }

            /* === Feature cards - CSS riêng biệt === */
            .feature-card{
            border-radius: var(--radius);
            background: #fff;
            text-align: center;
            border: 1px solid #e5e7eb;         /* viền xám mặc định */
            box-shadow: none;                   /* không có đổ bóng khi chưa hover */
            transition:
                transform var(--transition),
                filter var(--transition),
                box-shadow var(--transition),
                border-color var(--transition);
            will-change: transform;
            box-sizing: border-box;             /* để viền không làm nảy layout */
            }

            /* Hiệu ứng hover cho feature cards */
            .feature-card:hover{
            border-color: #3B82F6;              /* viền xanh rõ ràng */
            box-shadow: 0 0 0 1px #3B82F6 inset, var(--shadow-md);  /* viền xanh bên trong mỏng hơn + bóng */
            transform: translateY(-6px) scale(1.02);
            filter: saturate(1.03);
            }

            /* icon nhích nhẹ khi hover */
            .feature-card .card-icon{ transition: transform var(--transition); }
            .feature-card:hover .card-icon{ transform: translateY(-3px); }

            /* === Card chung cho các card khác === */
            .cardfx{
            border-radius: var(--radius);
            background: #fff;
            text-align: center;
            border: 1px solid #e5e7eb;
            box-shadow: none;                   /* không có đổ bóng khi chưa hover */
            transition:
                transform var(--transition),
                filter var(--transition),
                box-shadow var(--transition),
                border-color var(--transition);
            will-change: transform;
            box-sizing: border-box;
            }

            .cardfx:hover{
            border-color: rgba(139,92,246,.35);  /* viền tím nhẹ cho card khác */
            box-shadow: var(--shadow-md);        /* chỉ có đổ bóng khi hover */
            transform: translateY(-6px) scale(1.02);
            filter: saturate(1.03);
            }

            .cardfx .card-icon{ transition: transform var(--transition); }
            .cardfx:hover .card-icon{ transform: translateY(-3px); }
            /* ---- Features grid: ép các item cao bằng nhau ---- */
            .features-grid{
            /* mỗi hàng lấy chiều cao bằng nhau */
            grid-auto-rows: 1fr;
            align-items: stretch;
            }

            /* cho wrapper tilt và thẻ bên trong “kéo giãn” theo ô lưới */
            .features-grid .tilt,
            .features-grid .tilt-inner,
            .features-grid .feature-card{
            height: 100%;
            }

            /* bên trong thẻ dùng flex để nội dung xếp dọc gọn gàng */
            .features-grid .feature-card{
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 320px;
            }



            /* -------- Showcase video tiles -------- */
            .showcase-card{
              position: relative; overflow:hidden; border-radius: var(--radius);
              transition: transform var(--transition), box-shadow var(--transition), filter var(--transition);
              box-shadow: none;                  /* không có đổ bóng khi chưa hover */
              transform: translateZ(0);
            }
            .showcase-card:hover{ transform: translateY(-6px) scale(1.02); box-shadow: var(--shadow-md); }
            .showcase-card video{
              transition: transform var(--transition), filter var(--transition); will-change: transform;
              width: 100%; height: 250px; object-fit: cover;
            }
            .showcase-card:hover video{ transform: scale(1.06); filter: saturate(1.05) contrast(1.02); }
            .showcase-card::after{
              content:""; position:absolute; inset:0; pointer-events:none; border-radius: inherit;
              box-shadow: var(--glow); transition: box-shadow var(--transition);
            }
            .showcase-card:hover::after{ box-shadow: var(--glow-hover); }

            /* -------- Steps (How it works) -------- */
            .stepfx{
              border-radius: var(--radius);
              /* Loại bỏ hiệu ứng hover - chỉ giữ lại border-radius */
            }
            /* .stepfx:hover{ transform: translateY(-4px); box-shadow: var(--shadow-sm); } */

            /* -------- Tilt/parallax 3D -------- */
            .tilt{ perspective: 800px; transform-style: preserve-3d; }
            .tilt-inner{ transition: transform var(--transition); transform-style: preserve-3d; }
            .tilt:hover .tilt-inner{ transform: rotateX(2deg) rotateY(-2deg); }

            /* -------- Mobile fallback (giữ hiệu ứng qua :active) -------- */
            @media (hover: none){
              .btnfx:active{ transform: scale(.98); }
              .cardfx:active, .showcase-card:active{ transform: scale(.99); }
            }

            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-10px); }
                60% { transform: translateY(-5px); }
            }

            /* Responsive (giữ như cũ) */
            @media (max-width: 768px) {
                .hero-content { grid-template-columns: 1fr !important; text-align: center; }
                .hero-text h1 { font-size: 42px !important; }
                .about-content { grid-template-columns: 1fr !important; }
                .step { grid-template-columns: 1fr !important; }
                .step:nth-child(even) .step-content,
                .step:nth-child(even) .step-visual { order: unset !important; }
                .features-grid { grid-template-columns: 1fr !important; }
                .showcase-grid { grid-template-columns: 1fr !important; }
                .features-list { flex-direction: column !important; gap: 16px !important; }
                .nav-links { display: none !important; }
                .cta-buttons { flex-direction: column !important; align-items: center !important; }
            }
        </style>
    </head>

    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #111827; overflow-x: hidden;">
        <!-- Navbar -->
        <nav style="position: fixed; top: 0; left: 0; right: 0; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(0, 0, 0, 0.1); z-index: 1000; transition: all 0.3s ease;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 0;">
                    <div style="font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #8B5CF6, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">SadTalker</div>
                    <ul style="display: flex; gap: 32px; list-style: none; margin: 0; padding: 0;">
                        <li><a class="navfx" href="#features" onclick="(d=>d&&d.scrollIntoView({behavior:'smooth',block:'start'}))(document.querySelector('#features'))">Tính Năng</a></li>
                        <li><a class="navfx" href="#howitworks" onclick="(d=>d&&d.scrollIntoView({behavior:'smooth',block:'start'}))(document.querySelector('#howitworks'))">Cách Hoạt Động</a></li>
                        <li><a class="navfx" href="#showcase" onclick="(d=>d&&d.scrollIntoView({behavior:'smooth',block:'start'}))(document.querySelector('#showcase'))">Trình Diễn</a></li>
                        <li><a class="navfx" href="#about" onclick="(d=>d&&d.scrollIntoView({behavior:'smooth',block:'start'}))(document.querySelector('#about'))">Giới Thiệu</a></li>
                    </ul>
                                         <!-- Nút Bắt Đầu: class đặc biệt -->
                     <button class="btnfx btn-special"
                         style="padding: 12px 24px; border: none; border-radius: 12px; font-weight: 600;"
                         onclick="(function(){var b=document.querySelector('#nav_get_started_btn'); if(b){ b.click(); }})();">
                         Bắt Đầu
                     </button>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <section style="min-height: 100vh; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e40af 100%); position: relative; display: flex; align-items: center; overflow: hidden;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px; width: 100%;">
                <div class="hero-content" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; position: relative; z-index: 2;">
                    <div class="hero-text">
                        <h1 style="font-size: 56px; font-weight: bold; line-height: 1.1; margin-bottom: 24px; color: white;">
                            <span style="background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Tạo Video Nói Chuyện</span><br>
                            Từ Ảnh Với AI
                        </h1>
                        <p style="font-size: 20px; color: rgba(255, 255, 255, 0.8); margin-bottom: 32px; line-height: 1.6;">
                            Chuyển đổi bất kỳ ảnh chân dung nào thành video nói chuyện thực tế bằng công nghệ AI tiên tiến. Không cần kỹ năng kỹ thuật.
                        </p>
                                                 <!-- Nút Bắt Đầu Tạo Video: class đặc biệt -->
                         <button class="btnfx btn-special"
                             style="padding: 16px 32px; border: none; border-radius: 12px; font-size: 18px; font-weight: 600; box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);"
                             onclick="(function(){var b=document.querySelector('#nav_get_started_btn'); if(b){ b.click(); }})();">
                             Bắt Đầu Tạo Video
                         </button>
                    </div>
                    <div style="position: relative;">
                        <div style="background: rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 8px; backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);">
                            <video style="width: 100%; border-radius: 12px; display: block;" autoplay muted loop>
                                <source src="https://assets.mixkit.co/videos/preview/mixkit-woman-talking-on-a-video-call-3980-large.mp4" type="video/mp4">
                            </video>
                        </div>
                    </div>
                </div>
                <a href="#about" style="position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); color: white; text-align: center; cursor: pointer; text-decoration:none;"
                   onclick="(d=>d&&d.scrollIntoView({behavior:'smooth',block:'start'}))(document.querySelector('#about'))">
                    <div>Cuộn Xuống</div>
                    <div style="font-size: 24px; animation: bounce 2s infinite;">↓</div>
                </a>
            </div>
        </section>

        <!-- About Section -->
        <section id="about" style="padding: 120px 0; background: #f8fafc;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <div class="about-content" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center;">
                    <div style="position: relative;">
                        <video style="width: 100%; border-radius: 16px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);" autoplay muted loop>
                            <source src="https://assets.mixkit.co/videos/preview/mixkit-man-talking-on-a-video-call-3981-large.mp4" type="video/mp4">
                        </video>
                    </div>
                    <div>
                        <h2 style="font-size: 42px; font-weight: bold; margin-bottom: 24px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Công Nghệ AI Tiên Tiến</h2>
                        <p style="font-size: 18px; color: #6B7280; margin-bottom: 24px; line-height: 1.7;">
                            Trí tuệ nhân tạo tiên tiến của chúng tôi chuyển đổi ảnh tĩnh thành video nói chuyện sống động với độ chính xác đáng kinh ngạc và biểu cảm tự nhiên.
                        </p>
                        <p style="font-size: 18px; color: #6B7280; margin-bottom: 24px; line-height: 1.7;">
                            Sử dụng thuật toán học sâu được huấn luyện trên hàng triệu biểu cảm khuôn mặt và mẫu giọng nói, SadTalker tạo ra video gần như không thể phân biệt với bản ghi thực.
                        </p>
                        <div class="features-list" style="display: flex; gap: 32px; margin-top: 32px;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="width: 12px; height: 12px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%;"></div>
                                <span style="font-weight: 600; color: #111827;">Học Sâu</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="width: 12px; height: 12px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%;"></div>
                                <span style="font-weight: 600; color: #111827;">AI Tạo Ra</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section id="features" style="padding: 120px 0; background: white;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <div style="text-align: center; margin-bottom: 80px;">
                    <h2 style="font-size: 42px; font-weight: bold; margin-bottom: 16px; color: #111827;">Tính Năng Mạnh Mẽ</h2>
                    <p style="font-size: 20px; color: #6B7280; max-width: 600px; margin: 0 auto;">Tất cả những gì bạn cần để tạo video nói chuyện tuyệt vời từ ảnh</p>
                </div>
                <div class="features-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 32px;">
                                         <!-- Card 1 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">🎬</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Ảnh Thành Video</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Chuyển đổi bất kỳ ảnh chân dung nào thành video nói chuyện thực tế với đồng bộ môi và biểu cảm khuôn mặt tự nhiên.</p>
                       </div>
                     </div>
                     <!-- Card 2 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">🎵</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Hỗ Trợ Âm Thanh</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Tải lên file âm thanh của bạn hoặc sử dụng tính năng chuyển văn bản thành giọng nói để làm cho ảnh của bạn nói chuyện với đồng bộ hoàn hảo.</p>
                       </div>
                     </div>
                     <!-- Card 3 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">🎨</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Tùy Chỉnh</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Điều chỉnh biểu cảm, thời gian và tùy chỉnh đầu ra để phù hợp với tầm nhìn sáng tạo của bạn.</p>
                       </div>
                     </div>
                     <!-- Card 4 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">⚡</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Xử Lý Nhanh</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Tạo video nói chuyện chất lượng cao trong vài phút, không phải hàng giờ. AI được tối ưu hóa của chúng tôi đảm bảo kết quả nhanh chóng.</p>
                       </div>
                     </div>
                     <!-- Card 5 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">🔒</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Bảo Mật</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Ảnh và video của bạn được xử lý an toàn và không bao giờ được lưu trữ trên máy chủ của chúng tôi sau khi xử lý.</p>
                       </div>
                     </div>
                     <!-- Card 6 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">📱</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Nhiều Định Dạng</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Xuất ra nhiều định dạng và độ phân giải phù hợp cho mạng xã hội, thuyết trình hoặc sử dụng cá nhân.</p>
                       </div>
                     </div>
                </div>
            </div>
        </section>

        <!-- How It Works -->
        <section id="howitworks" style="padding: 120px 0; background: #f8fafc;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <div style="text-align: center; margin-bottom: 80px;">
                    <h2 style="font-size: 42px; font-weight: bold; margin-bottom: 16px; color: #111827;">Cách Hoạt Động</h2>
                    <p style="font-size: 20px; color: #6B7280; max-width: 600px; margin: 0 auto;">Tạo video nói chuyện chỉ trong 5 bước đơn giản</p>
                </div>
                <div style="max-width: 800px; margin: 0 auto;">
                    <!-- Step 1 -->
                    <div class="step" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 80px;">
                        <div class="stepfx">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; margin-bottom: 24px;">1</div>
                            <h3 style="font-size: 28px; font-weight: bold; margin-bottom: 16px; color: #111827;">Tải Lên Ảnh</h3>
                            <p style="font-size: 18px; color: #6B7280; line-height: 1.6;">Chọn ảnh chân dung rõ ràng với khuôn mặt hiển thị rõ. AI của chúng tôi hoạt động tốt nhất với ảnh nhìn thẳng.</p>
                        </div>
                        <div class="stepfx" style="background: white; border-radius: 16px; padding: 32px; text-align: center; border: 1px solid #e5e7eb; font-size: 48px;">📸</div>
                    </div>
                    <!-- Step 2 -->
                    <div class="step" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 80px;">
                        <div class="stepfx" style="order: 2;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; margin-bottom: 24px;">2</div>
                            <h3 style="font-size: 28px; font-weight: bold; margin-bottom: 16px; color: #111827;">Thêm File PowerPoint</h3>
                            <p style="font-size: 18px; color: #6B7280; line-height: 1.6;">Tải lên file PowerPoint để trích xuất nội dung và tạo video nói chuyện từ các slide của bạn.</p>
                        </div>
                        <div class="stepfx" style="background: white; border-radius: 16px; padding: 32px; text-align: center; border: 1px solid #e5e7eb; font-size: 48px; order: 1;">📊</div>
                    </div>
                    <!-- Step 3 -->
                    <div class="step" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 80px;">
                        <div class="stepfx">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; margin-bottom: 24px;">3</div>
                            <h3 style="font-size: 28px; font-weight: bold; margin-bottom: 16px; color: #111827;">Xử Lý AI</h3>
                            <p style="font-size: 18px; color: #6B7280; line-height: 1.6;">AI tiên tiến của chúng tôi phân tích ảnh và âm thanh để tạo chuyển động khuôn mặt tự nhiên và đồng bộ môi.</p>
                        </div>
                        <div class="stepfx" style="background: white; border-radius: 16px; padding: 32px; text-align: center; border: 1px solid #e5e7eb; font-size: 48px;">🤖</div>
                    </div>
                    <!-- Step 4 -->
                    <div class="step" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 80px;">
                        <div class="stepfx" style="order: 2;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; margin-bottom: 24px;">4</div>
                            <h3 style="font-size: 28px; font-weight: bold; margin-bottom: 16px; color: #111827;">Xem Trước & Chỉnh Sửa</h3>
                            <p style="font-size: 18px; color: #6B7280; line-height: 1.6;">Xem lại video nói chuyện của bạn và điều chỉnh thời gian, biểu cảm hoặc các tham số khác theo nhu cầu.</p>
                        </div>
                        <div class="stepfx" style="background: white; border-radius: 16px; padding: 32px; text-align: center; border: 1px solid #e5e7eb; font-size: 48px; order: 1;">👁️</div>
                    </div>
                    <!-- Step 5 -->
                    <div class="step" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 80px;">
                        <div class="stepfx">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; margin-bottom: 24px;">5</div>
                            <h3 style="font-size: 28px; font-weight: bold; margin-bottom: 16px; color: #111827;">Tải Xuống</h3>
                            <p style="font-size: 18px; color: #6B7280; line-height: 1.6;">Xuất video nói chuyện hoàn thành theo định dạng và độ phân giải ưa thích của bạn, sẵn sàng chia sẻ hoặc sử dụng.</p>
                        </div>
                        <div class="stepfx" style="background: white; border-radius: 16px; padding: 32px; text-align: center; border: 1px solid #e5e7eb; font-size: 48px;">⬇️</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Showcase -->
        <section id="showcase" style="padding: 120px 0; background: white;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <div style="text-align: center; margin-bottom: 80px;">
                    <h2 style="font-size: 42px; font-weight: bold; margin-bottom: 16px; color: #111827;">Trình Diễn Video</h2>
                    <p style="font-size: 20px; color: #6B7280; max-width: 600px; margin: 0 auto;">Xem những gì có thể làm được với công nghệ AI SadTalker</p>
                </div>
                <div class="showcase-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 32px; margin-bottom: 64px;">
                    <!-- Tile 1 -->
                    <div class="tilt">
                      <div class="tilt-inner showcase-card" style="background:#000;">
                        <video muted>
                            <source src="https://assets.mixkit.co/videos/preview/mixkit-woman-talking-on-a-video-call-3980-large.mp4" type="video/mp4">
                        </video>
                        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(transparent 60%, rgba(0,0,0,0.8)); display: flex; align-items: center; justify-content: center; opacity: 1; transition: opacity 0.3s ease;">
                            <div style="width: 64px; height: 64px; background: rgba(255, 255, 255, 0.9); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #111827;">▶</div>
                        </div>
                        <div style="position: absolute; bottom: 16px; left: 16px; color: white; font-weight: 600;">Hoạt Hình Chân Dung</div>
                      </div>
                    </div>
                    <!-- Tile 2 -->
                    <div class="tilt">
                      <div class="tilt-inner showcase-card" style="background:#000;">
                        <video muted>
                            <source src="https://assets.mixkit.co/videos/preview/mixkit-man-talking-on-a-video-call-3981-large.mp4" type="video/mp4">
                        </video>
                        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(transparent 60%, rgba(0,0,0,0.8)); display: flex; align-items: center; justify-content: center; opacity: 1; transition: opacity 0.3s ease;">
                            <div style="width: 64px; height: 64px; background: rgba(255, 255, 255, 0.9); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #111827;">▶</div>
                        </div>
                        <div style="position: absolute; bottom: 16px; left: 16px; color: white; font-weight: 600;">Tổng Hợp Giọng Nói</div>
                      </div>
                    </div>
                    <!-- Tile 3 -->
                    <div class="tilt">
                      <div class="tilt-inner showcase-card" style="background:#000;">
                        <video muted>
                            <source src="https://assets.mixkit.co/videos/preview/mixkit-woman-talking-on-a-video-call-3980-large.mp4" type="video/mp4">
                        </video>
                        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(transparent 60%, rgba(0,0,0,0.8)); display: flex; align-items: center; justify-content: center; opacity: 1; transition: opacity 0.3s ease;">
                            <div style="width: 64px; height: 64px; background: rgba(255, 255, 255, 0.9); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #111827;">▶</div>
                        </div>
                        <div style="position: absolute; bottom: 16px; left: 16px; color: white; font-weight: 600;">Biểu Cảm Thực Tế</div>
                      </div>
                    </div>
                </div>
                <div style="text-align: center;">
                    <!-- Nút Thử Ngay: gradient nền -->
                    <button class="btnfx" data-variant="gradient"
                        style="padding: 16px 32px; border: none; border-radius: 12px; font-size: 18px; font-weight: 600;"
                        onclick="(function(){var b=document.querySelector('#nav_get_started_btn'); if(b){ b.click(); }})();">
                        Thử Ngay
                    </button>
                </div>
            </div>
        </section>

        <!-- CTA Section -->
        <section id="cta" style="padding: 120px 0; background: linear-gradient(135deg, #8B5CF6, #3B82F6); text-align: center; color: white;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <h2 style="font-size: 48px; font-weight: bold; margin-bottom: 24px;">Sẵn Sàng Tạo Video Nói Chuyện Tuyệt Vời?</h2>
                <p style="font-size: 20px; margin-bottom: 48px; opacity: 0.9; max-width: 600px; margin-left: auto; margin-right: auto;">
                    Tham gia cùng hàng nghìn người sáng tạo đã sử dụng SadTalker để mang ảnh của họ trở nên sống động với công nghệ AI.
                </p>
                <div class="cta-buttons" style="display: flex; gap: 24px; justify-content: center; flex-wrap: wrap;">
                    <!-- Nút gradient -->
                    <button class="btnfx" data-variant="gradient"
                        style="padding: 16px 32px; border: none; border-radius: 12px; font-size: 18px; font-weight: 600;"
                        onclick="(function(){var b=document.querySelector('#nav_get_started_btn'); if(b){ b.click(); }})();">
                        Bắt Đầu Tạo Ngay
                    </button>
                    <button class="btnfx" data-border="flow"
                        style="background: transparent; padding: 16px 32px; border-radius: 12px; font-size: 18px; font-weight: 600;"
                        onclick="(d=>d&&d.scrollIntoView({behavior:'smooth',block:'start'}))(document.querySelector('#about'))">
                        Tìm Hiểu Thêm
                    </button>
                </div>
            </div>
        </section>
    </body>
    </html>
    """
    with gr.Row():
        html_component = gr.HTML(html_content)

    # Nút ẩn để bắt sự kiện điều hướng
    nav_button = gr.Button("Bắt Đầu", elem_id="nav_get_started_btn", visible=False)
    return nav_button


def custom_home_css():
    """Trả về CSS tùy chỉnh cho Gradio"""
    return """
    /* Ẩn các button kỹ thuật của Gradio nhưng vẫn có thể tương tác */
    #nav_get_started_btn {
        position: absolute !important;
        left: -9999px !important;
        opacity: 0 !important;
        pointer-events: auto !important;
        z-index: -1 !important;
    }

    /* Đảm bảo HTML component chiếm toàn bộ không gian */
    .gradio-container {
        max-width: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Ẩn header và footer mặc định của Gradio */
    .gradio-container > .main > .wrap {
        padding: 0 !important;
    }

    /* Responsive cho mobile */
    @media (max-width: 768px) {
        .gradio-container { padding: 0 !important; }
    }
    """

def home():
    return "Trang home đã được chuyển đổi sang Gradio"