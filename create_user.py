import os
import sys
import django
import tkinter as tk
from tkinter import ttk, messagebox

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stadium_booking.settings')
django.setup()

from django.contrib.auth.models import User
from booking.models import Profile


class UserCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("创建用户")
        self.root.geometry("480x520")
        self.root.resizable(False, False)

        self.center_window()

        self.primary_color = "#4F46E5"
        self.bg_color = "#F9FAFB"
        self.input_bg = "#FFFFFF"

        self.root.configure(bg=self.bg_color)

        self.setup_ui()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        title_frame = tk.Frame(self.root, bg=self.primary_color, height=60)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🏸 创建用户",
            font=("Microsoft YaHei", 16, "bold"),
            fg="white",
            bg=self.primary_color
        )
        title_label.pack(pady=15)

        form_frame = tk.Frame(self.root, bg=self.bg_color)
        form_frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(
            form_frame,
            text="用户名",
            font=("Microsoft YaHei", 10),
            fg="#374151",
            bg=self.bg_color
        ).pack(anchor="w", pady=(10, 5))

        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            form_frame,
            textvariable=self.username_var,
            font=("Microsoft YaHei", 11),
            bg=self.input_bg,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightcolor=self.primary_color
        )
        self.username_entry.pack(fill="x", ipady=8)

        tk.Label(
            form_frame,
            text="邮箱",
            font=("Microsoft YaHei", 10),
            fg="#374151",
            bg=self.bg_color
        ).pack(anchor="w", pady=(10, 5))

        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(
            form_frame,
            textvariable=self.email_var,
            font=("Microsoft YaHei", 11),
            bg=self.input_bg,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightcolor=self.primary_color
        )
        self.email_entry.pack(fill="x", ipady=8)

        tk.Label(
            form_frame,
            text="密码",
            font=("Microsoft YaHei", 10),
            fg="#374151",
            bg=self.bg_color
        ).pack(anchor="w", pady=(10, 5))

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            form_frame,
            textvariable=self.password_var,
            font=("Microsoft YaHei", 11),
            bg=self.input_bg,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightcolor=self.primary_color,
            show="*"
        )
        self.password_entry.pack(fill="x", ipady=8)

        tk.Label(
            form_frame,
            text="用户类型",
            font=("Microsoft YaHei", 10),
            fg="#374151",
            bg=self.bg_color
        ).pack(anchor="w", pady=(10, 5))

        self.user_type_var = tk.StringVar(value="regular")

        type_frame = tk.Frame(form_frame, bg=self.bg_color)
        type_frame.pack(fill="x")

        regular_radio = tk.Radiobutton(
            type_frame,
            text="普通用户",
            variable=self.user_type_var,
            value="regular",
            font=("Microsoft YaHei", 10),
            fg="#374151",
            bg=self.bg_color,
            activebackground=self.bg_color,
            command=self.update_button_text
        )
        regular_radio.pack(side="left", padx=(0, 30))

        admin_radio = tk.Radiobutton(
            type_frame,
            text="管理员",
            variable=self.user_type_var,
            value="admin",
            font=("Microsoft YaHei", 10),
            fg="#374151",
            bg=self.bg_color,
            activebackground=self.bg_color,
            command=self.update_button_text
        )
        admin_radio.pack(side="left", padx=(0, 30))

        super_admin_radio = tk.Radiobutton(
            type_frame,
            text="超级管理员",
            variable=self.user_type_var,
            value="super_admin",
            font=("Microsoft YaHei", 10),
            fg="#374151",
            bg=self.bg_color,
            activebackground=self.bg_color,
            command=self.update_button_text
        )
        super_admin_radio.pack(side="left")

        self.type_label = tk.Label(
            form_frame,
            text="✓ 可预约场地、查看预约",
            font=("Microsoft YaHei", 9),
            fg="#10B981",
            bg=self.bg_color
        )
        self.type_label.pack(anchor="w", pady=(5, 0))

        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill="x", padx=30, pady=(10, 20))

        self.create_btn = tk.Button(
            btn_frame,
            text="创建普通用户",
            font=("Microsoft YaHei", 11, "bold"),
            fg="white",
            bg=self.primary_color,
            activebackground="#4338CA",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            command=self.create_user
        )
        self.create_btn.pack(fill="x", ipady=10)

        cancel_btn = tk.Button(
            btn_frame,
            text="取消",
            font=("Microsoft YaHei", 10),
            fg="#6B7280",
            bg="white",
            activebackground="#F3F4F6",
            activeforeground="#374151",
            relief="solid",
            bd=1,
            cursor="hand2",
            command=self.root.destroy
        )
        cancel_btn.pack(fill="x", ipady=8, pady=(10, 0))

        self.root.bind('<Return>', lambda e: self.create_user())
        self.username_entry.focus()

    def update_button_text(self):
        user_type = self.user_type_var.get()
        if user_type == "super_admin":
            self.create_btn.config(text="创建超级管理员")
            self.type_label.config(text="✓ 拥有全部权限，可管理所有用户和系统设置", fg="#E74C3C")
        elif user_type == "admin":
            self.create_btn.config(text="创建管理员")
            self.type_label.config(text="✓ 可管理场地、设置时间段、管理预约", fg="#EF4444")
        else:
            self.create_btn.config(text="创建普通用户")
            self.type_label.config(text="✓ 可预约场地、查看预约", fg="#10B981")

    def create_user(self):
        username = self.username_var.get().strip()
        email = self.email_var.get().strip()
        password = self.password_var.get()
        user_type = self.user_type_var.get()

        if not username:
            messagebox.showwarning("提示", "请输入用户名")
            self.username_entry.focus()
            return

        if not password:
            messagebox.showwarning("提示", "请输入密码")
            self.password_entry.focus()
            return

        if len(password) < 6:
            messagebox.showwarning("提示", "密码长度至少为6位")
            self.password_entry.focus()
            return

        try:
            if User.objects.filter(username=username).exists():
                messagebox.showinfo("提示", f"用户 '{username}' 已存在")
                return

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                is_staff=(user_type in ("admin", "super_admin")),
                is_superuser=(user_type == "super_admin")
            )

            Profile.objects.create(
                user=user,
                user_type=user_type
            )

            if user_type == "super_admin":
                type_name = "超级管理员"
            elif user_type == "admin":
                type_name = "管理员"
            else:
                type_name = "普通用户"
            messagebox.showinfo("成功", f"用户创建成功！\n\n用户名: {username}\n用户类型: {type_name}\n密码: {password}")

            self.username_var.set("")
            self.email_var.set("")
            self.password_var.set("")
            self.user_type_var.set("regular")
            self.update_button_text()
            self.username_entry.focus()

        except Exception as e:
            messagebox.showerror("错误", f"创建失败：{str(e)}")


def main():
    root = tk.Tk()
    app = UserCreatorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
