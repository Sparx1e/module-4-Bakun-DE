from __future__ import annotations
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from app.config import APP_NAME, ICON_PATH
from app.db.auth_repository import AuthRepository
from app.db.catalog_repository import CatalogRepository
from app.db.connection import Database
from app.db.order_repository import OrderRepository
from app.errors import AppError
from app.models.entities import User
from app.services.catalog_service import CatalogService
from app.services.order_service import Cart, OrderService
from app.ui.cart_page import CartPage
from app.ui.catalog_page import CatalogPage
from app.ui.formatting import format_money
from app.ui.header import HeaderBar
from app.ui.login_page import LoginPage
from app.ui.messages import ask_confirmation, show_error, show_info, show_warning
from app.ui.order_detail_page import OrderDetailPage
from app.ui.order_edit_page import OrderEditPage
from app.ui.order_form_page import OrderFormPage
from app.ui.orders_page import OrdersPage
from app.ui.product_page import ProductPage

PAGE_TITLES = {
    "login": "ФормаДесерт — вход в систему",
    "catalog": "ФормаДесерт — каталог",
    "product": "ФормаДесерт — просмотр товара",
    "cart": "ФормаДесерт — оформление заказа",
    "orders": "ФормаДесерт — заказы",
    "order_detail": "ФормаДесерт — состав заказа",
    "order_form": "ФормаДесерт — новый заказ",
    "order_edit": "ФормаДесерт — редактирование заказа",
}


class MainWindow(QMainWindow):
    """Координирует страницы, роли пользователей и работу с базой данных."""

    def __init__(self, database: Database) -> None:
        super().__init__()
        self._database = database
        self._auth_repository = AuthRepository(database)
        self._catalog_service = CatalogService(CatalogRepository(database))
        self._order_service = OrderService(OrderRepository(database))

        self._user: User | None = None
        self._is_guest = False
        self._cart = Cart()
        self._history: list[str] = []
        self._current_page: str | None = None

        self.resize(1280, 860)
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setWindowTitle(APP_NAME)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = HeaderBar()
        self._header.logout_requested.connect(self._logout)
        self._header.login_requested.connect(self._show_login)
        root.addWidget(self._header)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)
        self.setCentralWidget(central)

        categories = self._catalog_service.load_categories()
        self._login_page = LoginPage()
        self._catalog_page = CatalogPage(categories)
        self._product_page = ProductPage()
        self._cart_page = CartPage()
        self._orders_page = OrdersPage()
        self._order_detail_page = OrderDetailPage()
        self._order_form_page = OrderFormPage()
        self._order_edit_page = OrderEditPage()

        self._pages = {
            "login": self._login_page,
            "catalog": self._catalog_page,
            "product": self._product_page,
            "cart": self._cart_page,
            "orders": self._orders_page,
            "order_detail": self._order_detail_page,
            "order_form": self._order_form_page,
            "order_edit": self._order_edit_page,
        }
        for page in self._pages.values():
            self._stack.addWidget(page)

        self._connect_signals()
        self._show_login()

    def _connect_signals(self) -> None:
        self._login_page.login_submitted.connect(self._login)
        self._login_page.guest_requested.connect(self._enter_guest)

        self._catalog_page.product_selected.connect(self._open_product)
        self._catalog_page.cart_requested.connect(self._open_cart)
        self._catalog_page.orders_requested.connect(self._open_orders)

        self._product_page.back_requested.connect(self._back)
        self._product_page.add_requested.connect(self._add_to_cart)
        self._product_page.login_requested.connect(self._show_login)

        self._cart_page.back_requested.connect(self._back)
        self._cart_page.confirm_requested.connect(self._confirm_cart)
        self._cart_page.quantity_changed.connect(self._change_cart_quantity)
        self._cart_page.remove_requested.connect(self._remove_cart_item)

        self._orders_page.open_requested.connect(self._open_order)
        self._orders_page.add_requested.connect(self._start_add_order)
        self._orders_page.delete_requested.connect(self._delete_order)
        self._orders_page.edit_requested.connect(self._start_edit_order)
        self._orders_page.back_requested.connect(self._show_catalog)

        self._order_detail_page.back_requested.connect(self._back)
        self._order_detail_page.edit_requested.connect(self._start_edit_order)

        self._order_form_page.confirm_requested.connect(self._confirm_new_order)
        self._order_form_page.cancel_requested.connect(self._back)

        self._order_edit_page.save_requested.connect(self._save_order_edit)
        self._order_edit_page.cancel_requested.connect(self._back)


    def _show_page(self, key: str, push: bool = True) -> None:
        if push and self._current_page is not None and self._current_page != key:
            self._history.append(self._current_page)
        self._current_page = key
        self._stack.setCurrentWidget(self._pages[key])
        title = PAGE_TITLES[key]
        self._header.set_page_title(title)
        self.setWindowTitle(title)

    def _back(self) -> None:
        if not self._history:
            self._show_catalog()
            return
        key = self._history.pop()
        if key == "catalog":
            self._reload_catalog()
        elif key == "orders":
            self._reload_orders()
        self._show_page(key, push=False)

    def _show_catalog(self) -> None:
        self._reload_catalog()
        self._show_page("catalog", push=False)

    def _show_login(self) -> None:
        self._user = None
        self._is_guest = False
        self._cart.clear()
        self._history.clear()
        self._header.show_login_state()
        self._login_page.reset()
        self._show_page("login", push=False)


    def _login(self, login: str) -> None:
        try:
            user = self._auth_repository.find_by_login(login)
        except AppError as exc:
            self._report_error(exc)
            return

        if user is None:
            show_warning(
                self,
                "Пользователь не найден",
                f"Логин «{login}» отсутствует в списке пользователей системы. "
                "Проверьте написание логина (например, admin, manager, client1) "
                "и повторите вход.",
            )
            return

        self._user = user
        self._is_guest = False
        self._cart.clear()
        self._history.clear()
        self._header.show_user(user)
        self._reload_catalog()
        self._show_page("catalog", push=False)

    def _enter_guest(self) -> None:
        self._user = None
        self._is_guest = True
        self._cart.clear()
        self._history.clear()
        self._header.show_guest_state()
        self._reload_catalog()
        self._show_page("catalog", push=False)

    def _logout(self) -> None:
        if not ask_confirmation(
            self,
            "Выход из системы",
            "Выйти из системы? Неподтверждённый заказ будет очищен.",
        ):
            return
        self._show_login()


    def _reload_catalog(self) -> None:
        try:
            products = self._catalog_service.load_products()
        except AppError as exc:
            self._report_error(exc)
            return
        self._catalog_page.set_user(self._user if not self._is_guest else None)
        self._catalog_page.set_cart_count(len(self._cart))
        self._catalog_page.load_products(products)

    def _open_product(self, product_id: int) -> None:
        try:
            product = self._catalog_service.get_product(product_id)
        except AppError as exc:
            self._report_error(exc)
            return
        if product is None:
            show_warning(
                self,
                "Товар не найден",
                "Выбранная модель отсутствует в каталоге. Обновите каталог и повторите выбор.",
            )
            self._reload_catalog()
            return
        self._product_page.load_product(product, self._user)
        self._show_page("product")


    def _add_to_cart(self, product_id: int, stock_item_id: int, quantity: int) -> None:
        if self._user is None or not self._user.is_client:
            show_warning(
                self,
                "Требуется вход",
                "Добавление товара в заказ доступно авторизованному клиенту. "
                "Войдите в систему по логину.",
            )
            return
        try:
            product = self._catalog_service.get_product(product_id)
            if product is None:
                show_warning(
                    self,
                    "Товар не найден",
                    "Модель отсутствует в каталоге. Обновите каталог.",
                )
                return
            variant = next(
                (
                    item
                    for item in product.variants
                    if item.stock_item_id == stock_item_id
                ),
                None,
            )
            if variant is None:
                show_warning(
                    self,
                    "Вариант недоступен",
                    "Выбранный вариант исполнения отсутствует. Обновите страницу товара.",
                )
                return
            self._cart.add(product, variant, quantity)
        except AppError as exc:
            show_warning(self, exc.title, str(exc))
            return

        self._catalog_page.set_cart_count(len(self._cart))
        show_info(
            self,
            "Позиция добавлена",
            f"«{product.name}», вариант «{variant.variant_name}», "
            f"{quantity} шт. добавлено в заказ.\n\n"
            "Продолжите выбор товаров или откройте корзину для подтверждения заказа.",
        )

    def _open_cart(self) -> None:
        if self._user is None or not self._user.is_client:
            show_warning(
                self,
                "Доступ запрещён",
                "Корзина доступна авторизованному клиенту.",
            )
            return
        self._cart_page.load_cart(self._cart)
        self._show_page("cart")

    def _change_cart_quantity(self, stock_item_id: int, quantity: int) -> None:
        try:
            self._cart.set_quantity(stock_item_id, quantity)
        except AppError as exc:
            show_warning(self, exc.title, str(exc))
        self._cart_page.load_cart(self._cart)
        self._catalog_page.set_cart_count(len(self._cart))

    def _remove_cart_item(self, stock_item_id: int) -> None:
        self._cart.remove(stock_item_id)
        self._cart_page.load_cart(self._cart)
        self._catalog_page.set_cart_count(len(self._cart))

    def _confirm_cart(self) -> None:
        if self._user is None or not self._user.is_client:
            return
        if self._cart.is_empty():
            show_warning(
                self,
                "Пустой заказ",
                "Нельзя подтвердить заказ без товарных позиций. Добавьте товар из каталога.",
            )
            return
        if not ask_confirmation(
            self,
            "Подтверждение заказа",
            f"Оформить заказ на сумму {self._format_total()}?\n\n"
            "После подтверждения позиции будут сохранены, а доступное количество "
            "товаров на складе уменьшится.",
        ):
            return
        try:
            order_id = self._order_service.create_order(self._user.user_id, self._cart)
        except AppError as exc:
            self._report_error(exc)
            self._reload_catalog()
            return

        self._cart.clear()
        self._catalog_page.set_cart_count(0)
        self._reload_catalog()
        show_info(
            self,
            "Заказ оформлен",
            f"Заказ №{order_id} успешно сохранён. "
            "Доступное количество товаров в каталоге обновлено.",
        )
        self._show_catalog()

    def _format_total(self) -> str:
        return format_money(self._cart.total)


    def _require_staff(self) -> bool:
        if self._user is None or not self._user.is_staff:
            show_error(
                self,
                "Доступ запрещён",
                "Работа со списком заказов доступна только менеджеру и администратору. "
                "Войдите под соответствующей учётной записью.",
            )
            return False
        return True

    def _open_orders(self) -> None:
        if not self._require_staff():
            return
        if not self._reload_orders():
            return
        self._show_page("orders")

    def _reload_orders(self) -> bool:
        try:
            orders = self._order_service.list_orders()
        except AppError as exc:
            self._report_error(exc)
            return False
        assert self._user is not None
        self._orders_page.load_orders(orders, self._user)
        return True

    def _open_order(self, order_id: int) -> None:
        if not self._require_staff():
            return
        try:
            order = self._order_service.get_order(order_id)
        except AppError as exc:
            self._report_error(exc)
            self._reload_orders()
            return
        assert self._user is not None
        self._order_detail_page.load_order(order, self._user)
        self._show_page("order_detail")

    def _delete_order(self, order_id: int) -> None:
        if not self._require_staff():
            return
        try:
            self._order_service.delete_order(order_id)
        except AppError as exc:
            self._report_error(exc)
            self._reload_orders()
            return

        show_info(
            self,
            "Заказ удалён",
            f"Заказ №{order_id} удалён. Товары возвращены на склад, "
            "список заказов обновлён.",
        )
        self._reload_catalog()
        self._reload_orders()
        if self._current_page == "order_detail":
            if self._history and self._history[-1] == "order_detail":
                self._history.pop()
            self._show_page("orders", push=False)

    def _start_add_order(self) -> None:
        if not self._require_staff():
            return
        try:
            clients = self._auth_repository.list_clients()
            products = self._catalog_service.load_products()
        except AppError as exc:
            self._report_error(exc)
            return
        assert self._user is not None
        self._order_form_page.load(clients, products, self._user)
        self._show_page("order_form")

    def _confirm_new_order(self, client_id: int, cart: Cart) -> None:
        if not self._require_staff():
            return
        if cart.is_empty():
            show_warning(
                self,
                "Пустой заказ",
                "Добавьте хотя бы одну позицию перед подтверждением.",
            )
            return
        if not ask_confirmation(
            self,
            "Подтверждение заказа",
            f"Создать заказ на сумму {format_money(cart.total)}?\n\n"
            "Позиции будут сохранены, остатки товаров уменьшатся.",
        ):
            return
        try:
            order_id = self._order_service.create_order(client_id, cart)
        except AppError as exc:
            self._report_error(exc)
            self._reload_catalog()
            return

        self._reload_catalog()
        self._reload_orders()
        show_info(
            self,
            "Заказ создан",
            f"Заказ №{order_id} успешно сохранён. Список заказов обновлён.",
        )
        if self._history and self._history[-1] == "orders":
            self._history.pop()
        self._show_page("orders", push=False)

    def _start_edit_order(self, order_id: int) -> None:
        if self._user is None or not self._user.is_admin:
            show_error(
                self,
                "Доступ запрещён",
                "Редактирование заказа доступно только администратору.",
            )
            return
        try:
            order = self._order_service.get_order(order_id)
        except AppError as exc:
            self._report_error(exc)
            return
        self._order_edit_page.load_order(order)
        self._show_page("order_edit")

    def _save_order_edit(self, order_id: int, order_date, delete_item_ids) -> None:
        if self._user is None or not self._user.is_admin:
            show_error(
                self,
                "Доступ запрещён",
                "Редактирование заказа доступно только администратору.",
            )
            return
        try:
            self._order_service.update_order(order_id, order_date, list(delete_item_ids))
        except AppError as exc:
            self._report_error(exc)
            return

        self._reload_catalog()
        self._reload_orders()
        show_info(
            self,
            "Изменения сохранены",
            f"Заказ №{order_id} обновлён. Изменённая дата и состав сохранены в базе данных.",
        )
        try:
            order = self._order_service.get_order(order_id)
        except AppError as exc:
            self._report_error(exc)
            self._show_page("orders", push=False)
            return
        assert self._user is not None
        self._order_detail_page.load_order(order, self._user)
        if self._history and self._history[-1] == "order_detail":
            self._history.pop()
        self._show_page("order_detail", push=False)


    def _report_error(self, exc: Exception) -> None:
        if isinstance(exc, AppError):
            show_error(self, exc.title, str(exc))
        else:
            show_error(
                self,
                "Непредвиденная ошибка",
                "Операция не выполнена. Приложение продолжает работу.\n\n"
                f"Техническая информация: {exc}",
            )

    def closeEvent(self, event: QCloseEvent) -> None:
        self._database.close()
        super().closeEvent(event)
