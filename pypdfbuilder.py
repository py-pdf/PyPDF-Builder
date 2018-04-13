#!/usr/bin/python

import os
from operator import itemgetter
from settings import *

import tkinter as tk
from tkinter import filedialog
from pygubu import Builder as pgBuilder

from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


class SplitTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.split_filepath = None
        self.pdf_pages = None
        self.split_file_info = self.parent.builder.get_variable('split_file_info')

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def open_file(self):
        self.split_filepath = self.parent.get_open_file(widget_title='Choose PDF to Split...')
        with open(self.split_filepath, 'rb') as in_pdf:
            pdf_handler = PdfFileReader(in_pdf)
            self.pdf_pages = pdf_handler.getNumPages()
        self.show_file_info()

    def show_file_info(self):
        filename = os.path.basename(self.split_filepath)
        self.split_file_info.set(f'{filename[0:35]}...({self.pdf_pages} pages)')

    def save_as(self):
        # Todo: check if there is an input file. Otherwise, do nothing
        if self.split_filepath:
            basepath = os.path.splitext(self.split_filepath)[0]
            # in spite of discussion here https://stackoverflow.com/a/2189814
            # we'll just go the lazy way to count the number of needed digits:
            num_length = len(str(abs(self.pdf_pages)))
            in_pdf = PdfFileReader(open(self.split_filepath, "rb"))
            for p in range(self.pdf_pages):
                output_path = f"{basepath}_{str(p+1).rjust(num_length, '0')}.pdf"
                out_pdf = PdfFileWriter()
                out_pdf.addPage(in_pdf.getPage(p))
                with open(output_path, "wb") as out_pdf_stream:
                    out_pdf.write(out_pdf_stream)


class RotateTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.rotate_filepath = None
        self.pdf_pages = None
        self.rotate_file_info = self.parent.builder.get_variable('rotate_file_info')
        self.rotate_from_page = self.parent.builder.get_variable('rotate_from_page')
        self.rotate_to_page = self.parent.builder.get_variable('rotate_to_page')

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def open_file(self):
        self.rotate_filepath = self.parent.get_open_file(widget_title='Choose PDF to Rotate...')
        with open(self.rotate_filepath, 'rb') as in_pdf:
            pdf_handler = PdfFileReader(in_pdf)
            self.pdf_pages = pdf_handler.getNumPages()
        self.show_file_info()
        self.show_rotate_pages()

    def show_rotate_pages(self):
        self.rotate_from_page.set(1)
        self.rotate_to_page.set(self.pdf_pages)

    def show_file_info(self):
        filename = os.path.basename(self.rotate_filepath)
        self.rotate_file_info.set(f'{filename[0:35]}...({self.pdf_pages} pages)')

    def save_as(self):
        # Todo: check if there is an input file. Otherwise, do nothing
        if self.rotate_filepath:
            basepath = os.path.splitext(self.rotate_filepath)[0]
            # in spite of discussion here https://stackoverflow.com/a/2189814
            # we'll just go the lazy way to count the number of needed digits:
            num_length = len(str(abs(self.pdf_pages)))
            in_pdf = PdfFileReader(open(self.rotate_filepath, "rb"))
            for p in range(self.pdf_pages):
                output_path = f"{basepath}_{str(p+1).rjust(num_length, '0')}.pdf"
                out_pdf = PdfFileWriter()
                out_pdf.addPage(in_pdf.getPage(p))
                with open(output_path, "wb") as out_pdf_stream:
                    out_pdf.write(out_pdf_stream)


class JoinTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.files_tree_widget = self.parent.builder.get_object('JoinFilesList')
        # self.files_tree_widget['columns'] = (0,0)
        self.files_tree_widget['displaycolumns'] = ('FileNameColumn', 'PageSelectColumn')
        self.current_file_info = self.parent.builder.get_variable('current_file_info')
        self.page_select_input = self.parent.builder.get_variable('page_select_input')
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
        self.show_selected_pages()

    def enter_page_selection(self, event):
        '''
        This medthod is called when the page selection input field loses focus
        i.e. when input is completed
        '''
        for f in self.selected_files:
            file_data = self.files_tree_widget.item(f, 'values')
            page_select = self.page_select_input.get()
            new_tuple = (file_data[PDF_FILENAME], page_select, file_data[PDF_FILEPATH], file_data[PDF_PAGES])
            self.files_tree_widget.item(f, values=new_tuple)

    def show_file_info(self):
        file_data = self.files_tree_widget.item(self.selected_files[0], 'values')
        self.current_file_info.set(f'{file_data[PDF_FILENAME][0:25]}...({file_data[PDF_PAGES]} pages)')

    def show_selected_pages(self):
        file_data = self.files_tree_widget.item(self.selected_files[0], 'values')
        self.page_select_input.set(file_data[PDF_PAGESELECT])

    def get_join_files(self):
        join_files = []
        for i in self.files_tree_widget.get_children():
            yield self.files_tree_widget.item(i)['values']

    def parse_page_select(self, page_select):
        '''
        As this method deals with raw user input, there will have to be a whole lot of error checking
        built into this function at a later time. Really don't look forward to this... at all.
        '''
        for page_range in page_select.replace(' ', '').split(','):
            if '-' in page_range:
                range_list = page_range.split('-')
                yield tuple(sorted((int(range_list[0])-1, int(range_list[1]))))
            else:
                yield tuple(sorted((int(page_range)-1, int(page_range))))

    def add_file(self):
        add_filepaths = list(self.parent.get_open_files(widget_title='Choose PDFs to Add...'))
        for filepath in add_filepaths:
            filename = os.path.basename(filepath)
            with open(filepath, 'rb') as in_pdf:
                pdf_handler = PdfFileReader(in_pdf)
                pages = pdf_handler.getNumPages()
            file_data = (filename, '', filepath, pages)
            self.files_tree_widget.insert('', tk.END, values=file_data)

    def save_as(self):
        if len(list(self.get_join_files())) > 0:
            # Todo: check if there are input files. Otherwise, do nothing
            save_filepath = self.parent.get_save_file(widget_title='Save Joined PDF to...')
            merger = PdfFileMerger()
            for f in self.get_join_files():
                if not f[PDF_PAGESELECT]:
                    merger.append(fileobj=open(f[PDF_FILEPATH], 'rb'))
                else:
                    for page_range in self.parse_page_select(str(f[PDF_PAGESELECT])):
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
        self.splittab = SplitTabManager(self)
        self.rotatetab = RotateTabManager(self)

    def jointab_add_file(self):
        self.jointab.add_file()

    def jointab_on_file_select(self, event):
        self.jointab.on_file_select(event)

    def jointab_enter_page_selection(self, event):
        self.jointab.enter_page_selection(event)

    def jointab_save_as(self):
        self.jointab.save_as()

    def jointab_move_up(self):
        self.jointab.move_up()

    def jointab_move_down(self):
        self.jointab.move_down()

    def jointab_remove(self):
        self.jointab.remove_file()

    def splittab_open_file(self):
        self.splittab.open_file()

    def splittab_save_as(self):
        self.splittab.save_as()

    def rotatetab_open_file(self):
        self.rotatetab.open_file()

    def get_open_files(self, widget_title='Open Files...'):
        return filedialog.askopenfilenames(
            # initialdir='/home/thomas/Dropbox/eBooks/',
            title=widget_title,
            filetypes=(("PDF File", "*.pdf"), ("All Files", "*.*"))
        )

    def get_open_file(self, widget_title='Open File...'):
        return filedialog.askopenfilename(
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
