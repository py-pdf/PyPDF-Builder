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
        self.current_file_info = self.parent.builder.get_variable('current_file_info')
        self.selected_files = []

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    @property
    def selected_files(self):
        return self.__selected_files

    @selected_files.setter
    def selected_files(self, val):
        self.__selected_files = val

    def on_file_select(self, event):
        self.selected_files = self.files_tree_widget.selection()
        self.show_file_info()

    def show_file_info(self):
        file_data = self.files_tree_widget.item(self.selected_files[0], 'values')
        self.current_file_info.set(f'{file_data[PDF_FILENAME][0:25]}...({file_data[PDF_PAGES]} pages)')

    def get_join_files(self):
        join_files = []
        for i in self.files_tree_widget.get_children():
            yield self.files_tree_widget.item(i)['values']

    def parse_page_select(self, page_select):
        '''
        As this method deals with raw user input, there will have to be a whole lot of error checking
        built into this function at a later time. Really don't look forward to this... at all.
        '''
        if page_select == '':
            yield 'all'
        for page_range in page_select.replace(' ', '').split(','):
            for sep in ':-':
                if sep in page_range:
                    range_list = page_range.split(sep)
                    yield set(sorted((int(range_list[0])-1, int(range_list[1]))))
                else:
                    yield set(sorted((int(page_range)-1, int(page_range))))

    def add_file(self):
        add_filepaths = list(self.parent.get_open_files(widget_title='Choose PDFs to Add...'))
        for fp in add_filepaths:
            filename = os.path.basename(fp)
            with open(fp, 'rb') as in_pdf:
                pdf_handler = PdfFileReader(in_pdf)
                pages = pdf_handler.getNumPages()
            file_data = (fp, filename, pages, '')
            self.files_tree_widget.insert('', tk.END, text=filename, values=file_data)

    def save_as(self):
        save_filepath = self.parent.get_save_file(widget_title='Save Joined PDF to...')
        merger = PdfFileMerger()
        for f in self.get_join_files():
            for page_range in self.parse_page_select(f[PDF_PAGESELECT]):
                if page_range == 'all':
                    merger.append(fileobj=open(f[PDF_FILEPATH], 'rb'))
                else:
                    merger.append(fileobj=open(f[PDF_FILEPATH], 'rb'), pages=page_range)
        with open(save_filepath, 'wb') as out_pdf:
            merger.write(out_pdf)

    def move_up(self):
        selected_files = self.selected_files
        first_idx = self.files_tree_widget.index(selected_files[0])
        parent = self.files_tree_widget.parent(selected_files[0])
        if first_idx > 0:
            for f in selected_files:
                swap_item = self.files_tree_widget.prev(f)
                new_idx = self.files_tree_widget.index(swap_item)
                self.files_tree_widget.move(f, parent, new_idx)

    def move_down(self):
        selected_files = list(reversed(self.selected_files))
        last_idx = self.files_tree_widget.index(selected_files[0])
        parent = self.files_tree_widget.parent(selected_files[0])
        last_idx_in_widget =  self.files_tree_widget.index(self.files_tree_widget.get_children()[-1])
        if last_idx < last_idx_in_widget:
            for f in selected_files:
                swap_item = self.files_tree_widget.next(f)
                own_idx = self.files_tree_widget.index(f)
                new_idx = self.files_tree_widget.index(swap_item)
                self.files_tree_widget.move(f, parent, new_idx)

    def remove_file(self):
        for f in self.selected_files:
            self.files_tree_widget.detach(f)


class PyPDFBuilderApplication:
    def __init__(self):
        self.builder = pgBuilder()
        self.builder.add_from_file(os.path.join(CURRENT_DIR, 'mainwindow.ui'))

        self.mainwindow = self.builder.get_object('mainwindow')
        self.mainmenu = self.builder.get_object('MainMenu')
        self.mainwindow.config(menu=self.mainmenu)

        self.builder.connect_callbacks(self)

        self.jointab = JoinTabManager(self)

    def jointab_add_file(self):
        self.jointab.add_file()

    def jointab_save_as(self):
        self.jointab.save_as()

    def jointab_move_up(self):
        self.jointab.move_up()

    def jointab_move_down(self):
        self.jointab.move_down()

    def jointab_remove(self):
        self.jointab.remove_file()

    def get_open_files(self, widget_title='Open Files...'):
        return filedialog.askopenfilenames(
            # initialdir='/home/thomas/Dropbox/eBooks/',
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
