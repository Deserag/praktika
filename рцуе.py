def show_product_details(self, order_id):
    # Создание новой таблицы с информацией о заказе
    detail_widget = QWidget()
    detail_layout = QVBoxLayout(detail_widget)

    # Заголовки таблицы деталей товара
    detail_table = QTableWidget()
    detail_table.setColumnCount(4)
    detail_table.setHorizontalHeaderLabels(
        ["Наименование товара", "Кол-во", "Цена", "Общая цена"])

    # Запрос на получение деталей товара из базы данных
    cursor = self.connection.cursor()
    cursor.execute(f"SELECT * FROM Заказы WHERE Код_заказа = {order_id};")
    rows = cursor.fetchall()

    # Добавление деталей товара в таблицу
    for row_num, row_data in enumerate(rows):
        detail_table.insertRow(row_num)
        for column_num, data in enumerate(row_data):
            item = QTableWidgetItem(str(data))
            detail_table.setItem(row_num, column_num, item)

    detail_layout.addWidget(detail_table)
    self.stacked_widget.addWidget(detail_widget)
    self.stacked_widget.setCurrentWidget(detail_widget)