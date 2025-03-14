import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk
import fitz  # PyMuPDF for PDFs
import os
from datetime import datetime
import json


class ImagePDFQuizApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image/PDF Quiz App")
        self.master.geometry("900x700")
        self.master.configure(bg='#e0f7fa')  # Set background color to a light cyan

        self.time_left = 30 * 60  # Default 30 mins
        self.sections = ['Section 1', 'Section 2', 'Section 3']
        self.files = {section: [] for section in self.sections}
        self.current_index = {section: 0 for section in self.sections}
        self.current_page = {section: 0 for section in self.sections}
        self.marked_for_review = {section: [] for section in self.sections}
        self.answers = {section: {} for section in self.sections}
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.pdf_cache = {}  # To store loaded PDFs as images

        self.setup_gui()
    
    def on_closing(self):
      self.cleanup_temp_files()
      self.master.destroy()

    def setup_gui(self):
        # Create a frame for the top bar
        top_bar = tk.Frame(self.master, bg='#e0f7fa')
        top_bar.pack(side=tk.TOP, fill=tk.X)

        # Create a Notebook
        self.notebook = ttk.Notebook(top_bar)
        self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create tabs for each section
        self.frames = {}
        for section in self.sections:
            frame = tk.Frame(self.notebook, bg='#e0f7fa')
            self.notebook.add(frame, text=section)
            self.frames[section] = frame
            self.setup_section_gui(frame, section)

        # Add Help tab to the notebook
        help_frame = tk.Frame(self.notebook, bg='#e0f7fa')
        self.notebook.add(help_frame, text="Help")
        self.setup_help_tab(help_frame)

        # Create a menu bar
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)

        # Create a dropdown menu for session
        session_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Session", menu=session_menu)
        session_menu.add_command(label="Save Session", command=self.save_session)
        session_menu.add_command(label="Load Session", command=self.load_session)

    def setup_help_tab(self, frame):
        help_text = (
    "📖 Welcome to the Image/PDF Quiz App!\n\n"
    "Key Features & How to Use:\n\n"
    "1. Sections & Tabs: Quiz is divided into sections (Section 1, Section 2, Section 3). Switch via tabs on top. "
    "You can rename them using 'Edit Sections'.\n\n"
    "2. Uploading Questions: Click 'Upload Questions (Images/PDFs)' to add JPG, PNG, or PDFs "
    "(up to 100 MB each). PDFs are paginated automatically.\n\n"
    "3. Navigation: Use 'Previous'/'Next' to move between questions. For PDFs, use 'Previous Page'/'Next Page'.\n\n"
    "4. Answering: Type answers in 'Your Answer (optional)' box. Answers auto-save when navigating.\n\n"
    "5. Mark for Review: Flag questions to revisit using 'Mark for Review'.\n\n"
    "6. Question Panel: Right-side numbered buttons indicate status:\n"
    "   - Grey: Not visited\n"
    "   - Red: Not answered\n"
    "   - Green: Answered\n"
    "   - Purple: Marked for review\n"
    "   - Purple with ✓: Answered and marked for review\n\n"
    "7. Timer: Start countdown using 'Start Timer' (in minutes). Auto-submit when time is up.\n\n"
    "8. Submit: Click 'Submit' to save all answers (organized by section and question) in a text file.\n\n"
    "✅ Tips: Focus on attempting all questions. Review marked questions before final submission.\n\n"
    "Good luck with your quiz! 🚀"
)


        help_label = tk.Label(frame, text=help_text, bg='#e0f7fa', fg='black', justify=tk.LEFT, wraplength=800)
        help_label.pack(padx=10, pady=10)

    def setup_section_gui(self, frame, section):
        # Create a PanedWindow
        paned_window = tk.PanedWindow(frame, orient=tk.HORIZONTAL, bg='#e0f7fa')
        paned_window.pack(fill=tk.BOTH, expand=1)

        # Left panel for main content
        left_panel = tk.Frame(paned_window, bg='#e0f7fa')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Right panel for questions
        right_panel = tk.Frame(paned_window, width=200, bg='#e0f7fa')
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Timer
        timer_label = tk.Label(left_panel, font=("Arial", 14), fg="red", bg='#e0f7fa')
        timer_label.pack(pady=10)

        # Display area
        canvas_frame = tk.Frame(left_panel, bg='#e0f7fa')
        canvas_frame.pack(expand=True)
        canvas = tk.Canvas(canvas_frame, width=600, height=310, bg='#ffffff', highlightbackground='#cccccc')  # White background for images
        canvas.pack(expand=True, fill=tk.BOTH)

        # Answer entry with scrollbar
        tk.Label(left_panel, text="Your Answer (optional):", bg='#e0f7fa', fg='black').pack()
        answer_frame = tk.Frame(left_panel, bg='#e0f7fa')
        answer_frame.pack(pady=5)
        answer_entry = tk.Text(answer_frame, height=1, width=40, fg='black')
        answer_entry.pack(side=tk.LEFT)
        answer_scroll = tk.Scrollbar(answer_frame, command=answer_entry.yview)
        answer_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        answer_entry.config(yscrollcommand=answer_scroll.set)

        # Navigation buttons
        nav_frame = tk.Frame(left_panel, bg='#e0f7fa')
        nav_frame.pack(pady=10)

        ttk.Style().configure("TButton", padding=6, relief="flat", background="#4db6e4", foreground="black")

        ttk.Button(nav_frame, text="Previous", command=lambda: self.prev_question(section)).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(nav_frame, text="Next", command=lambda: self.next_question(section)).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(nav_frame, text="Mark for Review", command=lambda: self.mark_for_review(section)).grid(row=0, column=2, padx=5, pady=5)

        # PDF navigation buttons
        pdf_nav_frame = tk.Frame(left_panel, bg='#e0f7fa')
        pdf_nav_frame.pack(pady=10)

        ttk.Button(pdf_nav_frame, text="Previous Page", command=lambda: self.prev_page(section)).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(pdf_nav_frame, text="Next Page", command=lambda: self.next_page(section)).grid(row=0, column=1, padx=5, pady=5)

        # Load files button
        ttk.Button(left_panel, text="Upload Questions (Images/PDFs)", command=lambda: self.load_files(section)).pack(pady=10)

        # Start Timer, Edit Sections, and Submit buttons
        button_frame = tk.Frame(left_panel, bg='#e0f7fa')
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Start Timer", command=self.start_timer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Sections", command=self.edit_sections).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Submit", command=self.submit).pack(side=tk.LEFT, padx=5)

        # Question panel content
        question_buttons_frame = tk.Frame(right_panel, bg='#e0f7fa')
        question_buttons_frame.pack(expand=True)

        # Store references to widgets
        self.__dict__.update({
            f'{section}_timer_label': timer_label,
            f'{section}_canvas': canvas,
            f'{section}_answer_entry': answer_entry,
            f'{section}_pdf_nav_frame': pdf_nav_frame,
            f'{section}_question_buttons_frame': question_buttons_frame,
        })

    def edit_sections(self):
        sections = simpledialog.askstring("Edit Sections", "Enter section names separated by commas:", initialvalue=", ".join(self.sections))
        if sections:
            self.sections = [section.strip() for section in sections.split(",")]
            self.files = {section: [] for section in self.sections}
            self.current_index = {section: 0 for section in self.sections}
            self.current_page = {section: 0 for section in self.sections}
            self.marked_for_review = {section: [] for section in self.sections}
            self.answers = {section: {} for section in self.sections}
            self.pdf_cache = {}
            for frame in self.frames.values():
                frame.destroy()
            self.frames = {}
            for section in self.sections:
                frame = tk.Frame(self.notebook, bg='#e0f7fa')
                self.notebook.add(frame, text=section)
                self.frames[section] = frame
                self.setup_section_gui(frame, section)

    def load_files(self, section):
        filetypes = [("Image/PDF files", "*.jpg *.jpeg *.png *.pdf")]
        files = filedialog.askopenfilenames(title="Select Question Files", filetypes=filetypes)
        if files:
            self.files[section] = list(files)
            self.marked_for_review[section] = [False] * len(self.files[section])
            self.current_index[section] = 0
            self.current_page[section] = 0
            self.load_question(section)
            self.update_question_buttons(section)

    def update_question_buttons(self, section):
        frame = self.__dict__[f'{section}_question_buttons_frame']
        for widget in frame.winfo_children():
            widget.destroy()
        for idx, file in enumerate(self.files[section]):
            button_text = f"{idx + 1}"
            if self.marked_for_review[section][idx]:
                if self.answers[section].get(idx):
                    button_text += " ✔"
                    button_color = "purple"
                else:
                    button_color = "purple"
            elif self.answers[section].get(idx):
                button_color = "green"
            else:
                button_color = "red" if self.answers[section].get(idx) == "" else "grey"
            borderwidth = 2 if idx == self.current_index[section] else 0
            button = tk.Button(frame, text=button_text, width=3, bg=button_color, command=lambda idx=idx: self.select_question(section, idx), highlightbackground="black", highlightthickness=borderwidth)
            row = idx // 4
            col = idx % 4
            button.grid(row=row, column=col, padx=5, pady=5)

        # Add a black border around the question buttons frame
        frame.config(highlightbackground="black", highlightthickness=2)

    def select_question(self, section, index):
        self.current_index[section] = index
        self.current_page[section] = 0
        self.load_question(section)

    def load_question(self, section):
        if not self.files[section]:
            return

        file_path = self.files[section][self.current_index[section]]
        ext = os.path.splitext(file_path)[1].lower()

        answer_entry = self.__dict__[f'{section}_answer_entry']
        answer_entry.delete("1.0", tk.END)
        existing_answer = self.answers[section].get(self.current_index[section], "")
        answer_entry.insert(tk.END, existing_answer)

        if ext == ".pdf":
            self.__dict__[f'{section}_pdf_nav_frame'].pack(pady=10)
            if file_path not in self.pdf_cache:
                self.pdf_cache[file_path] = fitz.open(file_path)
            doc = self.pdf_cache[file_path]
            if self.current_page[section] >= len(doc):
                self.current_page[section] = len(doc) - 1
            elif self.current_page[section] < 0:
                self.current_page[section] = 0
            page = doc.load_page(self.current_page[section])
            pix = page.get_pixmap()
            image_path = f"_temp_{section}_{self.current_index[section]}_{self.current_page[section]}.png"
            pix.save(image_path)
        else:
            self.__dict__[f'{section}_pdf_nav_frame'].pack_forget()
            image_path = file_path

        try:
            img = Image.open(image_path)
            img.thumbnail((500, 300))  # Reduced height by 30 pixels
            img_tk = ImageTk.PhotoImage(img)
            canvas = self.__dict__[f'{section}_canvas']
            canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            canvas.image = img_tk
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load file: {file_path}\n{e}")

        self.update_question_buttons(section)

    def next_question(self, section):
        self.save_answer(section)
        if self.current_index[section] < len(self.files[section]) - 1:
            self.current_index[section] += 1
            self.current_page[section] = 0
            self.load_question(section)

    def prev_question(self, section):
        self.save_answer(section)
        if self.current_index[section] > 0:
            self.current_index[section] -= 1
            self.current_page[section] = 0
            self.load_question(section)

    def next_page(self, section):
        self.current_page[section] += 1
        self.load_question(section)

    def prev_page(self, section):
        self.current_page[section] -= 1
        self.load_question(section)

    def mark_for_review(self, section):
        self.marked_for_review[section][self.current_index[section]] = True
        self.update_question_buttons(section)
        messagebox.showinfo("Marked", "Question marked for review.")

    def save_answer(self, section):
        answer = self.__dict__[f'{section}_answer_entry'].get("1.0", tk.END).strip()
        self.answers[section][self.current_index[section]] = answer
        self.update_question_buttons(section)

    def start_timer(self):
        time_input = tk.simpledialog.askinteger("Timer", "Enter time in minutes:", minvalue=1, maxvalue=180)
        if time_input:
            self.time_left = time_input * 60
            self.update_timer()

    def update_timer(self):
        mins, secs = divmod(self.time_left, 60)
        for section in self.sections:
            self.__dict__[f'{section}_timer_label'].config(text=f"Time Left: {mins:02d}:{secs:02d}")
        if self.time_left > 0:
            self.time_left -= 1
            self.master.after(1000, self.update_timer)
        else:
            self.auto_submit()

    def auto_submit(self):
        messagebox.showinfo("Time's up!", "Time is over. Auto-submitting your answers.")
        self.submit()

    def submit(self):
       if messagebox.askyesno("Submit", "Are you sure you want to submit your answers?"):
        for section in self.sections:
            self.save_answer(section)
        filename = f"responses_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        with open(filename, "w", encoding='utf-8') as file:
            for section in self.sections:
                file.write(f"--- {section} ---\n")
                for idx, answer in self.answers[section].items():
                    file.write(f"Q{idx + 1}: {answer}\n")
                file.write("\n")
        messagebox.showinfo("Submitted", f"Your responses have been saved as '{filename}'.")


    def save_session(self):
        # Save current answers before saving session
        for section in self.sections:
            self.save_answer(section)
        
        session_data = {
            'sections': self.sections,
            'files': self.files,
            'current_index': self.current_index,
            'current_page': self.current_page,
            'marked_for_review': self.marked_for_review,
            'answers': self.answers,
            'time_left': self.time_left,
        }
        file_path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON files', '*.json')])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(session_data, f)
            messagebox.showinfo("Saved", "Session saved successfully.")


    def cleanup_temp_files(self):
      for file in os.listdir():
        if file.startswith("_temp_") and file.endswith(".png"):
            try:
                os.remove(file)
            except Exception as e:
                print(f"Failed to delete {file}: {e}")


    def load_session(self):
        file_path = filedialog.askopenfilename(filetypes=[('JSON files', '*.json')])
        if file_path:
            with open(file_path, 'r') as f:
                session_data = json.load(f)
            self.sections = session_data['sections']
            self.files = session_data['files']
            self.current_index = session_data['current_index']
            self.current_page = session_data['current_page']
            self.marked_for_review = session_data['marked_for_review']
            self.answers = session_data['answers']
            self.time_left = session_data['time_left']
            for frame in self.frames.values():
                frame.destroy()
            self.frames = {}
            for section in self.sections:
                frame = tk.Frame(self.notebook, bg='#e0f7fa')
                self.notebook.add(frame, text=section)
                self.frames[section] = frame
                self.setup_section_gui(frame, section)
            self.update_timer()
            messagebox.showinfo("Loaded", "Session loaded successfully.")


# Run App
if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePDFQuizApp(root)
    root.mainloop()
