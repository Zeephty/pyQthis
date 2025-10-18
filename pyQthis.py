import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTransform, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QInputDialog,
    QTableWidgetItem,
)
import sqlite3
import MainMenu
import GameForm
import csv

# Стиль для таблицы
TABLE_G = """QTableWidget {border: 1px solid #cccccc; border-radius: 8px;}

            QTableWidget::item {border-bottom: 1px solid #cccccc; background-color: 
            qlineargradient(spread:pad, x1:1, y1:1, x2:1, y2:0, 
            stop:0 rgba(245, 245, 245, 245), stop:1 rgba(255, 255, 255, 255));}

            QTableWidget::item:hover {border: 1px solid #F37021; border-radius: 8px; background-color: #ADEFF5;}"""


# Создаем класс гейминга
class Pyqth(QMainWindow, GameForm.Ui_MainWindow):
    def __init__(self, thist, name, stat):
        super().__init__()
        self.setupUi(self)

        # присваем данные переданные данному классу
        self.history = thist
        self.profileIndex = name
        self.statictic = stat

        # читаем и записываем путь перемещений в переменную
        with open("move.csv", "r", encoding="utf8") as file:
            self.dict = {}
            for i in list(csv.DictReader(file, delimiter=";")):
                self.dict[i["История"]] = self.dict.get(i["История"], []) + [i]

        # создаем словарную матрешку из перемещений
        self.moves = self.overkill(
            {},
            [
                [
                    list(map(int, i["Линия выбора"].split("."))),
                    [
                        i["Текст"],
                        i["Конец?"],
                        list(map(lambda x: x.split("|"), i["Выборы"].split("//"))),
                    ],
                ]
                for i in self.dict[thist]
            ],
        )[1]

        # создаю таймер
        self.timer = QTimer(self)
        self.timer.setInterval(8)
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.imageA)
        self.timer.start()

        # создаю словарь из кнопок
        self.buttons = {
            1: self.itemButton1,
            2: self.itemButton2,
            3: self.itemButton3,
            4: self.itemButton4,
            5: self.itemButton5,
        }

        # добавляем стиль заднего фона и кнопок
        self.setStyleSheet("QMainWindow {background-color: #D1F8FF}")
        for v in self.buttons.values():
            v.clicked.connect(self.toggle)
            v.setStyleSheet("QPushButton {background-color: #A3D1FF}")

        # создаем переменные для анимации
        self.pixmap = QPixmap("sfu.png")
        self.alp = 0

        # создаем текущий словаерь выборов
        self.mbtn = {}

        # код перемещений
        self.h = f"[{thist}] 1"

        # фиксим кнопки текст на них и описание
        self.fix()

    # изменяем угол и поворачиваем изображение
    def imageA(self):
        self.labelImage.setPixmap(
            self.pixmap.transformed(QTransform().rotate(self.alp))
        )
        self.alp = (self.alp + 1) % 360

    # Функция скрывает ненужные кнопки меняет текущий словарь и меняет тексты на кнопке и описание
    def fix(self):
        self.mbtn = {}
        lst = self.moves[1]
        self.textl_2.setFontPointSize(12)
        self.textl_2.setText(lst[0])
        for i, v in self.buttons.items():
            if i <= len(lst[2]):
                v.setVisible(True)
                v.setText(lst[2][i - 1][0])
                self.mbtn[int(lst[2][i - 1][1])] = v
            else:
                v.setVisible(False)

    # рекурсивно задаем матрешку из ходов
    def overkill(self, name, lsts):
        a = name
        for i, v in enumerate(lsts[0][0]):
            a[v] = a.get(v, [{}])
            if i == len(lsts[0][0]) - 1:
                a[v] += [lsts[0][1]]
            a = a[v][0]
        if len(lsts) > 1:
            return self.overkill(name, lsts[1:])
        else:
            return name

    # проверяем на конечный ход и меняем базу данных если пользователь зарегестрирвался
    def toggle(self):
        obj = self.sender()
        if self.moves[1][1] == "0":
            for i, v in self.mbtn.items():
                if obj == v:
                    if i in self.moves[0]:
                        self.moves = self.moves[0][i]
                        self.h += f".{i}"
                        self.fix()
                    else:
                        print("Ошибка")
                    break
        else:
            self.f = Menu()
            if self.profileIndex != -1:
                con = sqlite3.connect("statistic.db")
                cur = con.cursor()

                cur.execute(
                    f"""INSERT INTO purges(playerId, purge, progress) 
                    VALUES({self.statictic[0][self.profileIndex]}, '{self.moves[1][1].split('|')[1]}', '{self.h}');"""
                )
                cur.execute(
                    f"UPDATE statistic SET ends = ends + 1 WHERE statistic.id = {self.statictic[0][self.profileIndex]}"
                )
                con.commit()
                statistic = list(
                    zip(
                        *cur.execute(
                            """SELECT statistic.id, login, ends, password 
                    FROM statistic join registered on statistic.id = registered.id"""
                        ).fetchall()
                    )
                )

                con.close()

                self.f.profileCheck = self.profileIndex
                self.f.profile.setText(self.statictic[1][self.profileIndex])
                self.f.statistic = statistic
                self.f.showTableStat()
                self.f.profileButton.setVisible(True)
            self.f.show()
            self.close()


# Создаем класс кгавного меню
class Menu(QMainWindow, MainMenu.Ui_MainWindow):
    def __init__(self):
        super().__init__()

        # имортируем объекты из файла
        self.setupUi(self)

        # Добавляем стиль к таблицам
        self.tableWidgetStatistic.setStyleSheet(TABLE_G)
        self.tableWidgetPurges.setStyleSheet(TABLE_G)

        # Меняем данные таблиц и отображаем их
        self.tableWidgetStatistic.clicked.connect(self.showTableStat)
        self.tableWidgetPurges.clicked.connect(self.showTableStat)

        # Номер элемента с профилем человека, который вошел в систему, если не зашел, то -1
        self.profileCheck = -1

        # Список виджетов из профиля
        self.profileWidjets = {
            "Текст профиль": self.label_3,
            "Назад": self.returnButton,
            "Таблица очивок": self.tableWidgetPurges,
            "Кол. концовок": self.labelEnds,
            "Логин": self.labelLogin,
        }

        # Список виджетов для историй
        self.menuHistory = {
            "Работа": self.mButton1,
            "Система": self.mButton2,
            "Болезнь": self.mButton3,
            "Мир под угрозой": self.mButton4,
            "А чего вы ожидали?": self.mButton5,
            "<-Назад": self.backwardButton,
            "Истории": self.textl,
        }

        # Список виджетов для главного меню
        self.mainMenu = {
            "Название": self.labelProjectName,
            "Играть": self.playButton,
            "Войти": self.loginButton,
            "Зарегестрироваться": self.registeringButton,
            "Выйти": self.exitButton,
            "Таблица статистики": self.tableWidgetStatistic,
            "Статистика": self.label_2,
            "Имя": self.profile,
        }

        # Скрываем кнопку для перехода в профиль
        self.profileButton.setVisible(False)

        # Скрываем все виджиты из выбора историй и профиля
        self.hideChoiceH()
        self.hideProfile()

        # Читаем базу данных со статистикой
        self.readTableStat()

        # Отображаем таблицу из главного меню и редактируем из профиля таблицу
        self.showTableStat()
        self.showTablePurges()

        # Привязываем к кнопке выхода закрытие приложения
        self.exitButton.clicked.connect(sys.exit)

        # Связываем кнопку играть к скрытию меню и показу выбора историй
        self.playButton.clicked.connect(self.hideMainmenu)
        self.playButton.clicked.connect(self.showChoiceH)

        # Связываем кнопку назад с о скрытию показа выбора историй и показа меню
        self.backwardButton.clicked.connect(self.showMainmenu)
        self.backwardButton.clicked.connect(self.hideChoiceH)

        # Связываем кнопку профидя к скрытию меню и показу выбора историй
        self.profileButton.clicked.connect(self.hideMainmenu)
        self.profileButton.clicked.connect(self.showProfile)
        self.profileButton.clicked.connect(self.showTablePurges)

        self.returnButton.clicked.connect(self.showMainmenu)
        self.returnButton.clicked.connect(self.hideProfile)

        # Привязываем кнопку к входу в учетную запись
        self.loginButton.clicked.connect(self.loginIn)

        # Привязываем кнопку к регистрации
        self.registeringButton.clicked.connect(self.registredIn)

        # Привязываем кнопки к функции запуска истории
        # Меняем цвет у тех кнопок у которых нет историй
        # Подписываем на них что их еще нет
        for i in list(self.menuHistory.values())[:-2]:
            i.clicked.connect(self.gameHistory)
            if i != self.mButton1:
                i.setStyleSheet("background-color: rgb(200, 100, 100)")
                i.setText("Не доступно")

    # фунция для запуска истории
    def gameHistory(self):
        obj = self.sender()
        if obj.text() == "Работа":
            self.f = Pyqth("Работа", self.profileCheck, self.statistic)
            self.f.show()
            self.close()
            self.help()

    # Функция скрывает виджеты профиля
    def hideProfile(self):
        for i in self.profileWidjets.values():
            i.setVisible(False)

    # Функция скрывает виджеты выбора
    def hideChoiceH(self):
        for i in self.menuHistory.values():
            i.setVisible(False)

    # Функция скрывает виджеты главного меню
    def hideMainmenu(self):
        for i in self.mainMenu.values():
            i.setVisible(False)
        if self.profileCheck != -1:
            self.profileButton.setVisible(False)

    # Показывает виджеты профиля
    def showProfile(self):
        for i in self.profileWidjets.values():
            i.setVisible(True)

    # Показывает виджеты выбора
    def showChoiceH(self):
        for i in self.menuHistory.values():
            i.setVisible(True)

    # Показывает виджеты главного меню
    def showMainmenu(self):
        for i in self.mainMenu.values():
            i.setVisible(True)
        if self.profileCheck != -1:
            self.profileButton.setVisible(True)

    # Читает данные из базы данных
    def readTableStat(self):
        con = sqlite3.connect("statistic.db")
        cur = con.cursor()

        self.statistic = list(
            zip(
                *cur.execute(
                    """SELECT statistic.id, login, ends, password 
            FROM statistic join registered on statistic.id = registered.id"""
                ).fetchall()
            )
        )

        con.close()

    # Функция проверки и входа в свой аккаунт
    def loginIn(self):
        login, done1 = QInputDialog.getText(
            self, "Регистрация", """Напиши свой логин:"""
        )
        if done1:
            if login in self.statistic[1]:
                password, done2 = QInputDialog.getText(
                    self, "Регистрация", """Напиши свой пароль:"""
                )
                if done2:
                    if self.statistic[3][self.statistic[1].index(login)] == password:
                        self.profileCheck = self.statistic[1].index(login)
                        self.profile.setText(login)
                        self.profileButton.setVisible(True)
                    else:
                        self.message("""Неправильный пароль!""", "Ошибка!!")
                else:
                    self.message("""Ты вышел!!""", "Зачем?")
            else:
                self.message("""Такого логина не существует!!""", "Ошибка!!")
        else:
            self.message("""Ты вышел!!""", "Зачем?")

    # Регистрация нового аккаунта
    def registredIn(self):
        login, done1 = QInputDialog.getText(
            self,
            "Регистрация",
            """Напиши логин 
(не допускаются логины, длина которых меньше 4, или уже существующие):""",
        )
        if done1:
            if (not self.statistic or login not in self.statistic[1]) and len(login) >= 4:
                password, done2 = QInputDialog.getText(
                    self,
                    "Регистрация",
                    """Напиши пароль:
(не допускаются пароли, длина которых меньше 8)""",
                )
                if done2:
                    if password and len(password) >= 8:
                        con = sqlite3.connect("statistic.db")
                        cur = con.cursor()

                        cur.execute(
                            f"""INSERT INTO statistic(login, ends) VALUES('{login}', 0);"""
                        )
                        cur.execute(
                            f"""INSERT INTO registered(password) VALUES('{password}');"""
                        )
                        con.commit()

                        self.statistic = list(
                            zip(
                                *cur.execute(
                                    """SELECT statistic.id, login, ends, password 
                            FROM statistic join registered on statistic.id = registered.id"""
                                ).fetchall()
                            )
                        )
                        self.profileCheck = self.statistic[1].index(login)

                        con.close()

                        self.showTableStat()
                    else:
                        self.message(
                            """Ты ввел пароль содержащий менее 9 символов!!""",
                            "Ошибка!!",
                        )
                else:
                    self.message("""Ты вышел!!""", "Зачем?")
            else:
                self.message(
                    """Ты ввел либо логин содержащий менее 4, либо уже существующий логин!!""",
                    "Ошибка!!",
                )
        else:
            self.message("""Ты вышел!!""", "Зачем?")

    # Функция для изменения таблицы с очивками также меняет значения логина и концовок
    def showTablePurges(self):
        self.tableWidgetPurges.clear()
        con = sqlite3.connect("statistic.db")
        cur = con.cursor()
        if self.profileCheck != -1:
            tbprof = cur.execute(
                f"""SELECT purges.purge, purges.progress, statistic.ends
from statistic join purges on statistic.id = purges.playerId 
WHERE statistic.id = {self.statistic[0][self.profileCheck]}"""
            ).fetchall()
            if list(tbprof) != []:
                self.labelLogin.setText(
                    "Login: " + self.statistic[1][self.profileCheck]
                )
                self.labelEnds.setText("Количество концовок: " + str(tbprof[0][2]))
        else:
            tbprof = []
        self.tableWidgetPurges.setRowCount(len(list(tbprof)))
        self.tableWidgetPurges.setColumnCount(2)
        self.tableWidgetPurges.horizontalHeader().setStretchLastSection(True)
        self.tableWidgetPurges.setHorizontalHeaderLabels(["Очивка", "Ходы"])
        for i, v in enumerate(list(tbprof)):
            for j in range(2):
                self.tableWidgetPurges.setItem(i, j, QTableWidgetItem(str(v[j])))
        con.close()

    # Функция изменяет таблицу с главной статистикой
    def showTableStat(self):
        self.tableWidgetStatistic.clear()
        if self.statistic:
            self.tableWidgetStatistic.setRowCount(len(self.statistic[0]))
            self.tableWidgetStatistic.setColumnCount(2)
            self.tableWidgetStatistic.horizontalHeader().setStretchLastSection(True)
            self.tableWidgetStatistic.setHorizontalHeaderLabels(["Имя", "Кол. концовок"])
            for i, v in enumerate(list(zip(*self.statistic))):
                for j in range(2):
                    self.tableWidgetStatistic.setItem(i, j, QTableWidgetItem(str(v[j + 1])))

    # Функция для упрощения вызова предупреждающего сообщения
    def message(self, text, name):
        msg = QMessageBox(parent=self, text=text)
        msg.setWindowTitle(name)
        msg.exec()

    # Функция которая напоминает о сути игры при входе в историю
    def help(self):
        msg = QMessageBox(
            parent=self,
            text="""Привет мой друг. В этой игре тебе нужно будет принимать решения.
Каждое твое решение может изменить концовку""",
        )
        msg.setWindowTitle("Уточнения")
        msg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Menu()
    ex.show()
    sys.exit(app.exec())
