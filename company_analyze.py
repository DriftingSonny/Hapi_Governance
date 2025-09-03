import tkinter as tk
from tkinter import ttk, scrolledtext, font
import configparser
import json
import os

class CompanyAnalyzer:
    def __init__(self, root):
        # 设置中文字体支持
        self.root = root
        self.root.title("哈气治国-公司分析器")
        self.root.geometry("1000x700")

        # 确保中文显示正常
        self.style = ttk.Style()

        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 分割窗口
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 左侧公司列表框架
        self.left_frame = ttk.LabelFrame(
            self.paned_window, text="公司列表", padding="10"
        )
        self.paned_window.add(self.left_frame, weight=1)

        # 右侧信息显示框架
        self.right_frame = ttk.LabelFrame(
            self.paned_window, text="公司信息汇总", padding="10"
        )
        self.paned_window.add(self.right_frame, weight=2)

        # 创建滚动条和公司列表
        self.create_company_list()

        # 创建信息显示区域
        self.create_info_display()

        # 读取公司数据
        self.read_company_data()

        # 添加公司到列表
        self.populate_company_list()

    def create_company_list(self):
        """创建公司列表、滚动条和搜索框"""
        # 搜索框和清除按钮 - 顶置
        self.search_frame = ttk.Frame(self.left_frame)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)

        # 搜索框容器
        self.search_container = ttk.Frame(self.search_frame)
        self.search_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_container.grid_propagate(False)

        # 搜索框
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self.search_container, textvariable=self.search_var, width=30
        )
        self.search_entry.pack(fill=tk.X, expand=True, ipady=3)
        self.search_var.trace_add("write", self.on_search_change)

        # 内嵌清除按钮
        self.clear_button = ttk.Button(
            self.search_container, text="×", command=self.clear_search, width=2
        )
        self.clear_button.place(relx=1.0, rely=0.5, anchor="e", x=-5, y=0)
        self.clear_button.bind(
            "<Enter>", lambda e: self.clear_button.configure(style="Accent.TButton")
        )
        self.clear_button.bind(
            "<Leave>", lambda e: self.clear_button.configure(style="TButton")
        )

        # 搜索提示标签
        self.search_hint = ttk.Label(
            self.search_frame, text="输入关键词搜索公司信息", font=("SimHei", 9)
        )
        self.search_hint.place(relx=0.05, rely=0.5, anchor="w")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_hint.place_forget())
        self.search_entry.bind("<FocusOut>", lambda e: self._show_search_hint())

        # 创建滚动条
        self.scrollbar = ttk.Scrollbar(self.left_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建Canvas来放置公司列表，支持滚动
        self.canvas = tk.Canvas(self.left_frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.canvas.yview)

        # 创建框架来放置复选框
        self.checkbox_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window(
            (0, 0), window=self.checkbox_frame, anchor="nw"
        )

        # 绑定事件，当框架大小改变时更新Canvas的滚动区域
        self.checkbox_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # 这将通过鼠标位置判断来处理不同区域的滚动
        self.root.bind_all("<MouseWheel>", self._on_mousewheel_global)

        # 存储复选框和标签的变量
        self.check_vars = {}
        self.company_frames = {}
        self.company_info_widgets = {}

        # 创建表头
        header_frame = ttk.Frame(self.checkbox_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header_frame, text="选择", font=("SimHei", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=5
        )
        ttk.Label(header_frame, text="公司信息", font=("SimHei", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=5
        )

    def _on_mousewheel_global(self, event):
        """全局鼠标滚轮事件处理，根据鼠标位置决定滚动哪个区域"""
        # 获取鼠标位置
        x, y = self.root.winfo_pointerxy()
        
        # 检查鼠标是否在左侧Canvas区域
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # 检查鼠标是否在右侧文本区域
        text_x = self.info_text.winfo_rootx()
        text_y = self.info_text.winfo_rooty()
        text_width = self.info_text.winfo_width()
        text_height = self.info_text.winfo_height()
        
        # 如果鼠标在左侧Canvas区域，滚动左侧列表
        if (canvas_x <= x < canvas_x + canvas_width and 
            canvas_y <= y < canvas_y + canvas_height):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            # 返回break阻止事件冒泡到其他组件
            return "break"
        # 如果鼠标在右侧文本区域，滚动右侧信息汇总
        elif (text_x <= x < text_x + text_width and 
              text_y <= y < text_y + text_height):
            self.info_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            # 返回break阻止事件冒泡到其他组件
            return "break"
        
        # 如果鼠标不在任何滚动区域，让事件正常传播
        return None

    def create_info_display(self):
        """创建信息显示区域"""
        # 创建标签和文本框
        self.info_text = scrolledtext.ScrolledText(
            self.right_frame, wrap=tk.WORD, width=60, height=30
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.config(state=tk.DISABLED)
    
    def read_company_data(self):
        """从INI文件读取公司数据"""
        self.company_data = {}
        # 使用RawConfigParser来避免百分号插值问题
        self.config = configparser.RawConfigParser()

        # 读取文件
        try:
            ini_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "company.ini"
            )
            self.config.read(ini_path, encoding="utf-8")

            # 解析每个公司的数据
            for section in self.config.sections():
                company_info = {}

                for key, value in self.config[section].items():
                    # 处理数组类型的值
                    if value.startswith("[") and value.endswith("]"):
                        try:
                            # 解析JSON数组
                            company_info[key] = json.loads(value)
                        except json.JSONDecodeError:
                            # 如果解析失败，保留原始值
                            company_info[key] = value
                    # 处理布尔值
                    elif value.lower() == "true":
                        company_info[key] = True
                    elif value.lower() == "false":
                        company_info[key] = False
                    # 处理NULL值
                    elif value.upper() == "NULL":
                        company_info[key] = None
                    # 处理字符串值
                    elif value.startswith('"') and value.endswith('"'):
                        company_info[key] = value[1:-1]
                    else:
                        company_info[key] = value

                self.company_data[section] = company_info
        except Exception as e:
            # 显示错误信息
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"读取文件出错: {str(e)}")
            self.info_text.config(state=tk.DISABLED)

    def populate_company_list(self):
        """将公司添加到列表中，每个公司显示五行信息"""
        # 清空现有组件
        for frame in self.company_frames.values():
            frame.destroy()
        self.check_vars.clear()
        self.company_frames.clear()
        self.company_info_widgets.clear()

        # 添加新的公司项
        for company in sorted(self.company_data.keys()):
            # 创建公司框架
            company_frame = ttk.Frame(self.checkbox_frame)
            company_frame.pack(fill=tk.X, padx=5, pady=5)

            # 获取公司信息
            company_info = self.company_data.get(company, {})

            # 创建复选框
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(
                company_frame,
                text="",
                variable=var,
                command=lambda c=company: self.on_company_select(c),
            )
            chk.grid(row=0, column=0, sticky="wn", padx=5, rowspan=5)

            # 创建信息显示框架
            info_frame = ttk.Frame(company_frame)
            info_frame.grid(row=0, column=1, sticky="w", padx=5, columnspan=3)

            # 第一行：公司名称
            company_label = ttk.Label(
                info_frame, text=company, font=("SimHei", 10, "bold"), width=30
            )
            company_label.grid(row=0, column=0, sticky="w", pady=2)

            # 第二行：科技、地块和名贵信息
            tech_info = company_info.get("科技", "NULL")
            tech_text = (
                f"科技: {tech_info}"
                if tech_info and tech_info != "NULL" and tech_info != "None"
                else "科技: NULL"
            )

            region_info = company_info.get("地块", "NULL")
            region_text = (
                f"地块: {region_info}"
                if region_info and region_info != "NULL" and region_info != "None"
                else "地块: NULL"
            )

            luxury_info = company_info.get("名贵", "NULL")
            luxury_text = (
                f"名贵: {luxury_info}"
                if luxury_info and luxury_info != "NULL" and luxury_info != "None"
                else "名贵: NULL"
            )

            # 将所有信息合并到一个标签中显示
            combined_text = f"{tech_text}  {region_text}  {luxury_text}"
            combined_label = ttk.Label(info_frame, text=combined_text)
            combined_label.grid(row=1, column=0, sticky="w", pady=1)

            # 确保公司的嵌套字典已创建
            if company not in self.company_info_widgets:
                self.company_info_widgets[company] = {}

            # 存储引用到字典中
            self.company_info_widgets[company]["tech_label"] = combined_label
            self.company_info_widgets[company]["region_label"] = combined_label
            self.company_info_widgets[company]["luxury_label"] = combined_label

            # 第三行：建筑信息（显示全部建筑）
            if isinstance(company_info.get("建筑"), list):
                buildings_text = f"建筑: {', '.join(company_info['建筑'])}"
            else:
                buildings_text = "建筑: -"

            buildings_label = ttk.Label(info_frame, text=buildings_text, wraplength=600)
            buildings_label.grid(row=2, column=0, sticky="w", pady=1, columnspan=3)

            # 第四行：建筑_可选信息
            if isinstance(company_info.get("建筑_可选"), list):
                optional_buildings_text = (
                    f"建筑_可选: {', '.join(company_info['建筑_可选'])}"
                )
            else:
                optional_buildings_text = "建筑_可选: -"

            optional_buildings_label = ttk.Label(
                info_frame, text=optional_buildings_text, wraplength=600
            )
            optional_buildings_label.grid(
                row=3, column=0, sticky="w", pady=1, columnspan=3
            )

            # 第五行：繁荣信息
            if isinstance(company_info.get("繁荣"), list):
                prosperity_text = f"繁荣: {', '.join(company_info['繁荣'])}"
            else:
                prosperity_text = "繁荣: -"

            prosperity_label = ttk.Label(
                info_frame, text=prosperity_text, wraplength=600
            )
            prosperity_label.grid(row=4, column=0, sticky="w", pady=1, columnspan=3)

            # 保存引用
            self.check_vars[company] = var
            self.company_frames[company] = company_frame
            self.company_info_widgets[company] = {
                "company_label": company_label,
                "tech_label": combined_label,
                "region_label": combined_label,
                "luxury_label": combined_label,
                "buildings_label": buildings_label,
                "optional_buildings_label": optional_buildings_label,
                "prosperity_label": prosperity_label,
            }

        # 更新滚动区域
        self.on_frame_configure(None)

    def on_company_select(self, company=None):
        """当公司被选中时更新信息显示"""
        # 获取所有被选中的公司
        selected_companies = [c for c, var in self.check_vars.items() if var.get()]

        # 更新信息显示
        self.update_info_display(selected_companies)

    def update_info_display(self, selected_companies):
        """更新信息显示区域"""
        # 清空文本框
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)

        # 如果没有选中的公司
        if not selected_companies:
            self.info_text.insert(tk.END, "请从左侧选择公司查看信息")
            self.info_text.config(state=tk.DISABLED)
            return

        # 汇总选中公司的信息
        # 统计数据
        total_companies = len(selected_companies)

        # 计算各类信息的汇总
        techs = set()
        regions = set()
        buildings = {}
        optional_buildings = {}
        bonuses = {}
        luxuries = set()
        special_luxuries = 0

        for company in selected_companies:
            info = self.company_data[company]

            # 科技
            if info.get("科技") and info["科技"] != "NULL":
                techs.add(info["科技"])

            # 地块
            if info.get("地块") and info["地块"] != "NULL":
                regions.add(info["地块"])

            # 建筑
            if isinstance(info.get("建筑"), list):
                for building in info["建筑"]:
                    buildings[building] = buildings.get(building, 0) + 1

            # 可选建筑
            if isinstance(info.get("建筑_可选"), list):
                for building in info["建筑_可选"]:
                    optional_buildings[building] = (
                        optional_buildings.get(building, 0) + 1
                    )

            # 繁荣效果
            if isinstance(info.get("繁荣"), list):
                for bonus in info["繁荣"]:
                    bonuses[bonus] = bonuses.get(bonus, 0) + 1

            # 名贵产品
            if info.get("名贵") and info["名贵"] != "NULL":
                luxuries.add(info["名贵"])

            # 特殊名贵
            if info.get("特殊名贵", False):
                special_luxuries += 1

        # 显示汇总信息
        self.info_text.insert(
            tk.END, f"# 公司信息汇总 ({total_companies} 个公司) \n\n"
        )

        # 显示科技
        if techs:
            self.info_text.insert(tk.END, "## 所需科技\n")
            for tech in sorted(techs):
                self.info_text.insert(tk.END, f"- {tech}\n")
            self.info_text.insert(tk.END, "\n")

        # 显示地块
        if regions:
            self.info_text.insert(tk.END, "## 所需地块\n")
            for region in sorted(regions):
                self.info_text.insert(tk.END, f"- {region}\n")
            self.info_text.insert(tk.END, "\n")

        # 显示必需建筑
        if buildings:
            self.info_text.insert(tk.END, "## 基础建筑\n")
            for building, count in sorted(
                buildings.items(), key=lambda x: x[1], reverse=True
            ):
                self.info_text.insert(tk.END, f"- {building} ({count}个公司)\n")
            self.info_text.insert(tk.END, "\n")

        # 显示可选建筑
        if optional_buildings:
            self.info_text.insert(tk.END, "## 可选建筑\n")
            for building, count in sorted(
                optional_buildings.items(), key=lambda x: x[1], reverse=True
            ):
                self.info_text.insert(tk.END, f"- {building} ({count}个公司)\n")
            self.info_text.insert(tk.END, "\n")

        # 显示繁荣效果
        if bonuses:
            self.info_text.insert(tk.END, "## 繁荣效果\n")
            for bonus, count in sorted(
                bonuses.items(), key=lambda x: x[1], reverse=True
            ):
                self.info_text.insert(tk.END, f"- {bonus} ({count}个公司)\n")
            self.info_text.insert(tk.END, "\n")

        # 显示名贵产品
        if luxuries:
            self.info_text.insert(tk.END, "## 名贵商品\n")
            for luxury in sorted(luxuries):
                self.info_text.insert(tk.END, f"- {luxury}\n")
            self.info_text.insert(tk.END, "\n")

        # 显示特殊名贵数量
        if special_luxuries > 0:
            self.info_text.insert(tk.END, f"## 特殊名贵商品数量: {special_luxuries}\n\n")

        # 显示选中的公司列表
        self.info_text.insert(tk.END, "## 选中的公司\n")
        for company in sorted(selected_companies):
            self.info_text.insert(tk.END, f"- {company}\n")

        # 禁用文本框编辑
        self.info_text.config(state=tk.DISABLED)

    def on_frame_configure(self, event):
        """当框架大小改变时更新Canvas的滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """当Canvas大小改变时调整内部框架宽度"""
        # 获取Canvas宽度
        canvas_width = event.width
        # 设置内部框架宽度
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def _show_search_hint(self):
        """显示搜索提示"""
        if not self.search_var.get():
            self.search_hint.place(relx=0.05, rely=0.5, anchor="w")

    def on_search_change(self, *args):
        """当搜索框内容改变时过滤公司列表"""
        search_text = self.search_var.get().lower()
        self.filter_companies(search_text)

    def clear_search(self):
        """清除搜索框内容"""
        self.search_var.set("")
        self._show_search_hint()
        self.filter_companies("")

    def filter_companies(self, search_text):
        """根据搜索文本过滤公司列表"""
        # 如果搜索文本为空，显示所有公司
        if not search_text:
            for company, frame in self.company_frames.items():
                frame.pack(fill=tk.X, padx=5, pady=5)
            return

        # 隐藏所有公司
        for company, frame in self.company_frames.items():
            frame.pack_forget()

        # 找出匹配的公司
        matched_companies = []
        for company in sorted(self.company_data.keys()):
            # 检查公司名称是否匹配
            if search_text in company.lower():
                matched_companies.append(company)
                continue

            # 检查公司信息是否匹配
            company_info = self.company_data[company]
            # 检查科技
            if (
                "科技" in company_info
                and company_info["科技"]
                and company_info["科技"] != "NULL"
                and search_text in str(company_info["科技"]).lower()
            ):
                if company not in matched_companies:
                    matched_companies.append(company)
                continue

            # 检查地块
            if (
                "地块" in company_info
                and company_info["地块"]
                and company_info["地块"] != "NULL"
                and search_text in str(company_info["地块"]).lower()
            ):
                if company not in matched_companies:
                    matched_companies.append(company)
                continue

            # 检查名贵
            if (
                "名贵" in company_info
                and company_info["名贵"]
                and company_info["名贵"] != "NULL"
                and search_text in str(company_info["名贵"]).lower()
            ):
                if company not in matched_companies:
                    matched_companies.append(company)
                continue

            # 检查建筑
            if isinstance(company_info.get("建筑"), list):
                for building in company_info["建筑"]:
                    if search_text in building.lower():
                        if company not in matched_companies:
                            matched_companies.append(company)
                        break

            # 检查可选建筑
            if isinstance(company_info.get("建筑_可选"), list):
                for building in company_info["建筑_可选"]:
                    if search_text in building.lower():
                        if company not in matched_companies:
                            matched_companies.append(company)
                        break

            # 检查繁荣效果
            if isinstance(company_info.get("繁荣"), list):
                for bonus in company_info["繁荣"]:
                    if search_text in bonus.lower():
                        if company not in matched_companies:
                            matched_companies.append(company)
                        break

        # 按顺序显示匹配的公司
        for company in sorted(matched_companies):
            self.company_frames[company].pack(fill=tk.X, padx=5, pady=5)

        # 更新滚动区域
        self.on_frame_configure(None)

    def _show_company(self, company, show_separator=True):
        """显示公司"""
        if company in self.company_frames:
            self.company_frames[company].pack(fill=tk.X, padx=5, pady=5)


if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()

    # 设置中文字体支持
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="SimHei", size=10)
    text_font = font.nametofont("TkTextFont")
    text_font.configure(family="SimHei", size=10)
    fixed_font = font.nametofont("TkFixedFont")
    fixed_font.configure(family="SimHei", size=10)

    # 创建应用
    app = CompanyAnalyzer(root)

    # 运行主循环
    root.mainloop()
