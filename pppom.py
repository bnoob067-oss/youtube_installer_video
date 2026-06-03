from tkinter import *
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import re
from datetime import datetime
import subprocess
import sys

# Заменяем pytubefix на yt-dlp
try:
    import yt_dlp
except ImportError:
    messagebox.showerror("Ошибка", "Библиотека yt-dlp не установлена. Установите её командой: pip install yt-dlp")
    sys.exit(1)

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Video Downloader Pro")
        
        # Устанавливаем полноэкранный режим
        self.root.attributes('-fullscreen', True)
        
        # Переменные
        self.url_var = StringVar()
        self.status_var = StringVar(value="Готов к работе")
        self.progress_var = DoubleVar(value=0)
        self.download_path = os.path.expanduser("~/Downloads")
        self.video_info = None
        self.formats_list = []
        self.current_url = ""  # Добавляем переменную для хранения текущего URL
        
        # Настройка опций yt-dlp
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        # Стили
        self.setup_styles()
        
        # Интерфейс
        self.setup_ui()
        
        # Привязываем клавишу Escape для выхода из полноэкранного режима
        self.root.bind('<Escape>', self.toggle_fullscreen)
        
        # Привязываем клавишу F11 для переключения полноэкранного режима
        self.root.bind('<F11>', self.toggle_fullscreen)
        
    def toggle_fullscreen(self, event=None):
        """Переключение полноэкранного режима по Escape или F11"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
        
    def setup_styles(self):
        """Настройка стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цветовая схема
        self.bg_color = "#f0f0f0"
        self.accent_color = "#ff0000"
        self.text_color = "#333333"
        
        self.root.configure(bg=self.bg_color)
        
    def setup_ui(self):
        """Создание интерфейса"""
        # Создаем Canvas и Scrollbar для возможности прокрутки
        self.main_canvas = Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        
        # Упаковываем Canvas и Scrollbar
        self.main_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        
        # Создаем фрейм внутри Canvas
        self.main_frame = Frame(self.main_canvas, bg=self.bg_color)
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        
        # Настройка прокрутки
        self.main_frame.bind("<Configure>", self.on_frame_configure)
        self.main_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Привязываем колесико мыши для прокрутки
        self.bind_mousewheel()
        
        # Главный контейнер с отступами
        main_container = Frame(self.main_frame, bg=self.bg_color)
        main_container.pack(fill=BOTH, expand=True, padx=30, pady=20)
        
        # Заголовок
        title_frame = Frame(main_container, bg=self.bg_color)
        title_frame.pack(fill=X, pady=(0, 15))
        
        Label(title_frame, text="🎬 Universal Video Downloader Pro", 
              font=("Arial", 26, "bold"), 
              bg=self.bg_color, 
              fg=self.accent_color).pack()
        
        Label(title_frame, text="Скачивайте видео с YouTube, Vimeo, Dailymotion, Twitch, Facebook и 1000+ других платформ", 
              font=("Arial", 12), 
              bg=self.bg_color, 
              fg=self.text_color).pack()
        
        # Подсказка о полноэкранном режиме
        hint_frame = Frame(title_frame, bg=self.bg_color)
        hint_frame.pack(pady=(5, 0))
        Label(hint_frame, text="💡 Нажмите ESC или F11 для выхода из полноэкранного режима | Используйте колесико мыши для прокрутки", 
              font=("Arial", 9), 
              bg=self.bg_color, 
              fg="#666").pack()
        
        # Фрейм для ввода URL
        url_frame = LabelFrame(main_container, text=" Ссылка на видео ", 
                              font=("Arial", 12, "bold"),
                              bg=self.bg_color, 
                              fg=self.text_color,
                              relief=GROOVE, 
                              borderwidth=2)
        url_frame.pack(fill=X, pady=(0, 15))
        
        Entry(url_frame, textvariable=self.url_var, 
              font=("Arial", 12), 
              relief=SOLID, 
              borderwidth=1).pack(fill=X, padx=15, pady=15, ipady=8)
        
        # Кнопки для URL
        url_buttons_frame = Frame(url_frame, bg=self.bg_color)
        url_buttons_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        Button(url_buttons_frame, text="📋 Вставить из буфера", 
               command=self.paste_from_clipboard,
               bg="#e0e0e0",
               activebackground="#d0d0d0",
               relief=RAISED,
               font=("Arial", 11),
               padx=10,
               pady=5).pack(side=LEFT, padx=5)
        
        Button(url_buttons_frame, text="🔍 Получить информацию", 
               command=self.get_video_info,
               bg=self.accent_color,
               fg="white",
               activebackground="#cc0000",
               relief=RAISED,
               font=("Arial", 11, "bold"),
               padx=15,
               pady=5).pack(side=RIGHT, padx=5)
        
        # Информация о видео
        self.info_frame = LabelFrame(main_container, text=" Информация о видео ", 
                                    font=("Arial", 12, "bold"),
                                    bg=self.bg_color, 
                                    fg=self.text_color,
                                    relief=GROOVE, 
                                    borderwidth=2)
        self.info_frame.pack(fill=X, pady=(0, 15))
        
        # Устанавливаем фиксированную высоту для info_text
        self.info_text = scrolledtext.ScrolledText(self.info_frame, 
                                                   height=6, 
                                                   font=("Arial", 11),
                                                   wrap=WORD,
                                                   relief=SOLID,
                                                   borderwidth=1)
        self.info_text.pack(fill=X, padx=15, pady=15)
        self.info_text.config(state=DISABLED)
        
        # Выбор формата
        format_frame = LabelFrame(main_container, text=" Выбор формата ", 
                                 font=("Arial", 12, "bold"),
                                 bg=self.bg_color, 
                                 fg=self.text_color,
                                 relief=GROOVE, 
                                 borderwidth=2)
        format_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # TreeView для форматов с фиксированной высотой
        columns = ("#", "Тип", "Качество", "Формат", "Размер", "Кодек")
        self.format_tree = ttk.Treeview(format_frame, columns=columns, show="headings", height=10)
        
        # Настройка ширины колонок для полноэкранного режима
        self.format_tree.heading("#", text="#")
        self.format_tree.heading("Тип", text="Тип")
        self.format_tree.heading("Качество", text="Качество")
        self.format_tree.heading("Формат", text="Формат")
        self.format_tree.heading("Размер", text="Размер")
        self.format_tree.heading("Кодек", text="Кодек")
        
        self.format_tree.column("#", width=60, anchor="center")
        self.format_tree.column("Тип", width=150, anchor="center")
        self.format_tree.column("Качество", width=120, anchor="center")
        self.format_tree.column("Формат", width=100, anchor="center")
        self.format_tree.column("Размер", width=100, anchor="center")
        self.format_tree.column("Кодек", width=200, anchor="center")
        
        scrollbar = ttk.Scrollbar(format_frame, orient=VERTICAL, command=self.format_tree.yview)
        self.format_tree.configure(yscrollcommand=scrollbar.set)
        
        self.format_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=(15, 0), pady=15)
        scrollbar.pack(side=RIGHT, fill=Y, padx=(0, 15), pady=15)
        
        # Панель загрузки
        download_frame = LabelFrame(main_container, text=" Настройки загрузки ", 
                                   font=("Arial", 12, "bold"),
                                   bg=self.bg_color, 
                                   fg=self.text_color,
                                   relief=GROOVE, 
                                   borderwidth=2)
        download_frame.pack(fill=X, pady=(0, 15))
        
        # Выбор папки
        path_frame = Frame(download_frame, bg=self.bg_color)
        path_frame.pack(fill=X, padx=15, pady=15)
        
        Label(path_frame, text="Папка для сохранения:", 
              font=("Arial", 11), 
              bg=self.bg_color).pack(side=LEFT)
        
        self.path_label = Label(path_frame, text=self.download_path, 
                               font=("Arial", 11), 
                               bg="white",
                               relief=SUNKEN,
                               anchor="w",
                               width=50)
        self.path_label.pack(side=LEFT, padx=(10, 5), fill=X, expand=True)
        
        Button(path_frame, text="📁 Выбрать", 
               command=self.select_folder,
               bg="#e0e0e0",
               activebackground="#d0d0d0",
               relief=RAISED,
               font=("Arial", 11),
               padx=10,
               pady=5).pack(side=RIGHT)
        
        # Прогресс бар
        progress_frame = Frame(download_frame, bg=self.bg_color)
        progress_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var,
                                           maximum=100,
                                           length=400,
                                           mode='determinate')
        self.progress_bar.pack(fill=X, pady=(0, 10))
        
        self.status_label = Label(progress_frame, textvariable=self.status_var,
                                 font=("Arial", 11), 
                                 bg=self.bg_color,
                                 fg=self.text_color)
        self.status_label.pack()
        
        # Кнопки действий (уменьшаем размер для лучшего отображения)
        buttons_frame = Frame(main_container, bg=self.bg_color)
        buttons_frame.pack(fill=X, pady=(5, 10))
        
        # Создаем фрейм для кнопок с равномерным распределением
        buttons_container = Frame(buttons_frame, bg=self.bg_color)
        buttons_container.pack(expand=True, fill=X)
        
        Button(buttons_container, text="⬇️ Скачать выбранное", 
               command=self.download_selected,
               bg="#4CAF50",
               fg="white",
               activebackground="#45a049",
               font=("Arial", 11, "bold"),
               height=1,
               width=20,
               padx=8,
               pady=8).pack(side=LEFT, padx=8, expand=True, fill=X)
        
        Button(buttons_container, text="🔄 Очистить", 
               command=self.clear_all,
               bg="#2196F3",
               fg="white",
               activebackground="#1976D2",
               font=("Arial", 11),
               height=1,
               width=15,
               padx=8,
               pady=8).pack(side=LEFT, padx=8, expand=True, fill=X)
        
        Button(buttons_container, text="📂 Открыть папку", 
               command=self.open_download_folder,
               bg="#FF9800",
               fg="white",
               activebackground="#F57C00",
               font=("Arial", 11),
               height=1,
               width=15,
               padx=8,
               pady=8).pack(side=LEFT, padx=8, expand=True, fill=X)
        
        Button(buttons_container, text="❌ Выход", 
               command=self.root.quit,
               bg="#f44336",
               fg="white",
               activebackground="#d32f2f",
               font=("Arial", 11),
               height=1,
               width=12,
               padx=8,
               pady=8).pack(side=RIGHT, padx=8)
        
        # Подсказка
        Label(main_container, text="💡 Поддерживаются: YouTube, Vimeo, Dailymotion, Twitch, Facebook, Twitter, TikTok, Instagram и многие другие",
              font=("Arial", 10),
              bg=self.bg_color,
              fg="#666").pack(pady=(5, 0))
        
    def on_frame_configure(self, event):
        """Обновление области прокрутки при изменении размера фрейма"""
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """Изменение ширины внутреннего фрейма при изменении размера Canvas"""
        self.main_canvas.itemconfig(self.canvas_window, width=event.width)
    
    def bind_mousewheel(self):
        """Привязка колесика мыши для прокрутки"""
        def on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel_to_widget(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel_to_widget(child)
        
        bind_mousewheel_to_widget(self.root)
    
    def paste_from_clipboard(self):
        """Вставить URL из буфера обмена"""
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_var.set(clipboard_text)
            messagebox.showinfo("Успех", "Ссылка вставлена из буфера обмена!")
        except:
            messagebox.showerror("Ошибка", "Не удалось получить данные из буфера")
    
    def format_file_size(self, size_bytes):
        """Форматирование размера файла в читаемый вид"""
        if size_bytes is None or size_bytes == 0:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} GB"
    
    def get_video_info(self):
        """Получить информацию о видео (поддерживает множество платформ)"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("Внимание", "Введите ссылку на видео!")
            return
        
        # Сохраняем текущий URL
        self.current_url = url
        
        # Очистка предыдущих данных
        self.format_tree.delete(*self.format_tree.get_children())
        self.info_text.config(state=NORMAL)
        self.info_text.delete(1.0, END)
        
        try:
            self.status_var.set("Получаю информацию о видео...")
            self.root.update()
            
            # Настройки для получения информации без скачивания
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Получаем информацию
                self.video_info = ydl.extract_info(url, download=False)
                
                # Определяем тип контента (видео или плейлист)
                if 'entries' in self.video_info:
                    # Это плейлист
                    self.show_playlist_info()
                else:
                    # Это одно видео
                    self.show_video_info()
                
            self.status_var.set("Информация получена. Выберите формат для скачивания")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить информацию:\n{str(e)}")
            self.status_var.set("Ошибка при получении информации")
            self.video_info = None
    
    def show_video_info(self):
        """Отображение информации об одном видео"""
        info = self.video_info
        
        # Извлекаем информацию с проверкой наличия полей
        title = info.get('title', 'N/A')
        uploader = info.get('uploader', 'N/A')
        duration = info.get('duration', 0)
        if duration:
            duration_str = f"{duration // 60}:{duration % 60:02d}"
        else:
            duration_str = "N/A"
        view_count = info.get('view_count', 'N/A')
        if view_count != 'N/A' and isinstance(view_count, (int, float)):
            view_count = f"{view_count:,}"
        
        # Используем сохраненный URL вместо неопределенной переменной
        webpage_url = self.current_url
        
        # Определение платформы по домену
        platform = "YouTube"
        if 'vimeo.com' in webpage_url:
            platform = "Vimeo"
        elif 'dailymotion.com' in webpage_url:
            platform = "Dailymotion"
        elif 'twitch.tv' in webpage_url:
            platform = "Twitch"
        elif 'facebook.com' in webpage_url:
            platform = "Facebook"
        elif 'youtube.com' in webpage_url or 'youtu.be' in webpage_url:
            platform = "YouTube"
        else:
            platform = info.get('extractor', 'Unknown')
        
        info_text = f"""📺 Название: {title}
👤 Автор: {uploader}
🎥 Платформа: {platform}
⏱️ Длительность: {duration_str}
👁️ Просмотров: {view_count}
"""
        
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state=DISABLED)
        
        # Заполняем список форматов
        self.populate_formats()
    
    def show_playlist_info(self):
        """Отображение информации о плейлисте"""
        playlist = self.video_info
        entries = playlist.get('entries', [])
        
        info_text = f"""📋 ПЛЕЙЛИСТ: {playlist.get('title', 'N/A')}
👤 Автор: {playlist.get('uploader', 'N/A')}
📹 Видео в плейлисте: {len(entries)}
"""
        
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state=DISABLED)
        
        # Для плейлиста показываем доступные форматы на основе первого видео
        if entries:
            messagebox.showinfo("Плейлист", 
                              f"Обнаружен плейлист с {len(entries)} видео.\n"
                              f"Доступные форматы будут определены по первому видео.\n"
                              f"При скачивании будет сохранен весь плейлист.")
            self.populate_formats(is_playlist=True)
    
    def populate_formats(self, is_playlist=False):
        """Заполнить список доступных форматов"""
        if not self.video_info:
            return
        
        self.formats_list = []
        
        try:
            # Получаем форматы из информации о видео
            formats = self.video_info.get('formats', [])
            index = 1
            
            # Сначала добавляем видео+аудио (потоковые форматы)
            for fmt in formats:
                # Фильтруем и показываем основные форматы
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                resolution = fmt.get('resolution', 'N/A')
                ext = fmt.get('ext', 'N/A').upper()
                filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0)
                size_str = self.format_file_size(filesize)
                
                # Определяем тип
                if vcodec != 'none' and acodec != 'none':
                    format_type = "🎬 Видео+Аудио"
                elif vcodec != 'none':
                    format_type = "🎞️ Только видео"
                elif acodec != 'none':
                    format_type = "🎵 Только аудио"
                else:
                    continue
                
                # Определяем качество
                quality = resolution
                if fmt.get('tbr'):
                    if format_type == "🎵 Только аудио":
                        quality = f"{fmt.get('abr', 'N/A')} kbps"
                    else:
                        quality = resolution if resolution != 'N/A' else f"{fmt.get('tbr', 0):.0f} kbps"
                
                # Кодек
                codec = vcodec if vcodec != 'none' else acodec
                if codec == 'none':
                    codec = 'N/A'
                elif codec:
                    codec = codec.split('.')[0][:20]
                else:
                    codec = 'N/A'
                
                self.format_tree.insert("", "end", values=(
                    index,
                    format_type,
                    quality,
                    ext,
                    size_str,
                    codec
                ))
                
                self.formats_list.append({
                    'format_id': fmt.get('format_id'),
                    'type': format_type,
                    'ext': ext,
                    'is_playlist': is_playlist
                })
                index += 1
                
                # Ограничиваем количество отображаемых форматов
                if index > 50:
                    self.format_tree.insert("", "end", values=(index, "...", "и другие форматы", "...", "...", "..."))
                    break
                    
        except Exception as e:
            self.format_tree.insert("", "end", values=(1, "⚠️", "Ошибка получения форматов", str(e)[:30], "", ""))
    
    def select_folder(self):
        """Выбрать папку для сохранения"""
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=self.download_path
        )
        
        if folder:
            self.download_path = folder
            self.path_label.config(text=folder)
    
    def download_progress_hook(self, d):
        """Обработчик прогресса загрузки для yt-dlp"""
        if d['status'] == 'downloading':
            # Получаем процент загрузки
            if 'total_bytes' in d and d['total_bytes'] > 0:
                percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.progress_var.set(percentage)
                
                downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                total_mb = d['total_bytes'] / (1024 * 1024)
                self.status_var.set(f"Загрузка: {percentage:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
            elif 'total_bytes_estimate' in d:
                percentage = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                self.progress_var.set(percentage)
                self.status_var.set(f"Загрузка: {percentage:.1f}%")
            else:
                self.status_var.set(f"Загрузка: {d.get('_percent_str', '0%').strip()}")
            
            # Показываем скорость
            if 'speed' in d and d['speed']:
                speed_mb = d['speed'] / (1024 * 1024)
                current_status = self.status_var.get()
                if "[MB/s]" not in current_status:
                    self.status_var.set(f"{current_status} [{speed_mb:.1f} MB/s]")
                
            self.root.update()
            
        elif d['status'] == 'finished':
            self.status_var.set("Обработка файла...")
            self.root.update()
    
    def download_selected(self):
        """Скачать выбранный формат"""
        selection = self.format_tree.selection()
        
        if not selection:
            messagebox.showwarning("Внимание", "Выберите формат для скачивания!")
            return
            
        if not self.video_info:
            messagebox.showwarning("Внимание", "Сначала получите информацию о видео!")
            return
        
        # Получаем индекс выбранного элемента
        item = self.format_tree.item(selection[0])
        values = item['values']
        if values[0] == "...":
            messagebox.showinfo("Информация", "Выберите конкретный формат из списка выше")
            return
            
        try:
            stream_index = int(values[0]) - 1
        except (ValueError, TypeError):
            messagebox.showerror("Ошибка", "Не удалось определить выбранный формат")
            return
        
        if stream_index >= len(self.formats_list):
            messagebox.showerror("Ошибка", "Неверный выбор формата!")
            return
        
        # Запускаем скачивание в отдельном потоке
        thread = threading.Thread(
            target=self.download_thread,
            args=(stream_index,),
            daemon=True
        )
        thread.start()
    
    def download_thread(self, stream_index):
        """Поток для скачивания с использованием yt-dlp"""
        try:
            selected = self.formats_list[stream_index]
            url = self.current_url  # Используем сохраненный URL
            
            # Создаем опции для загрузки
            ydl_opts = {
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.download_progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            # Если это аудио, настраиваем извлечение аудио
            if "Только аудио" in selected['type']:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                # Для видео используем выбранный формат
                format_id = selected.get('format_id')
                if format_id:
                    ydl_opts['format'] = format_id
                else:
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                
                # Добавляем постпроцессор для объединения видео и аудио
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            
            self.status_var.set(f"Начинаю загрузку...")
            self.progress_var.set(0)
            
            # Загружаем
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.status_var.set("Загрузка завершена!")
            self.progress_var.set(100)
            
            messagebox.showinfo("Успех", 
                              f"✅ Файл успешно скачан!\n\n"
                              f"Папка: {self.download_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при скачивании:\n{str(e)}\n\n"
                                          f"Убедитесь, что установлен FFmpeg для объединения видео и аудио.")
            self.status_var.set("Ошибка при скачивании")
            self.progress_var.set(0)
    
    def sanitize_filename(self, filename):
        """Очистка имени файла от недопустимых символов"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def clear_all(self):
        """Очистить все поля"""
        self.url_var.set("")
        self.current_url = ""  # Очищаем сохраненный URL
        self.info_text.config(state=NORMAL)
        self.info_text.delete(1.0, END)
        self.info_text.config(state=DISABLED)
        self.format_tree.delete(*self.format_tree.get_children())
        self.status_var.set("Готов к работе")
        self.progress_var.set(0)
        self.video_info = None
        self.formats_list = []
    
    def open_download_folder(self):
        """Открыть папку с загрузками"""
        try:
            if os.path.exists(self.download_path):
                if os.name == 'nt':  # Windows
                    os.startfile(self.download_path)
                elif os.name == 'posix':  # macOS, Linux
                    subprocess.run(['open', self.download_path] 
                                 if sys.platform == 'darwin' 
                                 else ['xdg-open', self.download_path])
            else:
                messagebox.showwarning("Внимание", "Папка не существует!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{str(e)}")

def main():
    """Запуск приложения"""
    root = Tk()
    
    # Устанавливаем размер окна перед полноэкранным режимом
    root.geometry("1200x800")
    
    app = YouTubeDownloaderGUI(root)
    
    root.mainloop()

if __name__ == "__main__":
    main()
