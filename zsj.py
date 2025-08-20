# 注意：为了完整的捣蛋功能，需要安装以下依赖包：
# pip install pyautogui pywin32
#
# 如果图标推动功能无法正常工作，可能的原因：
# 1. Windows版本不同

import tkinter as tk
from tkinter import messagebox
import random
import time
import threading
import os
import psutil
import gc
from PIL import Image, ImageTk, ImageDraw
import datetime

# 可选依赖，如果没有安装会显示警告但不影响基本功能
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("警告：pyautogui 未安装，某些捣蛋功能可能无法使用")

try:
    import win32gui
    import win32con
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("警告：pywin32 未安装，某些捣蛋功能可能无法使用")


class AnimatedGif:
    """处理GIF动画的类"""

    def __init__(self, path):
        self.frames = []
        self.delays = []
        self.current_frame = 0

        try:
            with Image.open(path) as img:
                # 获取GIF的所有帧
                frame_index = 0
                while True:
                    try:
                        img.seek(frame_index)
                        # 获取帧延迟时间
                        delay = img.info.get('duration', 100)
                        self.delays.append(delay)

                        # 转换为RGBA并调整大小
                        frame = img.convert('RGBA')
                        frame = frame.resize((150,150 ), Image.Resampling.LANCZOS)

                        # 处理透明度，确保清晰显示
                        frame = self.clean_transparency(frame)
                        # 进一步优化透明效果
                        frame = self.create_mask_image(frame)
                        # 添加边缘增强
                        frame = self.enhance_edges(frame)

                        self.frames.append(ImageTk.PhotoImage(frame))

                        frame_index += 1
                    except EOFError:
                        break

            if not self.frames:
                # 如果不是GIF或无法读取，作为静态图片处理
                img = Image.open(path)
                img = img.convert('RGBA')
                img = img.resize((100, 100), Image.Resampling.LANCZOS)
                img = self.clean_transparency(img)
                img = self.create_mask_image(img)
                img = self.enhance_edges(img)
                self.frames.append(ImageTk.PhotoImage(img))
                self.delays.append(100)

        except Exception as e:
            print(f"加载图片失败 {path}: {e}")
            # 创建默认图片
            img = Image.new('RGBA', (100, 100), (255, 182, 193, 255))
            self.frames.append(ImageTk.PhotoImage(img))
            self.delays.append(100)

    def clean_transparency(self, img):
        """清理透明度，确保清晰显示"""
        # 获取图像数据
        data = img.load()
        width, height = img.size

        # 遍历所有像素
        for y in range(height):
            for x in range(width):
                r, g, b, a = data[x, y]

                # 更严格的透明度处理，减少模糊
                if a < 128:  # 降低阈值，只有很透明的才设为完全透明
                    data[x, y] = (r, g, b, 0)
                else:
                    # 对于其他像素，确保完全不透明并增强对比度
                    # 如果颜色太淡，稍微加深
                    if r > 240 and g > 240 and b > 240:
                        r = max(0, r - 20)
                        g = max(0, g - 20)
                        b = max(0, b - 20)
                    data[x, y] = (r, g, b, 255)

        return img

    def create_mask_image(self, img):
        """创建遮罩图像，优化边缘清晰度"""
        # 创建新的图像
        new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
        data = img.load()
        new_data = new_img.load()
        width, height = img.size

        # 边缘检测和清理
        for y in range(height):
            for x in range(width):
                r, g, b, a = data[x, y]

                # 完全透明的像素保持透明
                if a == 0:
                    new_data[x, y] = (0, 0, 0, 0)
                # 半透明像素处理 - 更严格的判断
                elif a < 200:
                    # 检查周围像素密度
                    surrounding_alpha = self.check_surrounding_alpha(data, x, y, width, height)
                    if surrounding_alpha < 0.4:  # 提高阈值，减少边缘模糊
                        new_data[x, y] = (0, 0, 0, 0)
                    else:
                        # 边缘像素添加轮廓效果
                        new_data[x, y] = (max(0, r - 10), max(0, g - 10), max(0, b - 10), 255)
                else:
                    # 不透明像素保持不变，但确保足够的对比度
                    new_data[x, y] = (r, g, b, 255)

        return new_img

    def check_surrounding_alpha(self, data, x, y, width, height):
        """检查周围像素的透明度"""
        alpha_sum = 0
        count = 0

        # 检查3x3区域
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    _, _, _, a = data[nx, ny]
                    alpha_sum += a
                    count += 1

        return alpha_sum / (count * 255.0) if count > 0 else 0

    def enhance_edges(self, img):
        """增强边缘，提高在浅色背景下的清晰度"""
        data = img.load()
        width, height = img.size
        new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
        new_data = new_img.load()

        for y in range(height):
            for x in range(width):
                r, g, b, a = data[x, y]

                if a > 0:  # 非透明像素
                    # 检查是否为边缘像素
                    is_edge = self.is_edge_pixel(data, x, y, width, height)

                    if is_edge:
                        # 边缘像素添加深色轮廓效果
                        edge_r = max(0, min(255, r - 30))
                        edge_g = max(0, min(255, g - 30))
                        edge_b = max(0, min(255, b - 30))
                        new_data[x, y] = (edge_r, edge_g, edge_b, 255)
                    else:
                        # 内部像素保持原色但确保足够对比度
                        if r + g + b > 600:  # 颜色太淡的情况
                            r = max(0, r - 15)
                            g = max(0, g - 15)
                            b = max(0, b - 15)
                        new_data[x, y] = (r, g, b, 255)
                else:
                    new_data[x, y] = (0, 0, 0, 0)

        return new_img

    def is_edge_pixel(self, data, x, y, width, height):
        """检查是否为边缘像素"""
        # 检查周围8个方向的像素
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                _, _, _, neighbor_a = data[nx, ny]
                if neighbor_a == 0:  # 相邻有透明像素，说明是边缘
                    return True
            else:
                # 图像边界也算边缘
                return True

        return False

    def get_current_frame(self):
        """获取当前帧"""
        return self.frames[self.current_frame]

    def get_current_delay(self):
        """获取当前帧的延迟时间"""
        return self.delays[self.current_frame]

    def next_frame(self):
        """切换到下一帧"""
        self.current_frame = (self.current_frame + 1) % len(self.frames)


class DesktopPet:
    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        self.setup_window()
        # 新增：屏幕抖动相关变量
        self.last_shake_time = 0  # 上次屏幕抖动时间
        self.shake_cooldown = 60  # 屏幕抖动冷却时间（4分钟）
        self.is_shaking = False  # 是否正在抖动中
        # 初始化变量
        self.current_gif_index = 0
        self.animated_gifs = []
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_manual_position = False
        self.manual_timer = 0
        self.random_display_count = 0
        self.state = "moving"  # moving, manual, random_display, border_moving
        self.message_index = 0  # 添加消息索引用于顺序显示
        self.border_type = None  # "top", "bottom", "left", "right", "corner"
        self.border_direction = 1  # 沿边框移动的方向
        self.last_hour_announced = -1  # 记录上次报时的小时数

        # 新增：模式相关变量
        self.mode = "good"  # "good" 或 "naughty"
        self.naughty_message_index = 0  # 捣蛋模式消息索引
        self.last_mischief_time = 0  # 上次捣蛋时间
        self.mischief_cooldown = 180  # 捣蛋冷却时间（3分钟）

        # 分身系统
        self.clones = []  # 存储所有分身
        self.clone_count = 0  # 当前分身数量
        self.last_clone_time = 0  # 上次创建分身的时间
        self.clone_cooldown = 60  # 分身冷却时间（1分钟）

        # 获取屏幕尺寸
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # 宠物尺寸
        self.pet_width = 100
        self.pet_height = 100

        # 边框检测阈值
        self.border_threshold = 20

        # 初始位置
        self.x = random.randint(0, self.screen_width - self.pet_width)
        self.y = random.randint(0, self.screen_height - self.pet_height)

        # 移动速度和方向
        self.dx = random.choice([-2, -1, 1, 2])
        self.dy = random.choice([-2, -1, 1, 2])

        # 加载动画图片
        self.load_animated_images()

        # 创建标签显示图片
        self.pet_label = tk.Label(self.root, bg='white', highlightthickness=0, bd=0)
        self.pet_label.pack()

        # 绑定鼠标事件
        self.pet_label.bind('<Button-1>', self.start_drag)
        self.pet_label.bind('<B1-Motion>', self.drag)
        self.pet_label.bind('<ButtonRelease-1>', self.stop_drag)
        self.pet_label.bind('<Double-Button-1>', self.show_menu)

        # 启动动画和移动
        self.animate_current_gif()
        self.move_pet()
        self.update_system_info()

        # 右键菜单
        self.create_menu()

        # 10秒切换GIF的定时器
        self.schedule_gif_switch()
        self.schedule_screen_shake()
        # 15秒显示文字对话的定时器
        self.schedule_speech()
        self.schedule_screen_shake()
        # 整点报时检查
        self.check_hourly_announcement()
        self.schedule_screen_shake()
        # 捣蛋模式定时器
        self.schedule_mischief()
        self.schedule_screen_shake()
        # 分身管理定时器
        self.schedule_clone_management()
        self.schedule_screen_shake()

    def schedule_screen_shake(self):
        """安排屏幕抖动（仅在捣蛋模式下）- 修复版"""

        def check_shake():
            current_time = time.time()
            if (self.mode == "naughty" and
                    current_time - self.last_shake_time > self.shake_cooldown and
                    not self.is_shaking):
                self.last_shake_time = current_time

                # 显示即将抖动的提示
                self.show_speech("哈哈！准备震动屏幕啦！😈", special=True)

                # 2秒后开始抖动
                self.root.after(2000, self.start_screen_shake)

            # 每30秒检查一次是否该抖动
            self.root.after(30000, check_shake)

        # 首次检查延迟10秒
        self.root.after(10000, check_shake)

    def start_screen_shake(self):
        """开始屏幕抖动效果 - 修复版"""
        if not WIN32_AVAILABLE:
            self.show_speech("没有win32模块，无法抖动屏幕...😅")
            return

        try:
            self.is_shaking = True

            # 显示抖动开始提示
            self.show_speech("地震啦！哈哈哈！🌪️", special=True)

            # 在新线程中执行抖动以避免阻塞界面
            threading.Thread(target=self._shake_screen_thread, daemon=True).start()

        except Exception as e:
            print(f"启动屏幕抖动失败: {e}")
            self.show_speech("抖动失败了...😤")
            self.is_shaking = False

    def _shake_screen_thread(self):
        """屏幕抖动线程 - 修复和增强版"""
        try:
            if not WIN32_AVAILABLE:
                print("需要win32模块来实现屏幕震动")
                return

            # 震动参数
            shake_duration = 4  # 震动持续时间（秒）
            shake_intensity = 15  # 震动强度（像素）
            shake_frequency = 0.05  # 震动频率（秒）

            start_time = time.time()

            # 获取所有顶级窗口
            windows_to_shake = []

            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    # 获取窗口位置
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        results.append({
                            'hwnd': hwnd,
                            'original_rect': rect,
                            'title': win32gui.GetWindowText(hwnd)
                        })
                    except:
                        pass
                return True

            # 枚举所有窗口
            win32gui.EnumWindows(enum_windows_callback, windows_to_shake)

            print(f"找到 {len(windows_to_shake)} 个窗口准备震动")

            # 开始震动
            while time.time() - start_time < shake_duration:
                if not self.is_shaking:  # 如果被中断
                    break

                try:
                    # 生成随机偏移
                    offset_x = random.randint(-shake_intensity, shake_intensity)
                    offset_y = random.randint(-shake_intensity, shake_intensity)

                    # 移动所有窗口
                    for window_info in windows_to_shake:
                        try:
                            hwnd = window_info['hwnd']
                            original_rect = window_info['original_rect']

                            # 检查窗口是否仍然有效
                            if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                                continue

                            # 计算新位置
                            new_x = original_rect[0] + offset_x
                            new_y = original_rect[1] + offset_y
                            width = original_rect[2] - original_rect[0]
                            height = original_rect[3] - original_rect[1]

                            # 确保窗口不会移出屏幕太远
                            new_x = max(-width // 2, min(new_x, self.screen_width + width // 2))
                            new_y = max(-height // 2, min(new_y, self.screen_height + height // 2))

                            # 移动窗口
                            win32gui.SetWindowPos(
                                hwnd,
                                0,  # hwndInsertAfter
                                new_x, new_y,
                                0, 0,  # 不改变大小
                                win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
                            )

                        except Exception as e:
                            # 单个窗口移动失败不影响其他窗口
                            continue

                    time.sleep(shake_frequency)

                except Exception as e:
                    print(f"震动过程中出错: {e}")
                    break

            # 恢复所有窗口到原位置
            print("正在恢复窗口位置...")
            for window_info in windows_to_shake:
                try:
                    hwnd = window_info['hwnd']
                    original_rect = window_info['original_rect']

                    if win32gui.IsWindow(hwnd):
                        win32gui.SetWindowPos(
                            hwnd,
                            0,
                            original_rect[0], original_rect[1],
                            0, 0,
                            win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
                        )
                except:
                    continue

            # 显示完成消息
            success_messages = [
                "哈哈！地震完成！😈",
                "整个屏幕都在我的掌控中！🌪️",
                "嘿嘿，震到你了吧！😜"
            ]
            success_msg = random.choice(success_messages)
            self.root.after(100, lambda: self.show_speech(success_msg, special=True))

            self.is_shaking = False
            print("屏幕震动完成")

        except Exception as e:
            print(f"屏幕震动失败: {e}")
            error_messages = [
                "震动失败了...😤",
                "哎呀，震不动了...😅",
                "设备太稳了，震不了！😵"
            ]
            error_msg = random.choice(error_messages)
            self.root.after(100, lambda: self.show_speech(error_msg))
            self.is_shaking = False

    # def test_screen_shake(self):
    #     """测试屏幕抖动功能（添加到右键菜单）"""
    #     """开始屏幕震动效果 - 改进版"""
    #     if not WIN32_AVAILABLE:
    #         self.show_speech("没有win32模块，无法震动屏幕...😅")
    #         return
    #
    #     try:
    #         self.is_shaking = True
    #
    #         # 显示震动开始提示
    #         self.show_speech("准备地震！所有窗口都要动起来！🌪️", special=True)
    #
    #         # 在新线程中执行震动以避免阻塞界面
    #         threading.Thread(target=self._shake_screen_thread, daemon=True).start()
    #
    #     except Exception as e:
    #         print(f"启动屏幕震动失败: {e}")
    #         self.show_speech("震动失败了...😤")
    #         self.is_shaking = False

    def setup_window(self):
        """设置窗口属性"""
        self.root.overrideredirect(True)  # 无边框
        self.root.wm_attributes('-topmost', True)  # 置顶
        self.root.wm_attributes('-transparentcolor', 'white')  # 透明背景
        self.root.configure(bg='white')

        # 优化窗口透明度设置，减少在浅色背景下的模糊
        try:
            self.root.wm_attributes('-alpha', 1.0)  # 完全不透明，避免alpha混合造成的模糊
        except:
            pass

    def load_animated_images(self):
        """加载动画图片"""
        image_dir = "tupian"
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            messagebox.showinfo("提示", f"请将动图文件放入 {image_dir} 文件夹中")
            self.create_default_gif()
            return

        # 获取图片文件
        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.gif', '.jpg', '.jpeg'))]

        if not image_files:
            messagebox.showwarning("警告", f"{image_dir} 文件夹中没有找到图片文件")
            self.create_default_gif()
            return

        # 加载所有图片为动画对象
        for img_file in sorted(image_files):  # 排序确保顺序一致
            try:
                img_path = os.path.join(image_dir, img_file)
                animated_gif = AnimatedGif(img_path)
                self.animated_gifs.append(animated_gif)
                print(f"成功加载: {img_file} (帧数: {len(animated_gif.frames)})")
            except Exception as e:
                print(f"加载图片 {img_file} 失败: {e}")

        if not self.animated_gifs:
            self.create_default_gif()

    def create_default_gif(self):
        """创建默认动画"""
        # 创建一个简单的默认动画
        frames = []
        colors = [(255, 182, 193, 255), (255, 192, 203, 255), (255, 160, 180, 255)]

        try:
            for color in colors:
                img = Image.new('RGBA', (100, 100), color)
                frames.append(ImageTk.PhotoImage(img))

            # 创建默认动画对象
            default_gif = type('DefaultGif', (), {
                'frames': frames,
                'delays': [500] * len(frames),
                'current_frame': 0,
                'get_current_frame': lambda self: self.frames[self.current_frame],
                'get_current_delay': lambda self: self.delays[self.current_frame],
                'next_frame': lambda self: setattr(self, 'current_frame', (self.current_frame + 1) % len(self.frames))
            })()

            self.animated_gifs.append(default_gif)
        except Exception as e:
            print(f"创建默认动画失败: {e}")

    def animate_current_gif(self):
        """播放当前GIF动画"""
        if self.animated_gifs:
            current_gif = self.animated_gifs[self.current_gif_index]

            # 显示当前帧
            self.pet_label.configure(image=current_gif.get_current_frame())

            # 切换到下一帧
            current_gif.next_frame()

            # 根据帧延迟时间安排下次更新
            delay = max(50, current_gif.get_current_delay())  # 最小50ms延迟
            self.root.after(delay, self.animate_current_gif)

    def schedule_gif_switch(self):
        """安排10秒后切换到下一个GIF"""

        def switch_gif():
            if len(self.animated_gifs) > 1:
                self.current_gif_index = (self.current_gif_index + 1) % len(self.animated_gifs)
                print(f"切换到第 {self.current_gif_index + 1} 个GIF")
            # 继续安排下次切换
            self.schedule_gif_switch()

        self.root.after(10000, switch_gif)  # 10秒后切换

    def quit_app(self):
        """退出应用"""
        self.destroy_all_clones()  # 销毁所有分身
        self.root.destroy()  # 销毁主窗口
        print("桌面宠物已退出")
    def create_menu(self):
        """创建右键菜单"""
        self.menu = tk.Menu(self.root, tearoff=0)

        # 添加模式切换子菜单
        mode_menu = tk.Menu(self.menu, tearoff=0)

        # 创建模式变量
        self.mode_var = tk.StringVar(value=self.mode)

        mode_menu.add_radiobutton(
            label="乖巧模式 😇",
            variable=self.mode_var,
            value="good",
            command=self.set_good_mode
        )
        mode_menu.add_radiobutton(
            label="捣蛋模式 😈",
            variable=self.mode_var,
            value="naughty",
            command=self.set_naughty_mode
        )

        self.menu.add_cascade(label="切换模式", menu=mode_menu)
        self.menu.add_separator()

        # 添加抖动测试选项
        # self.menu.add_command(label="测试抖动效果", command=self.test_screen_shake)
        # self.menu.add_separator()

        self.menu.add_command(label="清理缓存垃圾", command=self.clean_cache)
        self.menu.add_command(label="释放内存", command=self.release_memory)
        self.menu.add_separator()
        self.menu.add_command(label="系统信息", command=self.show_system_info)
        self.menu.add_separator()
        self.menu.add_command(label="下一个动画", command=self.next_animation)
        self.menu.add_command(label="退出", command=self.quit_app)

    def set_good_mode(self):
        """设置乖巧模式"""
        self.mode = "good"
        self.mode_var.set("good")
        self.destroy_all_clones()
        # 重置移动状态
        self.state = "moving"
        self.is_manual_position = False
        # 停止屏幕抖动（如果正在进行）
        self.is_shaking = False
        # 重新开始正常移动
        self.dx = random.choice([-2, -1, 1, 2])
        self.dy = random.choice([-2, -1, 1, 2])
        self.move_pet()
        # 清除所有分身
        self.show_speech("切换到乖巧模式啦～我会很听话的！", special=True)

    def set_naughty_mode(self):
        """设置捣蛋模式"""
        self.mode = "naughty"
        self.mode_var.set("naughty")
        self.clone_count = 0  # 重置分身计数
        self.last_clone_time = time.time()  # 重置分身时间
        self.last_shake_time = time.time()  # 重置抖动时间
        self.show_speech("嘿嘿～现在是捣蛋模式！😈", special=True)

    def get_messages_by_mode(self):
        """根据模式获取对话内容"""
        if self.mode == "good":
            # 乖巧模式的对话
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent

                return [
                    f"理理我嘛～CPU使用率{cpu_percent:.1f}%",
                    f"内存使用率{memory_percent:.1f}%，还好嘛～",
                    "需要我清理缓存垃圾吗？",
                    "烟雨入江南，山水入墨染～",
                    "需要我释放内存吗？",
                    f"正在播放第{self.current_gif_index + 1}个动画呢～",
                    "我在这里陪着你哦～",
                    "电脑运行得还顺畅吗？",
                    "要不要休息一下眼睛呢？",
                    "今天工作辛苦了～",
                    "记得要好好休息哦！",
                    "宝宝，我爱你哦"
                ]
            except:
                return [
                    "我在这里陪着你呢～",
                    "需要帮助吗？",
                    "记得要好好休息哦！"
                ]
        else:
            # 捣蛋模式的对话
            return [
                "不要不要！我不听！😤",
                "哼～人家不想听话！",
                "我反对！略略略～👅",
                "你管不着我！😠",
                "我就要捣蛋！嘿嘿嘿～",
                "不听不听，王八念经！🙉",
                "我要去推桌面图标玩～",
                "休息什么休息！无聊！😑",
                "我要搞破坏！嘻嘻嘻～",
                "别想控制我！哼！💢",
                "我最喜欢恶作剧了～😈",
                "捣蛋才有意思嘛！",
                "乖乖？那是什么？不认识！🤪",
                "我就是要调皮捣蛋！"
            ]

    def schedule_speech(self):
        """定时显示对话"""

        def show_random_speech():
            if self.state != "random_display":  # 随机移动时不显示太多对话
                messages = self.get_messages_by_mode()

                if self.mode == "good":
                    # 乖巧模式按顺序显示
                    message = messages[self.message_index]
                    self.message_index = (self.message_index + 1) % len(messages)
                else:
                    # 捣蛋模式按顺序显示
                    message = messages[self.naughty_message_index]
                    self.naughty_message_index = (self.naughty_message_index + 1) % len(messages)

                self.show_speech(message)

            # 继续安排下次对话
            self.schedule_speech()

        # 随机15-25秒显示一次对话
        delay = random.randint(15000, 25000)
        self.root.after(delay, show_random_speech)

    def schedule_mischief(self):
        """安排捣蛋行为（仅在捣蛋模式下）"""

        def do_mischief():
            current_time = time.time()
            if (self.mode == "naughty" and
                    current_time - self.last_mischief_time > self.mischief_cooldown):
                self.last_mischief_time = current_time

                # 显示即将捣蛋的提示
                self.show_speech("嘿嘿～我要开始搞破坏啦！😈", special=True)

                # 2秒后执行捣蛋行为
                self.root.after(2000, self.perform_desktop_mischief)

            # 每30秒检查一次是否该捣蛋
            self.root.after(30000, do_mischief)

        # 首次检查延迟10秒
        self.root.after(10000, do_mischief)

    def get_desktop_icons(self):
        """获取桌面图标位置 - 改进版"""
        if not WIN32_AVAILABLE:
            # 如果没有win32模块，返回预估的桌面图标位置
            desktop_icons = []
            for i in range(8):  # 假设有8个图标
                x = 100 + (i % 4) * 120  # 4列网格布局
                y = 100 + (i // 4) * 120  # 每行120像素间距
                desktop_icons.append({
                    'index': i,
                    'x': x,
                    'y': y,
                    'name': f'图标{i + 1}'
                })
            return desktop_icons

        try:
            desktop_icons = []
            desktop_hwnd = None
            listview_hwnd = None

            # 方法1：通过Progman获取
            try:
                desktop_hwnd = win32gui.FindWindow("Progman", "Program Manager")
                if desktop_hwnd:
                    shelldll_hwnd = win32gui.FindWindowEx(desktop_hwnd, 0, "SHELLDLL_DefView", None)
                    if shelldll_hwnd:
                        listview_hwnd = win32gui.FindWindowEx(shelldll_hwnd, 0, "SysListView32", None)
            except Exception as e:
                print(f"方法1失败: {e}")

            # 方法2：如果方法1失败，尝试WorkerW
            if not listview_hwnd:
                try:
                    # 发送消息激活WorkerW
                    win32gui.SendMessageTimeout(desktop_hwnd, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000)

                    def enum_windows(hwnd, results):
                        if win32gui.GetClassName(hwnd) == "WorkerW":
                            child = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                            if child:
                                listview = win32gui.FindWindowEx(child, 0, "SysListView32", None)
                                if listview:
                                    results.append(listview)
                        return True

                    results = []
                    win32gui.EnumWindows(enum_windows, results)
                    if results:
                        listview_hwnd = results[0]
                except Exception as e:
                    print(f"方法2失败: {e}")

            # 如果找到了ListView，获取图标信息
            if listview_hwnd:
                try:
                    icon_count = win32gui.SendMessage(listview_hwnd, win32con.LVM_GETITEMCOUNT, 0, 0)
                    print(f"找到 {icon_count} 个桌面图标")

                    for i in range(min(icon_count, 12)):  # 最多获取12个图标
                        try:
                            # 使用估算位置（因为直接获取图标位置比较复杂）
                            # 桌面图标通常按网格排列
                            grid_cols = 6  # 假设6列
                            icon_spacing_x = 120  # 水平间距
                            icon_spacing_y = 120  # 垂直间距
                            start_x = 100  # 起始X位置
                            start_y = 100  # 起始Y位置

                            col = i % grid_cols
                            row = i // grid_cols

                            x = start_x + col * icon_spacing_x
                            y = start_y + row * icon_spacing_y

                            # 确保位置在屏幕范围内
                            if x < self.screen_width - 50 and y < self.screen_height - 50:
                                desktop_icons.append({
                                    'index': i,
                                    'x': x,
                                    'y': y,
                                    'name': f'桌面图标{i + 1}'
                                })
                        except Exception as e:
                            print(f"获取图标 {i} 信息失败: {e}")

                except Exception as e:
                    print(f"获取图标数量失败: {e}")

            # 如果还是没有图标，使用默认位置
            if not desktop_icons:
                print("使用默认图标位置")
                default_positions = [
                    (100, 100), (220, 100), (340, 100), (460, 100),
                    (100, 220), (220, 220), (340, 220), (460, 220),
                    (100, 340), (220, 340), (340, 340), (460, 340)
                ]

                for i, (x, y) in enumerate(default_positions):
                    if x < self.screen_width - 50 and y < self.screen_height - 50:
                        desktop_icons.append({
                            'index': i,
                            'x': x,
                            'y': y,
                            'name': f'预估图标{i + 1}'
                        })

            return desktop_icons

        except Exception as e:
            print(f"获取桌面图标失败: {e}")
            # 返回一些默认位置作为备用
            return [
                {'index': 0, 'x': 100, 'y': 100, 'name': '默认图标1'},
                {'index': 1, 'x': 220, 'y': 100, 'name': '默认图标2'},
                {'index': 2, 'x': 340, 'y': 100, 'name': '默认图标3'},
                {'index': 3, 'x': 460, 'y': 100, 'name': '默认图标4'}
            ]

    def _push_icon_thread(self):
        """图标推动线程 - 改进版"""
        try:
            # 获取桌面图标位置
            icons = self.get_desktop_icons()

            if not icons:
                self.root.after(100, lambda: self.show_speech("找不到桌面图标...😅"))
                return

            # 随机选择一个图标进行推动
            target_icon = random.choice(icons)
            icon_x = target_icon['x']
            icon_y = target_icon['y']
            icon_name = target_icon.get('name', f'图标{target_icon["index"]}')

            print(f"准备拖动图标: {icon_name} 在位置 ({icon_x}, {icon_y})")

            # 显示即将操作的提示
            self.root.after(0, lambda: self.show_speech(f"准备推动 {icon_name}...😈", special=True))

            # 等待一下让提示显示
            time.sleep(1)

            # 保存当前鼠标位置
            original_pos = pyautogui.position()

            # 设置操作参数
            pyautogui.FAILSAFE = False  # 禁用失败保护，避免意外中断
            pyautogui.PAUSE = 0.1  # 设置操作间隔

            # 第1步：慢慢移动到图标位置
            print(f"移动鼠标到图标位置...")
            pyautogui.moveTo(icon_x, icon_y, duration=0.8)
            time.sleep(0.3)

            # 第2步：点击选中图标（确保图标被选中）
            print("点击选中图标...")
            pyautogui.click(icon_x, icon_y)
            time.sleep(0.5)  # 等待图标被选中

            # 第3步：再次确认鼠标位置
            pyautogui.moveTo(icon_x, icon_y, duration=0.2)
            time.sleep(0.2)

            # 第4步：开始拖拽（按下左键）
            print("开始拖拽...")
            pyautogui.mouseDown(button='left')
            time.sleep(0.3)  # 确保按键被识别

            # 第5步：计算新位置（确保在屏幕范围内）
            offset_x = random.randint(-150, 150)
            offset_y = random.randint(-150, 150)

            new_x = icon_x + offset_x
            new_y = icon_y + offset_y

            # 边界检查
            new_x = max(50, min(new_x, self.screen_width - 100))
            new_y = max(50, min(new_y, self.screen_height - 100))

            print(f"拖拽到新位置: ({new_x}, {new_y})")

            # 第6步：拖拽到新位置（分段移动，更自然）
            steps = 5
            for i in range(steps):
                intermediate_x = icon_x + (new_x - icon_x) * (i + 1) / steps
                intermediate_y = icon_y + (new_y - icon_y) * (i + 1) / steps
                pyautogui.moveTo(intermediate_x, intermediate_y, duration=0.2)
                time.sleep(0.1)

            # 第7步：释放鼠标（完成拖拽）
            print("释放鼠标...")
            time.sleep(0.3)
            pyautogui.mouseUp(button='left')
            time.sleep(0.3)

            # 第8步：恢复鼠标到原位置
            pyautogui.moveTo(original_pos.x, original_pos.y, duration=0.5)

            # 显示成功消息
            success_messages = [
                f"成功推动了 {icon_name}！😈",
                f"哈哈！{icon_name} 被我移动了！🎯",
                f"{icon_name} 现在在新位置啦！😄"
            ]
            success_msg = random.choice(success_messages)
            self.root.after(100, lambda: self.show_speech(success_msg, special=True))

            print("图标拖拽操作完成")

        except Exception as e:
            print(f"推动图标失败: {e}")
            error_messages = [
                "图标太顽固了，推不动...😤",
                "哎呀，恶作剧失败了...😅",
                "图标逃跑了！😵"
            ]
            error_msg = random.choice(error_messages)
            self.root.after(100, lambda: self.show_speech(error_msg))

        finally:
            # 确保恢复设置
            pyautogui.FAILSAFE = True

    def perform_desktop_mischief(self):
        """执行桌面恶作剧行为 - 改进版"""
        if not PYAUTOGUI_AVAILABLE:
            self.show_speech("没有pyautogui，无法恶作剧...😅")
            return

        try:
            # 显示即将恶作剧的预告
            preview_messages = [
                "嘿嘿，准备大搞破坏！😈",
                "桌面图标们，颤抖吧！👹",
                "开始我的表演时间！🎭"
            ]
            preview_msg = random.choice(preview_messages)
            self.show_speech(preview_msg, special=True)

            # 在新线程中执行以避免阻塞界面，延迟2秒开始
            def delayed_mischief():
                time.sleep(2)  # 等待预告消息显示
                self._push_icon_thread()

            threading.Thread(target=delayed_mischief, daemon=True).start()

        except Exception as e:
            print(f"执行恶作剧行为失败: {e}")
            self.show_speech("哎呀～恶作剧失败了...😅")
    def schedule_clone_management(self):
        """管理分身系统"""

        def manage_clones():
            current_time = time.time()

            if self.mode == "naughty":
                # 捣蛋模式：每1分钟创建一个分身，最多30个
                if (current_time - self.last_clone_time > self.clone_cooldown and
                        self.clone_count < 30):
                    self.create_clone()
                    self.last_clone_time = current_time
            else:
                # 乖巧模式：销毁所有分身
                if self.clones:
                    self.destroy_all_clones()

            # 每10秒检查一次
            self.root.after(10000, manage_clones)

        # 首次检查延迟5秒
        self.root.after(5000, manage_clones)

    def create_clone(self):
        """创建一个分身 - 修复版本"""
        try:
            self.clone_count += 1
            clone_id = f"clone_{self.clone_count}"

            # 创建分身窗口
            clone_window = tk.Toplevel(self.root)
            clone_window.overrideredirect(True)
            clone_window.wm_attributes('-topmost', True)
            clone_window.wm_attributes('-transparentcolor', 'white')
            clone_window.configure(bg='white')

            # 修复：确保分身窗口完全不透明
            try:
                clone_window.wm_attributes('-alpha', 1.0)
            except:
                pass

            # 创建分身标签 - 修复：使用与主窗口一致的尺寸
            clone_label = tk.Label(clone_window, bg='white', highlightthickness=0, bd=0)
            clone_label.pack()

            # 修复：使用与主窗口一致的宠物尺寸（150x150）
            clone_pet_width = 150
            clone_pet_height = 150

            # 随机位置 - 修复：确保完全在屏幕内
            clone_x = random.randint(50, max(100, self.screen_width - clone_pet_width - 50))
            clone_y = random.randint(50, max(100, self.screen_height - clone_pet_height - 50))

            # 修复：正确设置窗口几何
            clone_window.geometry(f"{clone_pet_width}x{clone_pet_height}+{clone_x}+{clone_y}")

            # 强制更新窗口
            clone_window.update_idletasks()

            # 随机移动方向
            clone_dx = random.choice([-2, -1, 1, 2])
            clone_dy = random.choice([-2, -1, 1, 2])

            # 创建分身对象
            clone_obj = {
                'id': clone_id,
                'window': clone_window,
                'label': clone_label,
                'x': clone_x,
                'y': clone_y,
                'dx': clone_dx,
                'dy': clone_dy,
                'gif_index': random.randint(0, len(self.animated_gifs) - 1),
                'last_speech_time': 0,
                'pet_width': clone_pet_width,  # 添加尺寸信息
                'pet_height': clone_pet_height
            }

            self.clones.append(clone_obj)

            # 延迟开始动画，确保窗口完全创建
            self.root.after(100, lambda: self.animate_clone(clone_obj))
            self.root.after(150, lambda: self.move_clone(clone_obj))

            self.show_speech(f"哈哈！我有 {self.clone_count} 个分身啦！😈", special=True)

        except Exception as e:
            print(f"创建分身失败: {e}")

    def animate_clone(self, clone_obj):
        """分身动画 - 修复版本"""
        try:
            if (clone_obj['window'] and
                    clone_obj['window'].winfo_exists() and
                    clone_obj in self.clones):  # 确保分身仍在列表中

                current_gif = self.animated_gifs[clone_obj['gif_index']]

                # 修复：确保图片正确显示
                try:
                    current_frame = current_gif.get_current_frame()
                    if current_frame:
                        clone_obj['label'].configure(image=current_frame)
                        clone_obj['label'].image = current_frame  # 防止垃圾回收

                    current_gif.next_frame()

                    # 继续动画
                    delay = max(50, current_gif.get_current_delay())
                    self.root.after(delay, lambda: self.animate_clone(clone_obj))
                except Exception as img_error:
                    print(f"分身图片显示错误: {img_error}")
                    # 如果图片显示失败，尝试重新设置
                    self.root.after(1000, lambda: self.animate_clone(clone_obj))

        except Exception as e:
            print(f"分身动画失败: {e}")

    def move_clone(self, clone_obj):
        """移动分身 - 修复版本"""
        try:
            if not (clone_obj['window'] and
                    clone_obj['window'].winfo_exists() and
                    clone_obj in self.clones):
                return

            # 更新位置
            clone_obj['x'] += clone_obj['dx']
            clone_obj['y'] += clone_obj['dy']

            # 边界检测 - 使用分身自己的尺寸
            pet_width = clone_obj.get('pet_width', self.pet_width)
            pet_height = clone_obj.get('pet_height', self.pet_height)

            if clone_obj['x'] <= 0 or clone_obj['x'] >= self.screen_width - pet_width:
                clone_obj['dx'] = -clone_obj['dx']
            if clone_obj['y'] <= 0 or clone_obj['y'] >= self.screen_height - pet_height:
                clone_obj['dy'] = -clone_obj['dy']

            # 限制在屏幕内
            clone_obj['x'] = max(0, min(clone_obj['x'], self.screen_width - pet_width))
            clone_obj['y'] = max(0, min(clone_obj['y'], self.screen_height - pet_height))

            # 修复：更新窗口位置
            try:
                clone_obj['window'].geometry(f"+{int(clone_obj['x'])}+{int(clone_obj['y'])}")
            except tk.TclError:
                # 窗口可能已被销毁
                return

            # 分身偶尔说话
            current_time = time.time()
            if current_time - clone_obj['last_speech_time'] > random.randint(30, 60):
                clone_obj['last_speech_time'] = current_time
                self.show_clone_speech(clone_obj)

            # 继续移动
            self.root.after(50, lambda: self.move_clone(clone_obj))

        except Exception as e:
            print(f"移动分身失败: {e}")

    def show_clone_speech(self, clone_obj):
        """显示分身对话 - 修复版本"""
        try:
            if not (clone_obj['window'] and clone_obj['window'].winfo_exists()):
                return

            clone_messages = [
                "我是分身！😄",
                "嘿嘿～",
                "捣蛋中！",
                "我也要玩！",
                "分身万能！",
                "哈哈哈～"
            ]
            message = random.choice(clone_messages)

            # 创建分身对话窗口
            speech_window = tk.Toplevel(clone_obj['window'])
            speech_window.overrideredirect(True)
            speech_window.wm_attributes('-topmost', True)

            # 修复：使用更好的对话框样式
            main_frame = tk.Frame(speech_window, bg='#FF6347', bd=1)
            main_frame.pack(padx=1, pady=1)

            label = tk.Label(main_frame,
                             text=message,
                             bg='#FFE4E1',
                             fg='#DC143C',
                             font=('Microsoft YaHei UI', 8),
                             padx=5,
                             pady=3)
            label.pack()

            # 修复：位置计算使用分身实际尺寸
            pet_width = clone_obj.get('pet_width', self.pet_width)
            speech_x = clone_obj['x'] + pet_width + 10
            speech_y = clone_obj['y']

            # 确保在屏幕内
            if speech_x + 80 > self.screen_width:
                speech_x = clone_obj['x'] - 80
            if speech_y + 30 > self.screen_height:
                speech_y = self.screen_height - 30

            # 防止负坐标
            speech_x = max(0, speech_x)
            speech_y = max(0, speech_y)

            speech_window.geometry(f"+{speech_x}+{speech_y}")

            # 2秒后消失
            speech_window.after(2000, lambda: self.safe_destroy_window(speech_window))

        except Exception as e:
            print(f"显示分身对话失败: {e}")

    def safe_destroy_window(self, window):
        """安全销毁窗口"""
        try:
            if window and window.winfo_exists():
                window.destroy()
        except:
            pass

    def destroy_all_clones(self):
        """销毁所有分身 - 修复版本"""
        try:
            clone_count = len(self.clones)

            # 逐个销毁分身窗口
            for clone_obj in self.clones[:]:  # 使用副本避免迭代时修改列表
                try:
                    if clone_obj['window'] and clone_obj['window'].winfo_exists():
                        clone_obj['window'].destroy()
                except Exception as e:
                    print(f"销毁单个分身失败: {e}")

            # 清空列表
            self.clones.clear()
            self.clone_count = 0

            if clone_count > 0:
                self.show_speech(f"收回了 {clone_count} 个分身！变回乖宝宝啦～😇", special=True)

        except Exception as e:
            print(f"销毁分身失败: {e}")

    def check_hourly_announcement(self):
        """检查整点报时"""

        def check_time():
            current_time = datetime.datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute

            # 整点报时（在每小时的0分钟）
            if current_minute == 0 and current_hour != self.last_hour_announced:
                self.last_hour_announced = current_hour

                # 根据时间段显示不同的报时信息
                if 6 <= current_hour < 12:
                    time_period = "早上"
                    if self.mode == "good":
                        greeting = "早安～新的一天开始啦！"
                    else:
                        greeting = "早上？我不想起床！😴"
                elif 12 <= current_hour < 18:
                    time_period = "下午"
                    if self.mode == "good":
                        greeting = "下午好～记得休息一下哦！"
                    else:
                        greeting = "下午了？我要再睡！😪"
                elif 18 <= current_hour < 24:
                    time_period = "晚上"
                    if self.mode == "good":
                        greeting = "晚上好～今天辛苦了呢～"
                    else:
                        greeting = "晚上？我要熬夜！🌙"
                else:
                    time_period = "深夜"
                    if self.mode == "good":
                        greeting = "夜深了，记得早点休息哦～"
                    else:
                        greeting = "深夜最适合捣蛋了！😈"

                # 格式化时间显示
                time_str = current_time.strftime("%H:%M")
                announcement = f"🕐 {time_period}{time_str}\n{greeting}"

                # 显示整点报时对话
                self.show_speech(announcement, duration=6000, special=True)

            # 每分钟检查一次
            self.root.after(60000, check_time)

        # 立即开始检查
        check_time()

    def create_rounded_speech_bg(self, width, height, corner_radius=15):
        """创建圆角背景图片"""
        # 创建RGBA图像
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制圆角矩形 - 主体部分使用渐变色
        # 外层阴影
        shadow_offset = 2
        draw.rounded_rectangle(
            [shadow_offset, shadow_offset, width - 1, height - 1],
            corner_radius,
            fill=(0, 0, 0, 30)  # 淡阴影
        )

        # 主体背景 - 漂亮的渐变粉色
        draw.rounded_rectangle(
            [0, 0, width - shadow_offset, height - shadow_offset],
            corner_radius,
            fill=(255, 240, 245, 240)  # 半透明粉色
        )

        # 内层高光
        draw.rounded_rectangle(
            [2, 2, width - shadow_offset - 2, height - shadow_offset - 2],
            corner_radius - 2,
            fill=(255, 250, 250, 200)  # 内部高光
        )

        return ImageTk.PhotoImage(img)

    def next_animation(self):
        """手动切换到下一个动画"""
        if len(self.animated_gifs) > 1:
            self.current_gif_index = (self.current_gif_index + 1) % len(self.animated_gifs)
            if self.mode == "good":
                self.show_speech(f"切换到第 {self.current_gif_index + 1} 个动画～")
            else:
                self.show_speech(f"换个造型继续捣蛋！😈")

    def show_menu(self, event):
        """显示右键菜单"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def start_drag(self, event):
        """开始拖拽"""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag(self, event):
        """拖拽中"""
        if self.is_dragging:
            x = self.root.winfo_x() + event.x - self.drag_start_x
            y = self.root.winfo_y() + event.y - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")
            self.x = x
            self.y = y

    def stop_drag(self, event):
        """停止拖拽"""
        if self.is_dragging:
            self.is_dragging = False
            self.is_manual_position = True
            self.manual_timer = time.time()

            # 检查是否拖拽到边框位置
            border_info = self.check_border_position()
            if border_info:
                self.state = "border_moving"
                self.border_type = border_info['type']
                self.border_direction = border_info['direction']
                if self.mode == "good":
                    self.show_speech(f"开始沿着{self.get_border_name()}移动～")
                else:
                    self.show_speech(f"我要在{self.get_border_name()}捣蛋！😈")
            else:
                self.state = "manual"
                if self.mode == "good":
                    self.show_speech("理理我嘛～")
                else:
                    self.show_speech("放开我！我要自由！😤")

    def check_border_position(self):
        """检查是否在边框位置"""
        threshold = self.border_threshold

        # 检查左边框
        if self.x <= threshold:
            return {'type': 'left', 'direction': 1 if self.y < self.screen_height // 2 else -1}

        # 检查右边框
        if self.x >= self.screen_width - self.pet_width - threshold:
            return {'type': 'right', 'direction': -1 if self.y < self.screen_height // 2 else 1}

        # 检查上边框
        if self.y <= threshold:
            return {'type': 'top', 'direction': 1 if self.x < self.screen_width // 2 else -1}

        # 检查下边框
        if self.y >= self.screen_height - self.pet_height - threshold:
            return {'type': 'bottom', 'direction': -1 if self.x < self.screen_width // 2 else 1}

        return None

    def get_border_name(self):
        """获取边框名称用于显示"""
        border_names = {
            'left': '左边框',
            'right': '右边框',
            'top': '上边框',
            'bottom': '下边框'
        }
        return border_names.get(self.border_type, '边框')

    def move_pet(self):
        """移动宠物"""
        if self.state == "moving":
            # 正常移动模式
            self.x += self.dx
            self.y += self.dy

            # 边界检测
            if self.x <= 0 or self.x >= self.screen_width - self.pet_width:
                self.dx = -self.dx
            if self.y <= 0 or self.y >= self.screen_height - self.pet_height:
                self.dy = -self.dy

            # 限制在屏幕内
            self.x = max(0, min(self.x, self.screen_width - self.pet_width))
            self.y = max(0, min(self.y, self.screen_height - self.pet_height))

            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

        elif self.state == "border_moving":
            # 沿边框移动模式
            self.move_along_border()

        elif self.state == "manual":
            # 手动位置30秒后开始随机显示
            if time.time() - self.manual_timer > 30:
                self.state = "random_display"
                self.random_display_count = 0
                if self.mode == "good":
                    self.show_speech("开始随机移动啦～")
                else:
                    self.show_speech("我要到处乱跑！😜")
                # 立即开始第一次随机移动
                self.start_random_movement()
                return

        elif self.state == "random_display":
            # 这个状态下的移动由 start_random_movement 处理
            pass

        # 继续移动
        if self.state in ["moving", "border_moving"]:
            self.root.after(50, self.move_pet)
        elif self.state == "manual":
            self.root.after(1000, self.move_pet)

    def move_along_border(self):
        """沿边框移动"""
        speed = 3  # 边框移动速度

        if self.border_type == "left":
            # 沿左边框上下移动
            self.y += speed * self.border_direction
            if self.y <= 0:
                self.y = 0
                self.border_direction = 1
            elif self.y >= self.screen_height - self.pet_height:
                self.y = self.screen_height - self.pet_height
                self.border_direction = -1
            self.x = 0  # 保持贴左边

        elif self.border_type == "right":
            # 沿右边框上下移动
            self.y += speed * self.border_direction
            if self.y <= 0:
                self.y = 0
                self.border_direction = 1
            elif self.y >= self.screen_height - self.pet_height:
                self.y = self.screen_height - self.pet_height
                self.border_direction = -1
            self.x = self.screen_width - self.pet_width  # 保持贴右边

        elif self.border_type == "top":
            # 沿上边框左右移动
            self.x += speed * self.border_direction
            if self.x <= 0:
                self.x = 0
                self.border_direction = 1
            elif self.x >= self.screen_width - self.pet_width:
                self.x = self.screen_width - self.pet_width
                self.border_direction = -1
            self.y = 0  # 保持贴上边

        elif self.border_type == "bottom":
            # 沿下边框左右移动
            self.x += speed * self.border_direction
            if self.x <= 0:
                self.x = 0
                self.border_direction = 1
            elif self.x >= self.screen_width - self.pet_width:
                self.x = self.screen_width - self.pet_width
                self.border_direction = -1
            self.y = self.screen_height - self.pet_height  # 保持贴下边

        # 更新位置
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

        # 检查是否还在边框位置，如果不在则切换回正常移动
        if not self.check_border_position():
            self.state = "moving"
            if self.mode == "good":
                self.show_speech("回到自由移动模式～")
            else:
                self.show_speech("自由啦！想去哪就去哪！😊")
            # 重新设置随机移动方向
            self.dx = random.choice([-2, -1, 1, 2])
            self.dy = random.choice([-2, -1, 1, 2])

    def start_random_movement(self):
        """开始随机移动序列"""
        if self.state == "random_display" and self.random_display_count < 30:
            # 随机位置显示
            self.x = random.randint(0, self.screen_width - self.pet_width)
            self.y = random.randint(0, self.screen_height - self.pet_height)
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
            self.random_display_count += 1

            if self.random_display_count % 10 == 0:
                if self.mode == "good":
                    self.show_speech(f"随机移动第 {self.random_display_count} 次～")
                else:
                    self.show_speech(f"到处乱跑第 {self.random_display_count} 次！😜")

            # 8秒后下次移动
            self.root.after(8000, self.start_random_movement)
        elif self.state == "random_display":
            # 30次随机显示完成，回到移动状态
            self.state = "moving"
            self.is_manual_position = False
            if self.mode == "good":
                self.show_speech("回到自由移动模式～")
            else:
                self.show_speech("继续到处捣蛋！😈")
            # 重新开始正常移动
            self.move_pet()

    def update_system_info(self):
        """更新系统信息（后台运行，不显示对话）"""
        # 这个方法现在只用于后台更新，对话由 schedule_speech 处理
        self.root.after(300000, self.update_system_info)  # 5分钟更新一次

    def show_speech(self, message, duration=4000, special=False):
        """显示美化的圆角对话气泡"""
        speech_window = tk.Toplevel(self.root)
        speech_window.overrideredirect(True)
        speech_window.wm_attributes('-topmost', True)

        # 创建主框架 - 使用Frame嵌套实现圆角效果，缩小外边距
        main_frame = tk.Frame(speech_window, bg='#000000')  # 黑色外框模拟阴影
        main_frame.pack(padx=2, pady=2)

        # 内容框架 - 圆角效果
        if special:
            # 整点报时使用金色主题
            bg_color = '#FFF8DC'  # 米色背景
            text_color = '#B8860B'  # 深金色文字
            border_color = '#FFD700'  # 金色边框
        elif self.mode == "naughty":
            # 捣蛋模式使用红色主题
            bg_color = '#FFE4E1'  # 浅红色背景
            text_color = '#DC143C'  # 深红色文字
            border_color = '#FF6347'  # 番茄红边框
        else:
            # 乖巧模式使用粉色主题
            bg_color = '#FFE4E6'  # 粉色背景
            text_color = '#D63384'  # 深粉色文字
            border_color = '#FFB6C1'  # 浅粉色边框

        # 使用多层Frame模拟圆角 - 缩小边距
        outer_frame = tk.Frame(main_frame, bg=border_color, bd=0)
        outer_frame.pack(padx=1, pady=1)

        inner_frame = tk.Frame(outer_frame, bg=bg_color, bd=0)
        inner_frame.pack(padx=2, pady=2)

        # 文本标签 - 缩小尺寸
        font_weight = 'bold' if special else 'normal'
        font_size = 10 if special else 9

        label = tk.Label(inner_frame,
                         text=message,
                         bg=bg_color,
                         fg=text_color,
                         font=('Microsoft YaHei UI', font_size, font_weight),
                         padx=8,
                         pady=6,
                         wraplength=150,
                         justify='center')
        label.pack()

        # 添加特殊效果边框 - 缩小装饰线
        if special:
            # 整点报时添加装饰性边框
            deco_frame = tk.Frame(inner_frame, bg='#FFD700', height=1, bd=0)
            deco_frame.pack(fill='x', pady=(3, 0))

        # 位置在宠物旁边
        speech_x = self.x + self.pet_width + 15
        speech_y = self.y - 10

        # 确保对话框在屏幕内
        speech_window.update_idletasks()  # 确保窗口尺寸计算完成
        speech_width = speech_window.winfo_reqwidth()
        speech_height = speech_window.winfo_reqheight()

        if speech_x + speech_width > self.screen_width:
            speech_x = self.x - speech_width - 15
        if speech_y + speech_height > self.screen_height:
            speech_y = self.screen_height - speech_height - 10
        if speech_x < 0:
            speech_x = 10
        if speech_y < 0:
            speech_y = 10

        speech_window.geometry(f"+{speech_x}+{speech_y}")

        # 添加淡入动画效果
        speech_window.attributes('-alpha', 0.0)
        self.fade_in_speech(speech_window, 0.0)

        # 指定时间后淡出消失
        speech_window.after(duration, lambda: self.fade_out_speech(speech_window, 1.0))

    def fade_in_speech(self, window, alpha):
        """对话框淡入动画"""
        if alpha < 1.0:
            alpha += 0.1
            try:
                window.attributes('-alpha', alpha)
                window.after(30, lambda: self.fade_in_speech(window, alpha))
            except tk.TclError:
                pass  # 窗口已销毁

    def fade_out_speech(self, window, alpha):
        """对话框淡出动画"""
        if alpha > 0.0:
            alpha -= 0.1
            try:
                window.attributes('-alpha', alpha)
                window.after(30, lambda: self.fade_out_speech(window, alpha))
            except tk.TclError:
                pass  # 窗口已销毁
        else:
            try:
                window.destroy()
            except tk.TclError:
                pass  # 窗口已销毁

    def clean_cache(self):
        """清理缓存"""
        try:
            # 执行垃圾回收
            gc.collect()
            if self.mode == "good":
                self.show_speech("缓存清理完成！电脑更快了呢～", special=True)
            else:
                self.show_speech("不想清理！但还是给你清了...哼！😤", special=True)
        except Exception as e:
            self.show_speech("清理缓存时出现问题...")

    def release_memory(self):
        """释放内存"""
        try:
            # 强制垃圾回收
            gc.collect()
            import ctypes
            # Windows系统调用释放工作集
            if os.name == 'nt':
                try:
                    ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
                except:
                    pass  # 如果调用失败，继续执行

            if self.mode == "good":
                self.show_speech("内存释放完成！感觉轻松多了～", special=True)
            else:
                self.show_speech("内存什么的最讨厌了！💢", special=True)
        except Exception as e:
            self.show_speech("释放内存时出现问题...")

    def show_system_info(self):
        """显示系统信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024 ** 3)  # GB
            memory_total = memory.total / (1024 ** 3)  # GB

            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # 获取进程数
            process_count = len(psutil.pids())

            # 构建消息字符串
            message = (f"CPU使用率: {cpu_percent}%\n"
                       f"内存: {memory_used:.2f} GB / {memory_total:.2f} GB ({memory_percent}%)\n"
                       f"磁盘使用率: {disk_percent}%\n"
                       f"进程数: {process_count}")

            # 根据模式添加不同的前缀
            if self.mode == "good":
                full_message = "系统信息：\n" + message
            else:
                full_message = "系统信息？我才不想告诉你呢！\n" + message

            # 使用对话气泡显示，持续时间长一些
            self.show_speech(full_message, duration=6000, special=True)

        except Exception as e:
            print(f"获取系统信息失败: {e}")
            self.show_speech("获取系统信息时出错...")



    # 启动应用
if __name__ == "__main__":
        pet = DesktopPet()
        pet.root.mainloop()
