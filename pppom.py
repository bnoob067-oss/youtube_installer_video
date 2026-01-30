from tkinter import *
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
from datetime import datetime
import subprocess
import sys
from pytubefix import YouTube
from pytubefix.cli import on_progress

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Переменные
        self.url_var = StringVar()
        self.status_var = StringVar(value="Готов к работе")
        self.progress_var = DoubleVar(value=0)
        self.download_path = os.path.expanduser("~/Downloads")
        self.yt = None
        self.streams = []
        
        # Стили
        self.setup_styles()
        
        # Интерфейс
        self.setup_ui()
        
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
        # Главный фрейм
        main_frame = Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        title_frame = Frame(main_frame, bg=self.bg_color)
        title_frame.pack(fill=X, pady=(0, 20))
        
        Label(title_frame, text="🎬 YouTube Downloader Pro", 
              font=("Arial", 24, "bold"), 
              bg=self.bg_color, 
              fg=self.accent_color).pack()
        
        Label(title_frame, text="Скачивайте видео и аудио с YouTube", 
              font=("Arial", 12), 
              bg=self.bg_color, 
              fg=self.text_color).pack()
        
        # Фрейм для ввода URL
        url_frame = LabelFrame(main_frame, text=" Ссылка на видео ", 
                              font=("Arial", 11, "bold"),
                              bg=self.bg_color, 
                              fg=self.text_color,
                              relief=GROOVE, 
                              borderwidth=2)
        url_frame.pack(fill=X, pady=(0, 15))
        
        Entry(url_frame, textvariable=self.url_var, 
              font=("Arial", 11), 
              relief=SOLID, 
              borderwidth=1).pack(fill=X, padx=10, pady=10, ipady=5)
        
        # Кнопки для URL
        url_buttons_frame = Frame(url_frame, bg=self.bg_color)
        url_buttons_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        Button(url_buttons_frame, text="📋 Вставить из буфера", 
               command=self.paste_from_clipboard,
               bg="#e0e0e0",
               activebackground="#d0d0d0",
               relief=RAISED,
               font=("Arial", 10)).pack(side=LEFT, padx=5)
        
        Button(url_buttons_frame, text="🔍 Получить информацию", 
               command=self.get_video_info,
               bg=self.accent_color,
               fg="white",
               activebackground="#cc0000",
               relief=RAISED,
               font=("Arial", 10, "bold")).pack(side=RIGHT, padx=5)
        
        # Информация о видео
        self.info_frame = LabelFrame(main_frame, text=" Информация о видео ", 
                                    font=("Arial", 11, "bold"),
                                    bg=self.bg_color, 
                                    fg=self.text_color,
                                    relief=GROOVE, 
                                    borderwidth=2)
        self.info_frame.pack(fill=X, pady=(0, 15))
        
        self.info_text = scrolledtext.ScrolledText(self.info_frame, 
                                                   height=6, 
                                                   font=("Arial", 10),
                                                   wrap=WORD,
                                                   relief=SOLID,
                                                   borderwidth=1)
        self.info_text.pack(fill=X, padx=10, pady=10)
        self.info_text.config(state=DISABLED)
        
        # Выбор формата
        format_frame = LabelFrame(main_frame, text=" Выбор формата ", 
                                 font=("Arial", 11, "bold"),
                                 bg=self.bg_color, 
                                 fg=self.text_color,
                                 relief=GROOVE, 
                                 borderwidth=2)
        format_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # TreeView для форматов
        columns = ("#", "Тип", "Качество", "Формат", "Размер", "Кодек")
        self.format_tree = ttk.Treeview(format_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.format_tree.heading(col, text=col)
            self.format_tree.column(col, width=100, anchor="center")
        
        self.format_tree.column("#", width=50)
        self.format_tree.column("Тип", width=120)
        self.format_tree.column("Размер", width=80)
        
        scrollbar = ttk.Scrollbar(format_frame, orient=VERTICAL, command=self.format_tree.yview)
        self.format_tree.configure(yscrollcommand=scrollbar.set)
        
        self.format_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=RIGHT, fill=Y, padx=(0, 10), pady=10)
        
        # Панель загрузки
        download_frame = LabelFrame(main_frame, text=" Настройки загрузки ", 
                                   font=("Arial", 11, "bold"),
                                   bg=self.bg_color, 
                                   fg=self.text_color,
                                   relief=GROOVE, 
                                   borderwidth=2)
        download_frame.pack(fill=X, pady=(0, 15))
        
        # Выбор папки
        path_frame = Frame(download_frame, bg=self.bg_color)
        path_frame.pack(fill=X, padx=10, pady=10)
        
        Label(path_frame, text="Папка для сохранения:", 
              font=("Arial", 10), 
              bg=self.bg_color).pack(side=LEFT)
        
        self.path_label = Label(path_frame, text=self.download_path, 
                               font=("Arial", 10), 
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
               font=("Arial", 10)).pack(side=RIGHT)
        
        # Прогресс бар
        progress_frame = Frame(download_frame, bg=self.bg_color)
        progress_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var,
                                           maximum=100,
                                           length=400,
                                           mode='determinate')
        self.progress_bar.pack(fill=X, pady=(0, 5))
        
        self.status_label = Label(progress_frame, textvariable=self.status_var,
                                 font=("Arial", 10), 
                                 bg=self.bg_color,
                                 fg=self.text_color)
        self.status_label.pack()
        
        # Кнопки действий
        buttons_frame = Frame(main_frame, bg=self.bg_color)
        buttons_frame.pack(fill=X)
        
        Button(buttons_frame, text="⬇️  Скачать выбранное", 
               command=self.download_selected,
               bg="#4CAF50",
               fg="white",
               activebackground="#45a049",
               font=("Arial", 11, "bold"),
               height=2,
               width=20).pack(side=LEFT, padx=5)
        
        Button(buttons_frame, text="🔄 Очистить", 
               command=self.clear_all,
               bg="#2196F3",
               fg="white",
               activebackground="#1976D2",
               font=("Arial", 11),
               height=2,
               width=15).pack(side=LEFT, padx=5)
        
        Button(buttons_frame, text="📂 Открыть папку", 
               command=self.open_download_folder,
               bg="#FF9800",
               fg="white",
               activebackground="#F57C00",
               font=("Arial", 11),
               height=2,
               width=15).pack(side=LEFT, padx=5)
        
        Button(buttons_frame, text="❌ Выход", 
               command=self.root.quit,
               bg="#f44336",
               fg="white",
               activebackground="#d32f2f",
               font=("Arial", 11),
               height=2,
               width=10).pack(side=RIGHT, padx=5)
        
    def paste_from_clipboard(self):
        """Вставить URL из буфера обмена"""
        try:
            clipboard_text = self.root.clipboard_get()
            if "youtube.com" in clipboard_text or "youtu.be" in clipboard_text:
                self.url_var.set(clipboard_text)
                messagebox.showinfo("Успех", "Ссылка вставлена из буфера обмена!")
            else:
                messagebox.showwarning("Внимание", "В буфере обмена нет YouTube ссылки")
        except:
            messagebox.showerror("Ошибка", "Не удалось получить данные из буфера")
    
    def get_video_info(self):
        """Получить информацию о видео"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("Внимание", "Введите ссылку на видео!")
            return
            
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showwarning("Внимание", "Это не похоже на YouTube ссылку!")
            return
        
        # Очистка предыдущих данных
        self.format_tree.delete(*self.format_tree.get_children())
        self.info_text.config(state=NORMAL)
        self.info_text.delete(1.0, END)
        
        try:
            self.status_var.set("Получаю информацию о видео...")
            self.root.update()
            
            # Создаем YouTube объект
            self.yt = YouTube(url, on_progress_callback=self.on_progress)
            
            # Отображаем информацию
            info = f"""📺 Название: {self.yt.title}
👤 Автор: {self.yt.author}
⏱️  Длительность: {self.yt.length // 60}:{self.yt.length % 60:02d} минут
👁️  Просмотров: {self.yt.views:,}
📅 Дата публикации: {self.yt.publish_date}
"""
            
            self.info_text.insert(1.0, info)
            self.info_text.config(state=DISABLED)
            
            # Заполняем список форматов
            self.populate_formats()
            
            self.status_var.set("Информация получена. Выберите формат для скачивания")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить информацию:\n{str(e)}")
            self.status_var.set("Ошибка при получении информации")
    
    def populate_formats(self):
        """Заполнить список доступных форматов"""
        if not self.yt:
            return
            
        self.streams = []
        index = 1
        
        # Видео с аудио
        for stream in self.yt.streams.filter(progressive=True).order_by('resolution').desc():
            self.format_tree.insert("", "end", values=(
                index,
                "🎬 Видео+Аудио",
                stream.resolution,
                stream.mime_type.split('/')[1].upper(),
                f"{stream.filesize_mb:.1f} MB",
                stream.codecs[0].split('.')[0] if stream.codecs else "N/A"
            ))
            self.streams.append(stream)
            index += 1
        
        # Только аудио
        for stream in self.yt.streams.filter(only_audio=True).order_by('abr').desc():
            self.format_tree.insert("", "end", values=(
                index,
                "🎵 Только аудио",
                stream.abr,
                stream.mime_type.split('/')[1].upper(),
                f"{stream.filesize_mb:.1f} MB",
                stream.codecs[0] if stream.codecs else "N/A"
            ))
            self.streams.append(stream)
            index += 1
        
        # Только видео
        for stream in self.yt.streams.filter(adaptive=True, only_video=True).order_by('resolution').desc():
            self.format_tree.insert("", "end", values=(
                index,
                "🎞️ Только видео",
                stream.resolution,
                stream.mime_type.split('/')[1].upper(),
                f"{stream.filesize_mb:.1f} MB",
                stream.codecs[0].split('.')[0] if stream.codecs else "N/A"
            ))
            self.streams.append(stream)
            index += 1
    
    def select_folder(self):
        """Выбрать папку для сохранения"""
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=self.download_path
        )
        
        if folder:
            self.download_path = folder
            self.path_label.config(text=folder)
    
    def download_selected(self):
        """Скачать выбранный формат"""
        selection = self.format_tree.selection()
        
        if not selection:
            messagebox.showwarning("Внимание", "Выберите формат для скачивания!")
            return
            
        if not self.yt:
            messagebox.showwarning("Внимание", "Сначала получите информацию о видео!")
            return
        
        # Получаем индекс выбранного элемента
        item = self.format_tree.item(selection[0])
        values = item['values']
        stream_index = values[0] - 1  # Индекс в списке streams
        
        if stream_index >= len(self.streams):
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
        """Поток для скачивания"""
        try:
            selected_stream = self.streams[stream_index]
            
            # Очищаем имя файла
            safe_title = self.sanitize_filename(self.yt.title)
            
            # Определяем расширение файла
            extension = selected_stream.mime_type.split('/')[1]
            
            self.status_var.set(f"Скачивание: {safe_title}")
            self.progress_var.set(0)
            
            # Скачиваем
            selected_stream.download(
                output_path=self.download_path,
                filename=f"{safe_title}.{extension}"
            )
            
            self.status_var.set("Скачивание завершено!")
            self.progress_var.set(100)
            
            messagebox.showinfo("Успех", 
                              f"✅ Видео успешно скачано!\n\n"
                              f"Файл: {safe_title}.{extension}\n"
                              f"Папка: {self.download_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при скачивании:\n{str(e)}")
            self.status_var.set("Ошибка при скачивании")
            self.progress_var.set(0)
    
    def on_progress(self, stream, chunk, bytes_remaining):
        """Обработчик прогресса загрузки"""
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        
        self.progress_var.set(percentage)
        
        mb_downloaded = bytes_downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        
        self.status_var.set(f"Загрузка: {percentage:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)")
        self.root.update()
    
    def sanitize_filename(self, filename):
        """Очистка имени файла от недопустимых символов"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def clear_all(self):
        """Очистить все поля"""
        self.url_var.set("")
        self.info_text.config(state=NORMAL)
        self.info_text.delete(1.0, END)
        self.info_text.config(state=DISABLED)
        self.format_tree.delete(*self.format_tree.get_children())
        self.status_var.set("Готов к работе")
        self.progress_var.set(0)
        self.yt = None
        self.streams = []
    
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
    app = YouTubeDownloaderGUI(root)
    
    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main() 