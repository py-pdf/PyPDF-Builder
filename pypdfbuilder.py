#!/usr/bin/python

import os
from operator import itemgetter
from settings import *

import tkinter as tk
from tkinter import filedialog
from pygubu import Builder as pgBuilder

from PyPDF2 import PdfFileMerger, PdfFileReader

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


class JoinTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.files_tree_widget = self.parent.builder.get_object('JoinFilesList')
        self.files_tree_widget.bind("<<TreeviewSelect>>", self.on_file_select)
        self.join_files = []    # Format for entries: (pos, filepath, filename, pages)
        self.current_file_info = self.parent.builder.get_variable('current_file_info')

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def on_file_select(self, event):
        selected_file = self.files_tree_widget.selection()[0]
        file_data = self.files_tree_widget.item(selected_file, 'values')
        # Concat value
        self.current_file_info.set(f'{file_data[PDF_FILENAME][0:25]}...({file_data[PDF_PAGES]} pages)')

    def add_file(self):
        add_filepaths = list(self.parent.get_open_files(widget_title='Choose PDFs to Add...'))
        # print(f'Return value: {add_filepaths}\nListed: {add_filepath_list}')
        for fp in add_filepaths:
            filename = os.path.basename(fp)
            if len(self.join_files) > 0:
                pos = max(self.join_files, key=itemgetter(PDF_POSITION))[PDF_POSITION] + 1
            else:
                pos = 0
            with open(fp, 'rb') as in_pdf:
                pdf_handler = PdfFileReader(in_pdf)
                pages = pdf_handler.getNumPages()
            file_data = [pos, fp, filename, pages, '']
            id = self.files_tree_widget.insert('', tk.END, text=filename, values=file_data)
            file_data.append(id)             # reference to the widget item id
            self.join_files.append(file_data)

    def save_as(self):
        save_filepath = self.parent.get_save_file(widget_title='Save Joined PDF to...')
        merger = PdfFileMerger()
        for f in sorted(self.join_files, key=itemgetter(PDF_POSITION)):
            merger.append(fileobj=open(f[1], 'rb'))
        with open(save_filepath, 'wb') as out_pdf:
            merger.write(out_pdf)

    def move_up(self):
        selected_files = self.files_tree_widget.selection()
        first_idx = self.files_tree_widget.index(selected_files[0])
        parent = self.files_tree_widget.parent(selected_files[0])
        if first_idx > 0:
            for f in selected_files:
                swap_item = self.files_tree_widget.prev(f)
                new_idx = self.files_tree_widget.index(swap_item)
                self.files_tree_widget.move(f, parent, new_idx)

    def move_down(self):
        selected_files = list(reversed(self.files_tree_widget.selection()))
        last_idx = self.files_tree_widget.index(selected_files[0])
        parent = self.files_tree_widget.parent(selected_files[0])
        last_idx_in_widget =  self.files_tree_widget.index(self.files_tree_widget.get_children()[-1])
        if last_idx < last_idx_in_widget:
            for f in selected_files:
                swap_item = self.files_tree_widget.next(f)
                own_idx = self.files_tree_widget.index(f)
                new_idx = self.files_tree_widget.index(swap_item)
                self.files_tree_widget.move(f, parent, new_idx)

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

    def jointab_move_up(self):
        self.jointab.move_up()

    def jointab_move_down(self):
        self.jointab.move_down()

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
