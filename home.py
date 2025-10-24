import gradio as gr

def create_home_tab():
    """Tạo tab Home với Gradio + HTML/CSS/JS thuần (có hiệu ứng hover + tilt 3D)"""
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hệ Thống Sinh Video Bài Giảng</title>
        <style>
            .showcase-card .overlay{
            pointer-events: none !important;   /* cho click xuyên qua */
            z-index: 2;
            }
            /* Đảm bảo video nhận click, caption không chặn click */
            .showcase-card { position: relative; }
            .showcase-card::after { pointer-events: none !important; }

            .showcase-card video{
            position: relative;
            z-index: 5;                 /* video nằm trên */
            pointer-events: auto;
            display: block;
            width: 100%;
            height: 250px;
            object-fit: cover;
            transform: translateZ(0);   /* fix một số lỗi hit-test trên Chrome */
            }

            .showcase-card .show-title{
            position: absolute;
            left: 16px;
            bottom: 16px;
            color: #fff;
            font-weight: 600;
            z-index: 1;                 /* dưới video */
            pointer-events: none;       /* không bắt click, tránh che nửa trái */
            }
            /* Chỉ video được nhận click, mọi phần tử con khác trong card đều không */
            .showcase-card, .tilt, .tilt-inner { position: relative; }
            .showcase-card * { pointer-events: none !important; }   /* chặn mọi chồng lấn */
            .showcase-card video { pointer-events: auto !important; z-index: 10; position: relative; }
            /* Tắt nghiêng 3D cho các thẻ video trong khu vực showcase để tránh bug hit-test */
            .showcase-grid .tilt:hover .tilt-inner { transform: none !important; }
            .showcase-grid .tilt, 
            .showcase-grid .tilt-inner, 
            .showcase-grid .showcase-card { transform: none !important; }

            /* caption vẫn hiển thị bình thường nhưng không bắt click */
            .showcase-card .show-title { pointer-events: none !important; z-index: 1; }
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

            /* -------- Showcase video tiles (responsive, no crop) -------- */
            .showcase-card{
                position: relative;
                border-radius: var(--radius);
                transition: transform var(--transition), box-shadow var(--transition), filter var(--transition);
                box-shadow: none;
                transform: translateZ(0);
                overflow: visible;                   /* không cắt video khi fullscreen */
            }

            /* Khung media giữ đúng tỉ lệ 16:9 */
                .showcase-card .media{
                position: relative;
                width: 100%;
                aspect-ratio: 16/9;                  /* responsive height */
                border-radius: inherit;
                overflow: hidden;                    /* chỉ cắt trong thumbnail, không ảnh hưởng fullscreen */
                background: #000;                    /* nền đen cho letterbox */
            }

            /* Video lấp đầy khung, không crop nội dung */
            .showcase-card video{
                position: absolute;
                inset: 0;
                width: 100%;
                height: 100%;
                object-fit: contain;                 /* hiển thị toàn bộ khung hình */
                display: block;
                border-radius: inherit;
                transition: transform var(--transition), filter var(--transition);
                will-change: transform;
                z-index: 1;
            }

            /* Hover chỉ áp vào thumbnail, không ảnh hưởng fullscreen */
            .showcase-card:hover{ transform: translateY(-6px) scale(1.02); box-shadow: var(--shadow-md); }
            .showcase-card:hover video{ transform: scale(1.02); filter: saturate(1.02) contrast(1.01); }

            /* Caption */
            .showcase-card .show-title{
                position: absolute;
                left: 12px;
                bottom: 12px;
                color: #fff;
                font-weight: 600;
                z-index: 2;
                pointer-events: none;
                text-shadow: 0 2px 6px rgba(0,0,0,.6);
            }

            /* Tắt tilt cho khu vực video để tránh xung đột fullscreen */
            .showcase-grid .tilt:hover .tilt-inner { transform: none !important; }
            .showcase-grid .tilt, .showcase-grid .tilt-inner, .showcase-grid .showcase-card { transform: none !important; }

            /* --- Fullscreen fixes (Chrome/Edge/Firefox/Safari) --- */
            video:fullscreen,
            video:-webkit-full-screen {
                width: 100vw !important;
                height: 100vh !important;
                object-fit: contain !important;
                background: #000 !important;
                border-radius: 0 !important;
            }

            .showcase-card:has(video:fullscreen),
            .showcase-card:has(video:-webkit-full-screen) {
                overflow: visible !important;
                transform: none !important;
                box-shadow: none !important;
            }

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

            /* --- Scroll button in Hero --- */
            .hero { position: relative; }

            .scroll-down {
            position: absolute;
            left: 50%;
            bottom: 32px;               /* chỉnh khoảng cách với mép dưới tại đây */
            transform: translateX(-50%);
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            color: #fff;
            text-decoration: none;
            opacity: .95;
            transition: transform .2s ease, opacity .2s ease;
            }

            .scroll-down:hover { opacity: 1; transform: translateX(-50%) translateY(-2px); }
            .scroll-down .arrow { font-size: 24px; animation: bounce 2s infinite; }

            /* tránh header che nội dung khi cuộn tới anchor */
            section[id] { scroll-margin-top: 80px; }

            /* mobile: kéo nút lên một chút cho an toàn */
            @media (max-width: 768px) {
            .scroll-down { bottom: 24px; }
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
        
        <!-- Hero Section -->
        <section class="hero" style="
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e40af 100%);
        position: relative;
        overflow: hidden;">

        <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px; text-align: center;">
            <h1 style="font-size: 56px; font-weight: bold; margin-bottom: 24px; color: white;">
            <span style="background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                Hệ thống sinh video bài giảng tự động
            </span>
            </h1>
            <p style="font-size: 20px; color: rgba(255,255,255,0.8); margin-bottom: 32px; line-height:1.6;">
            Sinh Các Video Bài Giảng Sử Dụng AI Tạo Chuyển Động Khuôn Miệng Cho Hình Ảnh Chân Dung.
            </p>
            <button class="btnfx btn-special" style="padding:16px 32px; border:none; border-radius:12px; font-size:18px; font-weight:600; box-shadow:0 10px 30px rgba(139,92,246,0.3);"
            onclick="(function(){var b=document.querySelector('#nav_get_started_btn'); if(b){b.click();}})();">
            Bắt Đầu Tạo Video
            </button>
            <!-- Nút cuộn xuống -->
            <a href="#about" class="scroll-down">
                <span>Cuộn Xuống</span>
                <span class="arrow">↓</span>
            </a>
        </div>
        </section>


        <!-- About Section -->
        <section id="about" style="padding: 120px 0; background: #f8fafc;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <div class="about-content" style="display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center;">
                    <div style="position: relative;">
                        <img src="file=/home/dunghm/Du_an_sinh_video_main_goloi/Picture_video_UI/Screenshot 2025-10-02_014315.png"
                        alt="Ảnh minh họa"
                        style="width:100%; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.1);">
                    </div>
                    <div>
                        <h2 style="font-size: 42px; font-weight: bold; margin-bottom: 24px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Công Nghệ AI Tiên Tiến</h2>
                        <p style="font-size: 18px; color: #6B7280; margin-bottom: 24px; line-height: 1.7;">
                            Áp dụng mô hình học sâu Sadtaker để tạo chuyển động khuôn mặt và khuôn miệng trong việc đọc các nội dung
                        </p>
                        <p style="font-size: 18px; color: #6B7280; margin-bottom: 24px; line-height: 1.7;">
                           Từ đó tạo ra video bài giảng hoàn chỉnh với cấu trúc gồm có slide powerpoit và giảng viên đọc nội dung slide powerpoit
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
                          <p style="color: #6B7280; line-height: 1.6;">Chuyển đổi bất kỳ ảnh chân dung nào thành video nói chuyện thực tế với đồng bộ môi và biểu cảm khuôn mặt tự nhiên giúp bài giảng trở nên chân thực.</p>
                       </div>
                     </div>
                     <!-- Card 2 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">🎵</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Hỗ Trợ Nhân Bản, Sử Dụng Giọng Nói Người Thật</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Tải lên file âm thanh của bạn để nhân bản, sau đó sử dụng phiên bản giọng nói giúp tăng tính chân thực cho video bài giảng.</p>
                       </div>
                     </div>
                     <!-- Card 3 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">🎨</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Tùy Chỉnh</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Điều chỉnh chất lượng hình ảnh người nói và tốc độ đọc theo yêu cầu.</p>
                       </div>
                     </div>
                     <!-- Card 4 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">⚡</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Tự Động Hóa Mọi Quy Trình</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Tạo video bài giảng với giọng đọc và hình ảnh của giáo viên một cách tự động hóa từ việc lồng ghép slide powerpoit với video hình ảnh giảng viên,
                           tạo sản phẩm là một video hoàn chỉnh sẵn sàng để tải về.</p>
                       </div>
                     </div>
                     <!-- Card 5 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">🔒</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Bảo Mật</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Ảnh và video bài giảng của bạn được xử lý an toàn và không bao giờ được lưu trữ trên máy chủ của chúng tôi sau khi xử lý.</p>
                       </div>
                     </div>
                     <!-- Card 6 -->
                     <div class="tilt">
                       <div class="tilt-inner feature-card" style="background: white; padding: 32px; border: 1px solid #e5e7eb;">
                         <div class="card-icon" style="width: 64px; height: 64px; background: linear-gradient(135deg, #8B5CF6, #3B82F6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 24px; color: white;">📱</div>
                          <h3 style="font-size: 24px; font-weight: bold; margin-bottom: 16px; color: #111827;">Xuất bản video</h3>
                          <p style="color: #6B7280; line-height: 1.6;">Có thể xem trực tiếp video trước khi tải xuống.</p>
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
                            <h3 style="font-size: 28px; font-weight: bold; margin-bottom: 16px; color: #111827;">Chọn ngông ngữ và giọng đọc</h3>
                            <p style="font-size: 18px; color: #6B7280; line-height: 1.6;">Có thể chọn giọng đọc có sẵn hoặc giọng đọc nhân bản, với giọng nhân bản cần tải file mp3 chứa giọng đọc, sau đó chọn bản giọng đọc của mình rồi chọn ngôn ngữ của nội dung slide</p>
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
                            <p style="font-size: 18px; color: #6B7280; line-height: 1.6;">Xuất video bài giảng hoàn chỉnh sẵn sàng chia sẻ hoặc sử dụng.</p>
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
                    <p style="font-size: 20px; color: #6B7280; max-width: 600px; margin: 0 auto;">Xem trước một số sản phầm là video bài giảng hoàn chỉnh</p>
                </div>
                <div class="showcase-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 32px; margin-bottom: 64px;">
                    <!-- Tile 1 -->
                    <div class="tilt">
                      <div class="tilt-inner showcase-card" style="background:#000;">
                        <div class="media">
                            <video muted playsinline preload="metadata" controls>
                                <source src="file=/home/dunghm/Du_an_sinh_video_main_goloi/Picture_video_UI/v1.mp4" type="video/mp4">
                            </video>
                        </div>
                      </div>
                    </div>
                    <!-- Tile 2 -->
                    <div class="tilt">
                      <div class="tilt-inner showcase-card" style="background:#000;">
                        <div class="media">
                        <video muted playsinline preload="metadata" controls>
                            <source src="file=/home/dunghm/Du_an_sinh_video_main_goloi/Picture_video_UI/v2.mp4" type="video/mp4">
                        </video>                       
                        </div>
                      </div>
                    </div>
                    <!-- Tile 3 -->
                    <div class="tilt">
                      <div class="tilt-inner showcase-card" style="background:#000;">
                        <div class="media">
                        <video muted playsinline preload="metadata" controls>
                            <source src="file=/home/dunghm/Du_an_sinh_video_main_goloi/Picture_video_UI/lecture_final.mp4" type="video/mp4">
                        </video>                  
                        </div>
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
    </body>
    </html>
    """
    with gr.Row():
        html_component = gr.HTML(html_content)

    # Nút ẩn để bắt sự kiện điều hướng
    nav_button = gr.Button("Bắt Đầu", elem_id="nav_get_started_btn", visible=False)
    return nav_button

def create_global_navbar():
    navbar_html = """
    <nav style="position: fixed; top: 0; left: 0; right: 0; background: rgba(255,255,255,.95);
                backdrop-filter: blur(10px); border-bottom: 1px solid rgba(0,0,0,.1); z-index: 1000;">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">   
            <div style="display:grid; grid-template-columns: 1fr auto 1fr; align-items:center; padding:16px 0;">
                <!-- Cột 1: Logo (trái) -->
                <div style="font-size:24px; font-weight:bold; background:linear-gradient(135deg,#8B5CF6,#3B82F6);
                            -webkit-background-clip:text; -webkit-text-fill-color:transparent; justify-self:start;">
                    SadTalker
                </div>
                <!-- Cột 2: Menu (giữa tuyệt đối) -->
                <ul class="main-menu"
                    style="display:flex; gap:28px; list-style:none; margin:0; padding:0; align-items:center; justify-self:center;">
                    
                    <li><a class="navfx" href="#" onclick="var b=document.querySelector('#nav_home_btn'); if(b){b.click();} return false;">Trang chủ</a></li>
                    <li><a class="navfx" href="#" onclick="var b=document.querySelector('#nav_index_btn'); if(b){b.click();} return false;">Sinh video</a></li>
                    <li><a class="navfx" href="#" onclick="var b=document.querySelector('#nav_submit_btn'); if(b){b.click();} return false;">Submit</a></li>
                </ul>
                <div></div>
            </div>
        </div>
    </nav>
    """
    with gr.Group():
        navbar = gr.HTML(navbar_html)
        nav_home_btn   = gr.Button(visible=False, elem_id="nav_home_btn")
        nav_index_btn  = gr.Button(visible=False, elem_id="nav_index_btn")
        nav_submit_btn = gr.Button(visible=False, elem_id="nav_submit_btn")

    return {
        "navbar": navbar,
        "nav_home_btn": nav_home_btn,
        "nav_index_btn": nav_index_btn,
        "nav_submit_btn": nav_submit_btn
    }

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
    /* Center content of Index page */
    .index-center {
    max-width: 980px;    /* bạn có thể đổi 880/1024 tuỳ ý */
    margin-left: auto;
    margin-right: auto;
    gap: 12px;
    }
    #index_status { margin-top: 8px; }

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
        /* Ẩn navbar NỘI BỘ của trang Home (không đụng gì tới nội dung khác) */
    .home-page nav {
    display: none !important;
    }

    /* Vẫn cuộn mượt tới các anchor dưới navbar fixed dùng chung */
    .home-page section[id] { 
    scroll-margin-top: 80px; 
    }

    /* Phòng khi phần hero/đầu trang bị navbar che bớt */
    .home-page .hero {
    padding-top: 8px; /* hoặc 0; tuỳ ý, vì create_global_navbar đã có spacer 64px */
    }
    /* --- Fix viền đen bên dưới navbar (Gradio default background) --- */
    /* Chỉ Home mới trong suốt */
    .home-page body,
    .home-page .gradio-container,
    .home-page .main-container,
    .home-page .gradio-container .block,
    .home-page .gradio-container .wrap {
    background: transparent !important;
    }

    /* GỠ hoàn toàn cho Index & Editor (trả về màu mặc định của theme) */
    .index-page .gradio-container,
    .index-page .gradio-container .block,
    .index-page .gradio-container .wrap,
    .editor-page .gradio-container,
    .editor-page .gradio-container .block,
    .editor-page .gradio-container .wrap {
    background: var(--panel-background-fill) !important; /* màu nền panel của theme */
    }


    /* Loại bỏ viền đen trên cùng và khoảng cách lạ giữa navbar và nội dung */
    .main-container {
    margin-top: 0 !important;
    padding-top: 0 !important;
    }

    /* Chặn Gradio tự tạo nền tối cho layout */
    /* Đẩy nội dung xuống dưới navbar cố định (không dùng spacer) */
    :root { --nav-h: 56px; }                 /* khớp với padding/height của nav */

    .home-page .hero {
    margin-top: 0 !important;              /* bỏ margin gây lộ nền đen */
    padding-top: var(--nav-h) !important;  /* đẩy nội dung xuống bên trong hero */
    }

    .index-page, .editor-page {
    margin-top: 0 !important;
    padding-top: var(--nav-h) !important;  /* nếu 2 trang này cũng cần đẩy xuống */
    }

    """

def home():
    return "Trang home đã được chuyển đổi sang Gradio"