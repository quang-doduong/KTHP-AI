import customtkinter as ctk
import cv2
import shutil
import os
from tkinter import filedialog, Canvas

# Thiết lập giao diện
ctk.set_appearance_mode("Dark")
# Định nghĩa màu sắc thương hiệu SKQ
SKQ_BG_COLOR = "#001a4d"    # Xanh đậm nền
SKQ_CYAN = "#00d2ff"        # Xanh cyan điểm nhấn
SKQ_WHITE = "#FFFFFF"

class PalmReaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SKQ Analytics - AI Palm Reader")
        self.geometry("600x500")
        self.eval('tk::PlaceWindow . center')

        # Thư mục dữ liệu
        self.output_folder = "IMAGE_INPUT"
        os.makedirs(self.output_folder, exist_ok=True)

        # Trạng thái khởi tạo: Hiển thị màn hình Intro cinematic
        self.show_cinematic_intro()

    # ================= BƯỚC 1: HARDCODE LOGO & CINEMATIC ANIMATION =================
    
    def show_cinematic_intro(self):
        # Tạo khung Intro chiếm toàn bộ cửa sổ
        self.intro_frame = ctk.CTkFrame(self, fg_color=SKQ_BG_COLOR)
        self.intro_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Sử dụng Canvas để vẽ Logo "hardcode"
        self.canvas = Canvas(self.intro_frame, bg=SKQ_BG_COLOR, highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.45, anchor="center", width=500, height=400)

        # Khởi tạo các phần tử ẩn (màu trùng màu nền)
        # 1. Chữ SKQ
        self.text_skq = self.canvas.create_text(250, 150, text="SKQ", fill=SKQ_BG_COLOR, font=("Arial Black", 80))
        # 2. Mũi tên
        self.poly_arrow = self.canvas.create_polygon(360, 100, 380, 80, 400, 100, fill=SKQ_BG_COLOR)
        # 3. Chữ Analytics
        self.text_analytics = self.canvas.create_text(250, 230, text="Analytics", fill=SKQ_BG_COLOR, font=("Arial", 45, "bold"))
        # 4. Đường kẻ (bắt đầu bằng 0 length)
        self.line_separator = self.canvas.create_line(250, 280, 250, 280, fill=SKQ_BG_COLOR, width=2)
        # 5. Slogan
        self.text_tagline = self.canvas.create_text(250, 305, text="SUSTAINABLE KEY QUALITY", fill=SKQ_BG_COLOR, font=("Arial", 12))

        # Bắt đầu chuỗi animation cinematic
        self.after(500, lambda: self.fade_in_item(self.text_skq, SKQ_WHITE, steps=20))
        self.after(800, lambda: self.fade_in_item(self.poly_arrow, SKQ_CYAN, steps=20))
        self.after(1400, lambda: self.fade_in_item(self.text_analytics, SKQ_CYAN, steps=25))
        
        # Đường kẻ và tagline xuất hiện cùng lúc sau khi chữ chính hiện xong
        self.after(2200, self.animate_line_and_tagline)

    def fade_in_item(self, item_id, target_color_hex, steps=20, current_step=0):
        """Hàm đệ quy tạo hiệu ứng fade in bằng cách biến đổi màu dần dần"""
        if current_step > steps:
            return

        # Tính toán tỷ lệ hoàn thành
        fraction = current_step / steps
        
        # Hàm chuyển đổi Hex sang RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        # Màu nền và màu đích dưới dạng RGB
        bg_rgb = hex_to_rgb(SKQ_BG_COLOR)
        target_rgb = hex_to_rgb(target_color_hex)

        # Tính toán màu hiện tại (Interpolation)
        current_rgb = tuple(
            int(bg_rgb[i] + (target_rgb[i] - bg_rgb[i]) * fraction)
            for i in range(3)
        )

        # Chuyển RGB về lại Hex để Canvas hiểu
        current_hex = '#%02x%02x%02x' % current_rgb
        
        # Cập nhật màu phần tử
        self.canvas.itemconfig(item_id, fill=current_hex)

        # Gọi lại hàm sau một khoảng thời gian ngắn (tạo độ mượt)
        self.after(20, lambda: self.fade_in_item(item_id, target_color_hex, steps, current_step + 1))

    def animate_line_and_tagline(self):
        """Animation vẽ đường kẻ từ giữa ra 2 bên và hiện slogan cùng lúc"""
        steps = 15
        
        def do_step(current_step):
            if current_step > steps:
                # Sau khi vẽ xong đường kẻ, hiện slogan bằng hiệu ứng fade
                self.fade_in_item(self.text_tagline, SKQ_WHITE, steps=15)
                # Chờ một lúc rồi vào App chính
                self.after(1500, self.transition_to_main)
                return

            fraction = current_step / steps
            # Chiều rộng tối đa đường kẻ là 300px (từ 100 đến 400), tâm ở 250
            max_half_width = 150
            current_half_width = max_half_width * fraction
            
            # Cập nhật tọa độ đường kẻ (mở rộng từ tâm)
            self.canvas.coords(self.line_separator, 250 - current_half_width, 280, 250 + current_half_width, 280)
            
            # Cập nhật màu đường kẻ sang trắng dần
            target_rgb = (255, 255, 255) # White
            bg_rgb = (0, 26, 77) # BG
            current_rgb = tuple(int(bg_rgb[i] + (target_rgb[i] - bg_rgb[i]) * fraction) for i in range(3))
            current_hex = '#%02x%02x%02x' % current_rgb
            self.canvas.itemconfig(self.line_separator, fill=current_hex)

            self.after(25, lambda: do_step(current_step + 1))

        do_step(0)

    def transition_to_main(self):
        """Chuyển cảnh mượt mà: Fade out toàn bộ Intro frame trước khi xóa"""
        # (Để đơn giản và không làm phức tạp code GUI, chúng ta place_forget luôn. 
        # Nếu muốn cinematic hơn nữa ở bước này cần dùng thêm kỹ thuật phức tạp về alpha channel của Ctk)
        self.intro_frame.place_forget()
        self.setup_main_gui()

    # ================= BƯỚC 2: GIAO DIỆN CHÍNH (GIỮ NGUYÊN) =================

    def setup_main_gui(self):
        # Thiết lập nền chính trùng màu thương hiệu
        self.configure(fg_color=SKQ_BG_COLOR)

        # Tiêu đề
        self.lbl_title = ctk.CTkLabel(self, text="SKQ ANALYTICS - DATA COLLECTION", 
                                      font=("Arial", 20, "bold"), text_color=SKQ_CYAN)
        self.lbl_title.pack(pady=(40, 20))

        # Nút bấm
        self.btn_camera = ctk.CTkButton(self, text="📸 CHỤP ẢNH THỜI GIAN THỰC", width=300, height=50,
                                        font=("Arial", 14, "bold"), fg_color="#3a86ff", hover_color="#0056b3",
                                        command=self.capture_from_camera)
        self.btn_camera.pack(pady=10)

        self.btn_upload = ctk.CTkButton(self, text="📂 TẢI ẢNH LÊN MÁY TÍNH", width=300, height=50,
                                        font=("Arial", 14, "bold"), fg_color="#2b7a2b", 
                                        hover_color="#1e5c1e", command=self.upload_from_computer)
        self.btn_upload.pack(pady=10)

        # Khung trạng thái
        self.status_frame = ctk.CTkFrame(self, width=500, height=120, fg_color="#001233", corner_radius=10)
        self.status_frame.pack(pady=30, padx=20)
        self.status_frame.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Hệ thống SKQ sẵn sàng. Hãy cung cấp dữ liệu bàn tay.", 
                                      font=("Arial", 13), text_color="#aaaaaa", wraplength=450)
        self.lbl_status.pack(expand=True)

    # ================= LOGIC XỬ LÝ ẢNH (GIỮ NGUYÊN) =================

    def capture_from_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.update_status("❌ Không mở được Camera!", "red")
            return

        self.update_status("🎥 Đang mở Camera... (SPACE để chụp, ESC để thoát)", SKQ_CYAN)
        while True:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            cv2.imshow("SKQ PALM CAPTURE - Nhấn SPACE để chụp", frame)
            key = cv2.waitKey(1)
            if key == 32: # SPACE
                filename = "temp_hand_cam.jpg"
                cv2.imwrite(os.path.join(self.output_folder, filename), frame)
                cv2.destroyAllWindows()
                cap.release()
                self.trigger_fake_ai(filename)
                return
            elif key == 27: break
        cap.release()
        cv2.destroyAllWindows()
        self.update_status("Hệ thống SKQ sẵn sàng.", "#aaaaaa")

    def upload_from_computer(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if path:
            filename = "temp_hand_uploaded.jpg"
            shutil.copy(path, os.path.join(self.output_folder, filename))
            self.trigger_fake_ai(filename)

    def update_status(self, text, color="white"):
        self.lbl_status.configure(text=text, text_color=color)

    def trigger_fake_ai(self, filename):
        self.update_status(f"✅ Đã ghi nhận file: {filename}\nĐang chuẩn bị phân tích...", "#FFB703")
        self.after(1000, lambda: self.fake_loading(0))

    def fake_loading(self, step):
        if step < 10:
            dots = "." * (step % 4 + 1)
            self.update_status(f"🤖 SKQ AI ĐANG PHÂN TÍCH CHỈ TAY{dots}", "#4cc9f0")
            self.after(300, lambda: self.fake_loading(step + 1))
        else:
            self.update_status("🔮 HOÀN TẤT!\nẢnh đã sẵn sàng trong IMAGE_INPUT.\nChờ Model AI thật xử lý kết quả.", "#9d4edd")

if __name__ == "__main__":
    app = PalmReaderApp()
    app.mainloop()