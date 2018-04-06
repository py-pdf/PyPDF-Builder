#!/usr/bin/python

import os
from operator import itemgetter

import tkinter as tk
from tkinter import filedialog
from pygubu import Builder as pgBuilder

from PyPDF2 import PdfFileMerger

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


class JoinTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.files_tree_widget = self.parent.builder.get_object('JoinFilesList')
        self.join_files = []    # Format for entries: (pos, filepath, filename, pages)

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def add_file(self):
        add_filepaths = list(self.parent.get_open_files(widget_title='Choose PDFs to Add...'))
        # print(f'Return value: {add_filepaths}\nListed: {add_filepath_list}')
        for fp in add_filepaths:
            filename = os.path.basename(fp)
            if len(self.join_files) > 0:
                pos = max(self.join_files, key=itemgetter(0))[0] + 1
            else:
                pos = 0
            add_data = (pos, fp, filename, '')
            self.join_files.append(add_data)
            self.files_tree_widget.insert('', tk.END, text=filename, values=add_data)

    def save_as(self):
        save_filepath = self.parent.get_save_file(widget_title='Save Joined PDF to...')
        merger = PdfFileMerger()
        for f in sorted(self.join_files, key=itemgetter(0)):
            merger.append(fileobj=open(f[1], 'rb'))
        with open(save_filepath, 'wb') as out_pdf:
            merger.write(out_pdf)


class PyPDFBuilderApplication:
    def __init__(self):
        self.builder = pgBuilder()
        self.builder.add_from_file(os.path.join(CURRENT_DIR, 'mainwindow.ui'))

        self.mainwindow = self.builder.get_object('mainwindow')
        self.mainmenu = self.builder.get_object('MainMenu')
        self.mainwindow.config(menu=self.mainmenu)

        self.builder.connect_callbacks(self)

        self.jointab = JoinTabManager(self)

    def callback(self):
        pass

    def jointab_add_file(self):
        self.jointab.add_file()

    def jointab_save_as(self):
        self.jointab.save_as()

    def get_open_files(self, widget_title='Open Files...'):
        return filedialog.askopenfilenames(
            initialdir='/home/thomas/Dropbox/eBooks/',
            title=widget_title,
            filetypes=(("PDF File", "*.pdf"), ("All Files", "*.*"))
        )

    def get_save_file(self, widget_title='Save File...'):
        return filedialog.asksaveasfilename(
            title=widget_title,
            filetypes=(("PDF File", "*.pdf"), ("All Files", "*.*"))
        )

    def quit(self, event=None):
        self.mainwindow.quit()

    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = PyPDFBuilderApplication()
    app.run()
