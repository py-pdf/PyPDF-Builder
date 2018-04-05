#!/usr/bin/python

import os
import tkinter as tk
import pygubu


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


class MyApplication:
    def __init__(self):
        self.builder = pygubu.Builder()
        self.builder.add_from_file(os.path.join(CURRENT_DIR, 'mainwindow.ui'))

        self.mainwindow = self.builder.get_object('mainwindow')
        self.mainmenu = self.builder.get_object('MainMenu')
        self.mainwindow.config(menu=self.mainmenu)

        self.builder.connect_callbacks(self)

    def quit(self, event=None):
        self.mainwindow.quit()

    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    app = MyApplication()
    app.run()