import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' 

import customtkinter as ctk
import cv2
import shutil
import random
import json
import threading
import numpy as np
from tkinter import Canvas, filedialog
from PIL import Image

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

# Thiết lập giao diện
ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue")

# Định nghĩa màu sắc thương hiệu
SKQ_BG_COLOR = "#001a4d"    
SKQ_CYAN = "#00d2ff"        
SKQ_WHITE = "#FFFFFF"

class PalmReaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SKQ Analytics - AI Palm Reader")
        self.geometry("900x600")
        self.eval('tk::PlaceWindow . center')

        # --- TỔ CHỨC CẤU TRÚC THƯ MỤC VÀ LUỒNG DỮ LIỆU ---
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.output_folder = os.path.join(self.base_dir, "IMAGE_INPUT")
        os.makedirs(self.output_folder, exist_ok=True)

        self.data_folder = os.path.join(self.base_dir, "DATA")
        os.makedirs(self.data_folder, exist_ok=True)
        
        self.json_path = os.path.join(self.data_folder, "analysis_data.json")
        self.init_json_data()

        # --- NẠP MÔ HÌNH AI ---
        self.model_path = os.path.join(self.data_folder, "palm_model.h5")
        self.ai_model = None
        self.load_ai_model()

        self.sidebar_expanded = False
        self.topbar_expanded = False

        self.show_cinematic_intro()

    def init_json_data(self):
        if not os.path.exists(self.json_path):
            default_data = {
                "Tình cảm": [
                    "Đường tâm đạo sâu, thế giới tình cảm rất phong phú.",
                    "Nội tâm có xu hướng khép kín, cần mở lòng hơn.",
                    "Đường tình duyên có chút trắc trở lúc đầu, nhưng hậu vận viên mãn."
                ],
                "Sức khỏe": [
                    "Đường sinh đạo rõ nét, thể trạng dẻo dai và bền bỉ.",
                    "Cơ thể có dấu hiệu mỏi mệt, cần chú ý cân bằng giấc ngủ.",
                    "Năng lượng dồi dào, hệ miễn dịch hoạt động rất tốt."
                ]
            }
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)

    def load_ai_model(self):
        if os.path.exists(self.model_path):
            try:
                tf.get_logger().setLevel('ERROR') 
                self.ai_model = load_model(self.model_path)
                print("✅ Đã nạp thành công mô hình AI: palm_model.h5")
            except Exception as e:
                print(f"❌ Lỗi khi nạp mô hình AI: {e}")
                self.ai_model = None
        else:
            print("⚠️ Không tìm thấy file palm_model.h5 trong thư mục DATA. Hệ thống sẽ chạy chế độ Demo.")

    def clear_input_folder(self):
        for filename in os.listdir(self.output_folder):
            file_path = os.path.join(self.output_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                pass

    # ================= BƯỚC 1: INTRO ANIMATION =================
    
    def show_cinematic_intro(self):
        self.intro_frame = ctk.CTkFrame(self, fg_color=SKQ_BG_COLOR, corner_radius=0)
        self.intro_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.canvas = Canvas(self.intro_frame, bg=SKQ_BG_COLOR, highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.45, anchor="center", width=500, height=400)

        self.text_skq = self.canvas.create_text(250, 150, text="SKQ", fill=SKQ_BG_COLOR, font=("Arial Black", 80))
        self.poly_arrow = self.canvas.create_polygon(360, 100, 380, 80, 400, 100, fill=SKQ_BG_COLOR)
        self.text_analytics = self.canvas.create_text(250, 230, text="Analytics", fill=SKQ_BG_COLOR, font=("Arial", 45, "bold"))
        self.line_separator = self.canvas.create_line(250, 280, 250, 280, fill=SKQ_BG_COLOR, width=2)
        self.text_tagline = self.canvas.create_text(250, 305, text="SUSTAINABLE KEY QUALITY", fill=SKQ_BG_COLOR, font=("Arial", 12))

        self.after(500, lambda: self.fade_in_item(self.text_skq, SKQ_WHITE, steps=20))
        self.after(800, lambda: self.fade_in_item(self.poly_arrow, SKQ_CYAN, steps=20))
        self.after(1400, lambda: self.fade_in_item(self.text_analytics, SKQ_CYAN, steps=25))
        self.after(2200, self.animate_line_and_tagline)

    def fade_in_item(self, item_id, target_color_hex, steps=20, current_step=0):
        if current_step > steps: return
        fraction = current_step / steps
        bg_rgb = tuple(int(SKQ_BG_COLOR.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        target_rgb = tuple(int(target_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        current_rgb = tuple(int(bg_rgb[i] + (target_rgb[i] - bg_rgb[i]) * fraction) for i in range(3))
        self.canvas.itemconfig(item_id, fill='#%02x%02x%02x' % current_rgb)
        self.after(20, lambda: self.fade_in_item(item_id, target_color_hex, steps, current_step + 1))

    def animate_line_and_tagline(self):
        steps = 15
        def do_step(current_step):
            if current_step > steps:
                self.fade_in_item(self.text_tagline, SKQ_WHITE, steps=15)
                self.after(1000, self.transition_to_main)
                return
            fraction = current_step / steps
            current_half_width = 150 * fraction
            self.canvas.coords(self.line_separator, 250 - current_half_width, 280, 250 + current_half_width, 280)
            target_rgb = (255, 255, 255)
            bg_rgb = (0, 26, 77)
            current_rgb = tuple(int(bg_rgb[i] + (target_rgb[i] - bg_rgb[i]) * fraction) for i in range(3))
            self.canvas.itemconfig(self.line_separator, fill='#%02x%02x%02x' % current_rgb)
            self.after(25, lambda: do_step(current_step + 1))
        do_step(0)

    def transition_to_main(self):
        self.intro_frame.place_forget()
        self.setup_main_gui()

    # ================= BƯỚC 2: GIAO DIỆN CHÍNH & NGĂN KÉO =================

    def setup_main_gui(self):
        self.configure(fg_color="#e9ecef") 

        self.input_view = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=400, height=300)
        self.input_view.pack_propagate(False)
        
        ctk.CTkLabel(self.input_view, text="Nguồn dữ liệu đầu vào", font=("Arial", 20, "bold"), text_color="black").pack(pady=(30, 20))
        
        self.btn_camera = ctk.CTkButton(self.input_view, text="📸 Chụp ảnh Camera", height=45, width=300, font=("Arial", 14),
                                        command=self.capture_from_camera)
        self.btn_camera.pack(pady=10)

        self.btn_upload = ctk.CTkButton(self.input_view, text="📂 Tải ảnh từ máy", height=45, width=300, font=("Arial", 14), 
                                        fg_color="#2b7a2b", hover_color="#1e5c1e", command=self.upload_from_computer)
        self.btn_upload.pack(pady=10)

        self.lbl_status = ctk.CTkLabel(self.input_view, text="Trạng thái: Sẵn sàng nhận dữ liệu", font=("Arial", 13), text_color="gray")
        self.lbl_status.pack(pady=20)
        self.input_view.place(relx=0.5, rely=0.5, anchor="center")

        self.result_view = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=400, height=450)
        self.result_view.pack_propagate(False)

        ctk.CTkLabel(self.result_view, text="Ảnh bàn tay của bạn", font=("Arial", 20, "bold"), text_color="black").pack(pady=(20, 10))
        self.lbl_image = ctk.CTkLabel(self.result_view, text="", width=250, height=250, fg_color="#f0f0f0", corner_radius=10)
        self.lbl_image.pack(pady=10)

        self.btn_reset = ctk.CTkButton(self.result_view, text="🔄 Xem chỉ tay khác", height=40, width=200, fg_color="#ff9f1c", 
                                       hover_color="#f77f00", font=("Arial", 14, "bold"), command=self.reset_to_input)
        self.btn_reset.pack(pady=(20, 10))

        self.setup_drawers()

    def setup_drawers(self):
        self.sidebar_expanded = False
        self.topbar_expanded = False
        self.current_sidebar_x = -180
        
        # Mở rộng chiều cao Topbar lên 250px để chứa đoạn text dài
        self.current_topbar_y = -220
        self.sidebar_anim_id = None
        self.topbar_anim_id = None

        self.topbar = ctk.CTkFrame(self, height=250, corner_radius=0, fg_color="transparent")
        self.topbar.place(x=0, y=-220, relwidth=1) 

        self.topbar_content = ctk.CTkFrame(self.topbar, height=220, corner_radius=0, fg_color="white")
        self.topbar_content.place(x=0, y=0, relwidth=1)
        
        self.topbar_handle = ctk.CTkFrame(self.topbar, height=30, corner_radius=0, fg_color="#9d4edd", cursor="hand2")
        self.topbar_handle.place(x=0, y=220, relwidth=1)
        self.topbar_icon = ctk.CTkLabel(self.topbar_handle, text="▼ Phân tích chi tiết", font=("Arial", 12, "bold"), text_color="white")
        self.topbar_icon.place(relx=0.5, rely=0.5, anchor="center")

        self.cards = {}
        # Đổi thẻ Sự nghiệp thành Tính cách
        card_configs = [("Tình cảm", "❤️"), ("Sức khỏe", "🌱"), ("Tính cách", "🧠")]
        
        for i, (title, icon) in enumerate(card_configs):
            # Mở rộng chiều rộng và chiều cao của từng thẻ (280x160)
            frame = ctk.CTkFrame(self.topbar_content, fg_color="#f8f9fa", corner_radius=10, width=280, height=180)
            frame.place(relx=0.16 + i*0.34, rely=0.5, anchor="center")
            frame.pack_propagate(False)
            
            ctk.CTkLabel(frame, text=f"{icon} {title}", font=("Arial", 14, "bold"), text_color="gray").pack(pady=(10, 5))
            
            # Căn lề trái và bọc chữ chuẩn xác cho đoạn văn dài
            lbl_val = ctk.CTkLabel(frame, text="Không có", font=("Arial", 12), text_color="#ff4d4d", wraplength=250, justify="left")
            lbl_val.pack(padx=15, pady=5)
            self.cards[title] = lbl_val

        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="transparent")
        self.sidebar.place(x=-180, y=0, relheight=1) 

        self.sidebar_content = ctk.CTkFrame(self.sidebar, width=180, corner_radius=0, fg_color="white")
        self.sidebar_content.place(x=0, y=0, relheight=1)
        
        self.sidebar_handle = ctk.CTkFrame(self.sidebar, width=30, corner_radius=0, fg_color=SKQ_BG_COLOR, cursor="hand2")
        self.sidebar_handle.place(x=180, y=0, relheight=1)
        self.sidebar_icon = ctk.CTkLabel(self.sidebar_handle, text="▶", font=("Arial", 16, "bold"), text_color=SKQ_CYAN)
        self.sidebar_icon.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.sidebar_content, text="SKQ AI", font=("Arial", 22, "bold"), text_color=SKQ_BG_COLOR).place(x=45, y=30)
        
        buttons = ["🏠 Dashboard", "📷 Phân tích mới", "🕒 Lịch sử", "⚙️ Cài đặt"]
        for i, text in enumerate(buttons):
            btn = ctk.CTkButton(self.sidebar_content, text=text, fg_color="transparent", text_color="black",
                                hover_color="#f0f0f0", anchor="w", font=("Arial", 14), width=160)
            btn.place(x=10, y=100 + i*50)

        self.bind_all("<Motion>", self.on_mouse_move)
        self.bind("<Leave>", self.on_mouse_leave)

        self.topbar.tkraise()
        self.sidebar.tkraise()

    def on_mouse_move(self, event):
        try:
            mx = self.winfo_pointerx() - self.winfo_rootx()
            my = self.winfo_pointery() - self.winfo_rooty()
        except: return

        if mx <= 30 and not getattr(self, 'sidebar_expanded', False):
            self.sidebar_expanded = True
            self.animate_sidebar(0)
        elif mx > 210 and getattr(self, 'sidebar_expanded', False):
            self.sidebar_expanded = False
            self.animate_sidebar(-180)

        if my <= 30 and not getattr(self, 'topbar_expanded', False):
            self.topbar_expanded = True
            self.animate_topbar(0)
        # Sửa lại tọa độ đóng Topbar theo chiều cao mới (250px)
        elif my > 250 and getattr(self, 'topbar_expanded', False):
            self.topbar_expanded = False
            self.animate_topbar(-220)

    def on_mouse_leave(self, event):
        try:
            mx = self.winfo_pointerx() - self.winfo_rootx()
            my = self.winfo_pointery() - self.winfo_rooty()
            w, h = self.winfo_width(), self.winfo_height()
            
            if mx < 0 or mx > w or my < 0 or my > h:
                if getattr(self, 'sidebar_expanded', False):
                    self.sidebar_expanded = False
                    self.animate_sidebar(-180)
                if getattr(self, 'topbar_expanded', False):
                    self.topbar_expanded = False
                    self.animate_topbar(-220)
        except: pass

    def animate_sidebar(self, target_x):
        if self.sidebar_anim_id:
            self.after_cancel(self.sidebar_anim_id)
            self.sidebar_anim_id = None
        self._do_animate_sidebar(target_x)

    def _do_animate_sidebar(self, target_x):
        current_x = self.current_sidebar_x
        if current_x == target_x:
            self.sidebar_icon.configure(text="◀" if target_x == 0 else "▶")
            return
        step = 45 if target_x > current_x else -45
        new_x = current_x + step
        if (step > 0 and new_x > target_x) or (step < 0 and new_x < target_x): new_x = target_x
        self.current_sidebar_x = new_x
        self.sidebar.place(x=new_x)
        self.sidebar_anim_id = self.after(15, lambda: self._do_animate_sidebar(target_x))

    def animate_topbar(self, target_y):
        if self.topbar_anim_id:
            self.after_cancel(self.topbar_anim_id)
            self.topbar_anim_id = None
        self._do_animate_topbar(target_y)

    def _do_animate_topbar(self, target_y):
        current_y = self.current_topbar_y
        if current_y == target_y:
            self.topbar_icon.configure(text="▲ Thu gọn" if target_y == 0 else "▼ Phân tích chi tiết")
            return
        step = 40 if target_y > current_y else -40
        new_y = current_y + step
        if (step > 0 and new_y > target_y) or (step < 0 and new_y < target_y): new_y = target_y
        self.current_topbar_y = new_y
        self.topbar.place(y=new_y)
        self.topbar_anim_id = self.after(15, lambda: self._do_animate_topbar(target_y))

    # ================= XỬ LÝ ẢNH & THỰC THI AI =================

    def capture_from_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.lbl_status.configure(text="❌ Lỗi: Không mở được Camera!", text_color="red")
            return

        self.lbl_status.configure(text="🎥 Đang mở Camera... (SPACE: chụp, ESC: thoát)", text_color=SKQ_CYAN)
        while True:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            cv2.imshow("SKQ PALM CAPTURE - Nhan SPACE de chup", frame)
            key = cv2.waitKey(1)
            if key == 32: 
                self.clear_input_folder() 
                filename = "current_hand.jpg"
                filepath = os.path.join(self.output_folder, filename)
                cv2.imwrite(filepath, frame)
                cv2.destroyAllWindows()
                cap.release()
                self.process_image_flow(filepath)
                return
            elif key == 27: break
        cap.release()
        cv2.destroyAllWindows()
        self.lbl_status.configure(text="Đã hủy chụp.", text_color="gray")

    def upload_from_computer(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if path:
            self.clear_input_folder() 
            ext = os.path.splitext(path)[1]
            filename = f"current_hand{ext}"
            filepath = os.path.join(self.output_folder, filename)
            shutil.copy(path, filepath)
            self.process_image_flow(filepath)

    def process_image_flow(self, filepath):
        self.lbl_status.configure(text="✅ Đã nhận ảnh. Đang phân tích bằng AI Model...", text_color="#d4a373")
        
        with Image.open(filepath) as img:
            img.thumbnail((250, 250)) 
            self.current_img_ctk = ctk.CTkImage(light_image=img, size=(img.width, img.height))
            
        self.lbl_image.configure(image=self.current_img_ctk, text="")
        
        threading.Thread(target=self.run_ai_prediction, args=(filepath,), daemon=True).start()

    # --- CHẠY DỰ ĐOÁN PHÂN LOẠI 2 LỚP (BINARY CLASSIFICATION) ---
    def run_ai_prediction(self, filepath):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception:
            json_data = {}

        # 1. NẾU CÓ MODEL: CHẠY PREDICT
        if self.ai_model is not None:
            try:
                # Tiền xử lý ảnh (Resize về 224x224, bạn có thể chỉnh lại nếu model của bạn dùng size khác)
                img = Image.open(filepath).convert('RGB')
                img = img.resize((224, 224)) 
                img_array = img_to_array(img)
                img_array = np.expand_dims(img_array, axis=0)
                img_array = img_array / 255.0 

                # Chạy dự đoán
                predictions = self.ai_model.predict(img_array, verbose=0)[0]
                
                # Lấy Index lớp có xác suất cao nhất
                predicted_class_index = int(np.argmax(predictions))

                # ÁNH XẠ KẾT QUẢ DỰA THEO FOLDER LÚC TRAIN
                if predicted_class_index == 0: # KT
                    # Index 0: Loai_1_HaiDuongGiaoNhau
                    tinh_cach_text = "Hai đường giao nhau: Trong nhân tướng học, việc đường trí đạo và đường sinh đạo chạm hoặc dính nhau một đoạn ở điểm xuất phát là dấu hiệu rất phổ biến. Nó tiết lộ mức độ cẩn trọng, khả năng suy nghĩ và tính cách độc lập của bạn."
                else:
                    # Index 1: Loai_2_TachBiet
                    tinh_cach_text = "Hai đường tách biệt: Trong nhân tướng học, việc đường trí đạo và sinh đạo tách rời ở phần đầu cho thấy bạn là người có tính cách độc lập, phóng khoáng và rất tự tin. Bạn hành động quyết đoán, đôi khi bốc đồng nhưng lại tràn đầy đam mê và không ngại rủi ro."

                # Lấy random vui các dòng còn lại để app trông đầy đặn
                tinh_cam_text = random.choice(json_data.get("Tình cảm", ["Chưa có dữ liệu"]))
                suc_khoe_text = random.choice(json_data.get("Sức khỏe", ["Chưa có dữ liệu"]))

            except Exception as e:
                print(f"Lỗi trong quá trình AI Predict: {e}")
                tinh_cam_text = "Lỗi phân tích"
                suc_khoe_text = "Lỗi phân tích"
                tinh_cach_text = "Lỗi phân tích hình ảnh từ mô hình."

        # 2. NẾU KHÔNG CÓ MODEL: CHẠY DEMO RANDOM
        else:
            tinh_cam_text = random.choice(json_data.get("Tình cảm", ["Chưa có dữ liệu"]))
            suc_khoe_text = random.choice(json_data.get("Sức khỏe", ["Chưa có dữ liệu"]))
            tinh_cach_text = "Hãy nạp file palm_model.h5 vào thư mục DATA để AI hoạt động thực sự."

        # 3. GỬI KẾT QUẢ CẬP NHẬT LÊN GIAO DIỆN CHÍNH
        self.after(500, lambda: self.show_ai_results(tinh_cam_text, suc_khoe_text, tinh_cach_text))

    def show_ai_results(self, t_cam, s_khoe, t_cach):
        self.input_view.place_forget() 
        self.result_view.place(relx=0.5, rely=0.5, anchor="center") 
        
        self.topbar.tkraise()
        self.sidebar.tkraise()
        self.lbl_status.configure(text="Trạng thái: Đã có kết quả từ Model AI", text_color="green")

        self.cards["Tình cảm"].configure(text=t_cam, text_color="#001a4d")
        self.cards["Sức khỏe"].configure(text=s_khoe, text_color="#001a4d")
        self.cards["Tính cách"].configure(text=t_cach, text_color="#001a4d")

        self.topbar_expanded = True
        self.animate_topbar(0)

    def reset_to_input(self):
        self.result_view.place_forget() 
        self.input_view.place(relx=0.5, rely=0.5, anchor="center") 
        
        self.topbar.tkraise()
        self.sidebar.tkraise()

        for title, lbl in self.cards.items():
            lbl.configure(text="Không có", text_color="#ff4d4d")
            
        self.topbar_expanded = False
        self.animate_topbar(-220)
        self.lbl_status.configure(text="Trạng thái: Sẵn sàng nhận dữ liệu", text_color="gray")

if __name__ == "__main__":
    app = PalmReaderApp()
    app.mainloop()