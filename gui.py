"""
MMU Simulator GUI - with Config Editor and Pause/Resume
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from config_parser import parse_config, calculate_derived_values
from trace_parser import parse_trace
from frame_manager import FrameManager
from mmu import MMU
import threading


class MMUGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MMU Simulator")
        self.root.geometry("1200x750")
        self.root.configure(bg='#2c3e50')

        # Variables
        self.trace_file = tk.StringVar(value="trace_small.txt")
        self.config_file = tk.StringVar(value="config.txt")
        self.algorithm = tk.StringVar(value="FIFO")
        self.config = None
        self.all_addresses = []

        # Pause/Resume control variables
        self.is_running = False
        self.is_paused = False
        self.pause_condition = threading.Condition()
        self.simulation_thread = None

        self.setup_ui()

    def setup_ui(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#2c3e50')
        title_frame.pack(fill=tk.X, pady=10)

        title = tk.Label(title_frame, text="MMU Simulator",
                         font=("Arial", 18, "bold"), bg='#2c3e50', fg='white')
        title.pack()



        # Main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ===== LEFT PANEL (Controls) =====
        left_frame = tk.LabelFrame(main_frame, text="Controls",
                                   font=("Arial", 11, "bold"),
                                   bg='#34495e', fg='white',
                                   bd=2, relief=tk.GROOVE)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), ipadx=5, ipady=5)

        # Config file selection
        tk.Label(left_frame, text="Config File:", font=("Arial", 10),
                 bg='#34495e', fg='white').grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)

        config_entry = tk.Entry(left_frame, textvariable=self.config_file, width=20,
                                font=("Arial", 10), bg='white', fg='black')
        config_entry.grid(row=0, column=1, pady=5, padx=5)

        browse_config_btn = tk.Button(left_frame, text="Browse", command=self.browse_config_file,
                                      bg='#3498db', fg='white', font=("Arial", 9),
                                      relief=tk.RAISED, bd=1, padx=10)
        browse_config_btn.grid(row=0, column=2, padx=5)

        load_config_btn = tk.Button(left_frame, text="📁 Load Config", command=self.load_config,
                                    bg='#1abc9c', fg='white', font=("Arial", 9, "bold"),
                                    relief=tk.RAISED, bd=1, padx=10)
        load_config_btn.grid(row=0, column=3, padx=5)

        # Config editor button
        edit_config_btn = tk.Button(left_frame, text="✏️ Edit Config", command=self.open_config_editor,
                                    bg='#9b59b6', fg='white', font=("Arial", 9, "bold"),
                                    relief=tk.RAISED, bd=1, padx=10)
        edit_config_btn.grid(row=0, column=4, padx=5)

        # Trace file
        tk.Label(left_frame, text="Trace File:", font=("Arial", 10),
                 bg='#34495e', fg='white').grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)

        trace_entry = tk.Entry(left_frame, textvariable=self.trace_file, width=20,
                               font=("Arial", 10), bg='white', fg='black')
        trace_entry.grid(row=1, column=1, pady=5, padx=5)

        browse_trace_btn = tk.Button(left_frame, text="Browse", command=self.browse_trace_file,
                                     bg='#3498db', fg='white', font=("Arial", 9),
                                     relief=tk.RAISED, bd=1, padx=10)
        browse_trace_btn.grid(row=1, column=2, padx=5)

        # Algorithm selection
        tk.Label(left_frame, text="Algorithm:", font=("Arial", 10),
                 bg='#34495e', fg='white').grid(row=2, column=0, sticky=tk.W, pady=8, padx=5)

        algo_frame = tk.Frame(left_frame, bg='#34495e')
        algo_frame.grid(row=2, column=1, columnspan=4, sticky=tk.W, pady=8)

        self.fifo_btn = tk.Radiobutton(algo_frame, text="FIFO", variable=self.algorithm,
                                       value="FIFO", bg='#34495e', fg='white',
                                       font=("Arial", 10), selectcolor='#34495e')
        self.fifo_btn.pack(side=tk.LEFT)

        self.lru_btn = tk.Radiobutton(algo_frame, text="LRU", variable=self.algorithm,
                                      value="LRU", bg='#34495e', fg='white',
                                      font=("Arial", 10), selectcolor='#34495e')
        self.lru_btn.pack(side=tk.LEFT, padx=20)

        self.opt_btn = tk.Radiobutton(algo_frame, text="OPT", variable=self.algorithm,
                                      value="OPT", bg='#34495e', fg='white',
                                      font=("Arial", 10), selectcolor='#34495e')
        self.opt_btn.pack(side=tk.LEFT)

        # Control buttons frame
        control_frame = tk.Frame(left_frame, bg='#34495e')
        control_frame.grid(row=3, column=0, columnspan=5, pady=10, padx=5)

        # Run button
        self.run_btn = tk.Button(control_frame, text="▶ RUN SIMULATION", command=self.run_simulation,
                                 bg='#27ae60', fg='white', font=("Arial", 11, "bold"),
                                 relief=tk.RAISED, bd=2, padx=15, pady=5, cursor="hand2")
        self.run_btn.pack(side=tk.LEFT, padx=5)

        # Pause button
        self.pause_btn = tk.Button(control_frame, text="⏸ PAUSE", command=self.pause_simulation,
                                   bg='#f39c12', fg='white', font=("Arial", 10, "bold"),
                                   relief=tk.RAISED, bd=2, padx=15, pady=5, cursor="hand2",
                                   state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        # Resume button
        self.resume_btn = tk.Button(control_frame, text="▶ RESUME", command=self.resume_simulation,
                                    bg='#2980b9', fg='white', font=("Arial", 10, "bold"),
                                    relief=tk.RAISED, bd=2, padx=15, pady=5, cursor="hand2",
                                    state=tk.DISABLED)
        self.resume_btn.pack(side=tk.LEFT, padx=5)

        # Stop button
        self.stop_btn = tk.Button(control_frame, text="⏹ STOP", command=self.stop_simulation,
                                  bg='#e74c3c', fg='white', font=("Arial", 10, "bold"),
                                  relief=tk.RAISED, bd=2, padx=15, pady=5, cursor="hand2",
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Separator
        separator = tk.Frame(left_frame, height=2, bg='#2c3e50')
        separator.grid(row=4, column=0, columnspan=5, sticky=tk.EW, pady=10, padx=5)

        # Config display
        tk.Label(left_frame, text="System Configuration:", font=("Arial", 11, "bold"),
                 bg='#34495e', fg='white').grid(row=5, column=0, columnspan=5, sticky=tk.W, pady=(10, 5), padx=5)

        self.config_text = tk.Text(left_frame, width=40, height=14,
                                   font=("Courier", 9), bg='white', fg='#2c3e50',
                                   relief=tk.SUNKEN, bd=1, state=tk.DISABLED)
        self.config_text.grid(row=6, column=0, columnspan=5, pady=5, padx=5)

        # Progress section
        tk.Label(left_frame, text="Progress:", font=("Arial", 10),
                 bg='#34495e', fg='white').grid(row=7, column=0, columnspan=5, sticky=tk.W, pady=(10, 5), padx=5)

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var,
                                            maximum=100, length=280)
        self.progress_bar.grid(row=8, column=0, columnspan=5, pady=5, padx=5)

        self.progress_label = tk.Label(left_frame, text="0%", font=("Arial", 9),
                                       bg='#34495e', fg='white')
        self.progress_label.grid(row=9, column=0, columnspan=5, pady=(0, 10))

        # ===== RIGHT PANEL (Output) =====
        right_frame = tk.LabelFrame(main_frame, text="Simulation Output",
                                    font=("Arial", 11, "bold"),
                                    bg='#34495e', fg='white',
                                    bd=2, relief=tk.GROOVE)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, ipadx=5, ipady=5)

        self.output_text = scrolledtext.ScrolledText(right_frame, width=70, height=35,
                                                     font=("Courier", 9),
                                                     bg='white', fg='black',
                                                     relief=tk.SUNKEN, bd=1)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status bar at bottom
        self.status_bar = tk.Label(self.root, text="Ready", relief=tk.SUNKEN,
                                   anchor=tk.W, bg='#34495e', fg='white',
                                   font=("Arial", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Load initial config
        self.load_config()

    def browse_config_file(self):
        filename = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.config_file.set(filename)
            self.load_config()

    def browse_trace_file(self):
        filename = filedialog.askopenfilename(
            title="Select Trace File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.trace_file.set(filename)

    def open_config_editor(self):
        """Open a new window to edit config file"""
        editor_window = tk.Toplevel(self.root)
        editor_window.title("Config File Editor")
        editor_window.geometry("500x600")
        editor_window.configure(bg='#34495e')

        tk.Label(editor_window, text="Edit Configuration File", font=("Arial", 14, "bold"),
                 bg='#34495e', fg='white').pack(pady=10)

        # Text area for editing
        text_frame = tk.Frame(editor_window, bg='#34495e')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.config_editor = scrolledtext.ScrolledText(text_frame, width=60, height=25,
                                                        font=("Courier", 10), bg='white', fg='black')
        self.config_editor.pack(fill=tk.BOTH, expand=True)

        # Load current config file content
        try:
            with open(self.config_file.get(), 'r') as f:
                content = f.read()
                self.config_editor.insert(tk.END, content)
        except Exception as e:
            self.config_editor.insert(tk.END, f"# Error loading file: {e}\n")

        # Buttons frame
        btn_frame = tk.Frame(editor_window, bg='#34495e')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_config():
            try:
                new_content = self.config_editor.get(1.0, tk.END)
                with open(self.config_file.get(), 'w') as f:
                    f.write(new_content)
                messagebox.showinfo("Success", "Config file saved!")
                self.load_config()  # Reload config immediately
                editor_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        def reload_and_close():
            self.load_config()
            editor_window.destroy()

        tk.Button(btn_frame, text="💾 Save & Reload", command=save_config,
                  bg='#27ae60', fg='white', font=("Arial", 10, "bold"),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="❌ Cancel", command=reload_and_close,
                  bg='#e74c3c', fg='white', font=("Arial", 10),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def log(self, message):
        """Add message to output window"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def update_status(self, message):
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def update_progress(self, current, total):
        percent = int((current / total) * 100)
        self.progress_var.set(percent)
        self.progress_label.config(text=f"{percent}%")
        self.root.update_idletasks()

    def load_config(self):
        try:
            config = parse_config(self.config_file.get())
            config = calculate_derived_values(config)
            self.config = config

            self.config_text.config(state=tk.NORMAL)
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(tk.END, f"Config File: {self.config_file.get()}\n")
            self.config_text.insert(tk.END, "-" * 35 + "\n")
            self.config_text.insert(tk.END, f"RAM Size: {config.ram_size_kb} KB\n")
            self.config_text.insert(tk.END, f"Page Size: {config.page_size_bytes} B\n")
            self.config_text.insert(tk.END, f"Total Frames: {config.num_frames}\n")
            self.config_text.insert(tk.END, f"TLB Size: {config.tlb_size}\n")
            self.config_text.insert(tk.END, f"TLB Latency: {config.tlb_latency_ns} ns\n")
            self.config_text.insert(tk.END, f"RAM Latency: {config.ram_latency_ns} ns\n")
            self.config_text.insert(tk.END, f"Disk Latency: {config.disk_latency_ns} ns\n")
            self.config_text.insert(tk.END, f"Offset Bits: {config.offset_bits}\n")
            self.config_text.insert(tk.END, f"Offset Mask: 0x{config.offset_mask:X}\n")
            self.config_text.config(state=tk.DISABLED)
            self.update_status(f"Config loaded from {self.config_file.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            self.update_status("Error loading config")

    def load_trace(self):
        try:
            accesses = parse_trace(self.trace_file.get())
            self.all_addresses = [acc.address for acc in accesses]
            self.update_status(f"Loaded {len(accesses)} memory accesses")
            return accesses
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load trace: {e}")
            self.update_status("Error loading trace")
            return None

    def run_simulation(self):
        if self.config is None:
            messagebox.showerror("Error", "Config not loaded!")
            return

        if self.is_running:
            messagebox.showwarning("Warning", "Simulation already running!")
            return

        self.clear_output()
        self.update_status("Loading...")

        accesses = self.load_trace()
        if not accesses:
            return

        self.total_instructions = len(accesses)

        self.run_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)

        self.is_running = True
        self.is_paused = False

        self.simulation_thread = threading.Thread(
            target=self._run_simulation_thread,
            args=(accesses,)
        )
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def pause_simulation(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.update_status("⏸ PAUSED")
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.NORMAL)
            self.log("\n⏸ SIMULATION PAUSED - Click RESUME to continue\n")

    def resume_simulation(self):
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.update_status("Resuming...")
            self.pause_btn.config(state=tk.NORMAL)
            self.resume_btn.config(state=tk.DISABLED)
            self.log("\n▶ SIMULATION RESUMED\n")

            with self.pause_condition:
                self.pause_condition.notify()

    def stop_simulation(self):
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.update_status("Stopping simulation...")
            self.log("\n⏹ SIMULATION STOPPED BY USER\n")

            self.run_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress_var.set(0)
            self.progress_label.config(text="0%")

    def _run_simulation_thread(self, accesses):
        try:
            self.log("=" * 60)
            self.log("RUNNING SIMULATION")
            self.log("=" * 60)

            fm = FrameManager(self.config.num_frames)
            algo = self.algorithm.get()

            self.log(f"\nAlgorithm: {algo}")
            self.log(f"Total instructions: {len(accesses)}")

            if algo == "OPT":
                mmu = MMU(self.config, fm, algorithm=algo, trace_addresses=self.all_addresses)
            else:
                mmu = MMU(self.config, fm, algorithm=algo)

            for i, acc in enumerate(accesses):
                if not self.is_running:
                    self.log("\n❌ SIMULATION STOPPED")
                    break

                if self.is_paused:
                    with self.pause_condition:
                        self.pause_condition.wait()
                    if not self.is_running:
                        break

                phys_addr, latency, summary = mmu.translate(acc.address, acc.is_write)

                self.update_progress(i + 1, len(accesses))

                self.log(
                    f"\nAccess {i + 1}/{len(accesses)}: {hex(acc.address)} ({'WRITE' if acc.is_write else 'READ'})")
                self.log(f"  {summary}")
                self.log(f"  Physical: {hex(phys_addr)} | Latency: {latency:,} ns")

            if self.is_running:
                mmu.print_stats()
                stats = mmu.get_stats()
                self.log("\n" + "=" * 60)
                self.log("FINAL STATISTICS")
                self.log("=" * 60)
                self.log(f"Total Accesses:     {stats['total_accesses']}")
                self.log(f"TLB Hits:           {stats['tlb_hits']}")
                self.log(f"TLB Misses:         {stats['tlb_misses']}")
                self.log(f"TLB Hit Rate:       {stats['tlb_hit_rate']:.2%}")
                self.log(f"Page Faults:        {stats['page_faults']}")
                self.log(f"Page Fault Rate:    {stats['page_fault_rate']:.2%}")
                self.log(f"Disk Reads:         {stats['disk_reads']}")
                self.log(f"Disk Writes:        {stats['disk_writes']}")
                self.log(f"Total Time:         {stats['total_latency_ns']:,.0f} ns")
                self.log(f"Average Time:       {stats['avg_latency_ns']:.0f} ns")
                self.log(f"EAT (Theoretical):  {stats['eat_ns']:.2f} ns")
                self.log("=" * 60)
                self.log("\n✅ SIMULATION COMPLETE!")
                self.update_status("Simulation complete")

        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.update_status(f"Error: {e}")
        finally:
            self.is_running = False
            self.is_paused = False
            self.run_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress_bar.stop()


def main():
    root = tk.Tk()
    app = MMUGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()