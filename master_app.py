import flet as ft
import json
import os
import re

class Master:
    def __init__(self, name, phone, total_orders=0, total_commission=0):
        self.name = name
        self.phone = phone
        self.total_orders = total_orders
        self.total_commission = total_commission

    @property
    def rating(self):
        if self.total_orders == 0:
            return 0
        return self.total_commission / self.total_orders

    def to_dict(self):
        return {"name": self.name, "phone": self.phone, 
                "total_orders": self.total_orders, "total_commission": self.total_commission}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["phone"], data["total_orders"], data["total_commission"])

class MasterApp:
    def __init__(self):
        self.masters = []
        self.data_file = "masters_data.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.masters = [Master.from_dict(m) for m in data]
            except:
                self.masters = []

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.masters], f, ensure_ascii=False, indent=2)

    def add_master(self, name, phone):
        if any(m.phone == phone for m in self.masters):
            raise ValueError("❌ Мастер с таким номером уже существует")
        self.masters.insert(0, Master(name, phone))
        self.save_data()

    def delete_master(self, master):
        self.masters = [m for m in self.masters if m.phone != master.phone]
        self.save_data()

    def add_orders(self, master, count):
        master.total_orders += count
        self.save_data()

    def add_commission(self, master, amount):
        master.total_commission += amount
        self.save_data()

    def get_sorted_masters(self):
        return sorted(self.masters, key=lambda x: x.rating, reverse=True)

def main(page: ft.Page):
    page.title = "Управление мастерами"
    page.window_width = 1100
    page.window_height = 700
    page.padding = 20
    
    app = MasterApp()
    
    name_input = ft.TextField(label="ФИО мастера", width=350)
    phone_input = ft.TextField(label="Телефон (+996...)", width=250, value="+996")
    search_input = ft.TextField(label="Поиск", width=300, prefix_icon=ft.icons.SEARCH)
    
    stats_text = ft.Text("Статистика", size=14)
    masters_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=600)
    
    def show_message(text, is_error=False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(text),
            bgcolor=ft.colors.RED_700 if is_error else ft.colors.GREEN_700,
            duration=3000
        )
        page.snack_bar.open = True
        page.update()
    
    def refresh_list(e=None):
        masters_list.controls.clear()
        
        search = search_input.value.lower() if search_input.value else ""
        masters = app.get_sorted_masters()
        
        if search:
            masters = [m for m in masters if search in m.name.lower() or search in m.phone.lower()]
        
        for master in masters:
            if master.rating >= 500:
                rating_color = ft.colors.GREEN
                rating_icon = "🏆"
            elif master.rating >= 200:
                rating_color = ft.colors.ORANGE
                rating_icon = "⭐"
            else:
                rating_color = ft.colors.RED
                rating_icon = "⚡"
            
            card = ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(master.name, size=18, weight=ft.FontWeight.BOLD),
                                ft.Text(master.phone, size=14, color=ft.colors.GREY_600),
                                ft.Text(f"{rating_icon} Рейтинг: {master.rating:.2f} руб./заказ", 
                                       size=12, color=rating_color),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"📦 Заказов: {master.total_orders}", size=14),
                                ft.Text(f"💰 Комиссия: {master.total_commission:.2f} руб.", size=14),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.ElevatedButton("➕ Заказы", on_click=lambda e, m=master: open_orders_dialog(m)),
                            ft.ElevatedButton("💰 Комиссия", on_click=lambda e, m=master: open_commission_dialog(m)),
                            ft.ElevatedButton("🗑️ Удалить", on_click=lambda e, m=master: confirm_delete(m),
                                             bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
                        ], alignment=ft.MainAxisAlignment.END, spacing=10),
                    ])
                )
            )
            masters_list.controls.append(card)
        
        if app.masters:
            total_orders = sum(m.total_orders for m in app.masters)
            total_comm = sum(m.total_commission for m in app.masters)
            avg = total_comm / total_orders if total_orders > 0 else 0
            stats_text.value = f"📊 Мастеров: {len(app.masters)} | Заказов: {total_orders} | Комиссия: {total_comm:.2f} руб. | Средний рейтинг: {avg:.2f} руб./заказ"
        else:
            stats_text.value = "📊 Нет данных"
        
        page.update()
    
    def open_orders_dialog(master):
        count_field = ft.TextField(label="Количество заказов", value="1", keyboard_type=ft.KeyboardType.NUMBER, width=300)
        
        def add_orders(e):
            try:
                count = int(count_field.value)
                if count > 0:
                    app.add_orders(master, count)
                    dialog.open = False
                    page.update()
                    refresh_list()
                    show_message(f"✅ Добавлено {count} заказ(ов) для {master.name}")
                else:
                    show_message("❌ Введите число больше 0", True)
            except:
                show_message("❌ Ошибка", True)
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Добавить заказы для {master.name}"),
            content=count_field,
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton("Добавить", on_click=add_orders),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def open_commission_dialog(master):
        amount_field = ft.TextField(label="Сумма комиссии (руб.)", keyboard_type=ft.KeyboardType.NUMBER, width=300, hint_text="Введите сумму")
        
        def add_commission(e):
            try:
                amount = float(amount_field.value)
                if amount > 0:
                    app.add_commission(master, amount)
                    dialog.open = False
                    page.update()
                    refresh_list()
                    show_message(f"✅ Добавлена комиссия {amount:.2f} руб. для {master.name}")
                else:
                    show_message("❌ Введите сумму больше 0", True)
            except:
                show_message("❌ Ошибка", True)
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Добавить комиссию для {master.name}"),
            content=amount_field,
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton("Добавить", on_click=add_commission),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def confirm_delete(master):
        def delete(e):
            app.delete_master(master)
            dialog.open = False
            page.update()
            refresh_list()
            show_message(f"🗑️ Мастер {master.name} удален")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Подтверждение удаления"),
            content=ft.Text(f"Удалить мастера {master.name}? Все данные будут потеряны."),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton("Удалить", on_click=delete, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def close_dialog(dialog):
        dialog.open = False
        page.update()
    
    def add_new_master(e):
        name = name_input.value.strip()
        phone = phone_input.value.strip()
        
        if not name or not phone:
            show_message("⚠️ Заполните все поля", True)
            return
        
        if not phone.startswith("+996"):
            show_message("⚠️ Телефон должен начинаться с +996", True)
            return
        
        try:
            app.add_master(name, phone)
            name_input.value = ""
            phone_input.value = "+996"
            refresh_list()
            show_message(f"✅ Мастер {name} добавлен")
        except Exception as ex:
            show_message(str(ex), True)
    
    search_input.on_change = refresh_list
    
    page.add(
        ft.Column([
            ft.Text("👨‍🔧 Управление мастерами", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Container(
                bgcolor=ft.colors.GREY_100,
                border_radius=10,
                padding=15,
                content=ft.Column([
                    ft.Text("➕ Добавить мастера", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([name_input, phone_input, ft.ElevatedButton("Добавить", on_click=add_new_master), search_input], spacing=10),
                ])
            ),
            
            
            ft.Container(height=10),
            stats_text,
            ft.Divider(),
            ft.Text("📋 Список мастеров", size=18, weight=ft.FontWeight.BOLD),
            masters_list,
        ], expand=True, spacing=10)
    )
    
    refresh_list()

if __name__ == "__main__":
    # Railway автоматически предоставляет порт в переменной окружения PORT
    port = int(os.environ.get("PORT", 8000))
    # Запускаем приложение как веб-сервер, слушая все доступные адреса (0.0.0.0)
    ft.app(target=main, port=port, view=ft.WEB_BROWSER, host="0.0.0.0")
    