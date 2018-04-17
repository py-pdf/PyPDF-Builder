#!/usr/bin/python

import os
from pathlib import Path as plPath
from operator import itemgetter
from settings import *

from tkinter import filedialog
from pygubu import Builder as pgBuilder
from pygubu.builder import ttkstdwidgets

from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
USER_DIR = str(plPath.home())


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
        choose_split_file = self.parent.get_open_file(widget_title='Choose PDF to Split…')
        if choose_split_file:
            self.split_filepath = choose_split_file
            with open(self.split_filepath, 'rb') as in_pdf:
                pdf_handler = PdfFileReader(in_pdf)
                self.pdf_pages = pdf_handler.getNumPages()
            self.show_file_info()

    def show_file_info(self):
        filename = os.path.basename(self.split_filepath)
        self.split_file_info.set(f'{filename[0:35]}…({self.pdf_pages} pages)')

    def save_as(self):
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
        self.rotate_amount = self.parent.builder.get_variable('rotate_amount')
        # Set default values. No idea how to avoid this using only the UI file, so I'm
        # breaking the MVC principle here.
        self.rotate_amount.set(None)
        self.rotate_from_page.set('')
        self.rotate_to_page.set('')

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def open_file(self):
        '''
        Use interim variable for path in case there was a file already selected, then user
        opens file dialog again and presses cancel. In this case, '' gets returned and would
        overwrite the old filepath
        '''
        chose_rotate_file = self.parent.get_open_file(widget_title='Choose PDF to Rotate…')
        if chose_rotate_file:
            self.rotate_filepath = chose_rotate_file
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
        self.rotate_file_info.set(f'{filename[0:35]}…({self.pdf_pages} pages)')

    def save_as(self):
        page_range = (self.rotate_from_page.get()-1, self.rotate_to_page.get())
        save_filepath = self.parent.get_save_file(widget_title='Save New PDF to…')
        if self.rotate_filepath:
            in_pdf = PdfFileReader(open(self.rotate_filepath, "rb"))
            out_pdf = PdfFileWriter()
            for p in range(self.pdf_pages):
                if p in range(*page_range):
                    out_pdf.addPage(in_pdf.getPage(p).rotateClockwise(ROTATE_DEGREES[self.rotate_amount.get()]))
                else:
                    out_pdf.addPage(in_pdf.getPage(p))
            with open(save_filepath, "wb") as out_pdf_stream:
                out_pdf.write(out_pdf_stream)


class JoinTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.files_tree_widget = self.parent.builder.get_object('JoinFilesList')
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
        self.current_file_info.set(f'{file_data[PDF_FILENAME][0:25]}…({file_data[PDF_PAGES]} pages)')

    def show_selected_pages(self):
        file_data = self.files_tree_widget.item(self.selected_files[0], 'values')
        self.page_select_input.set(file_data[PDF_PAGESELECT])

    def get_join_files(self):
        return [self.files_tree_widget.item(i)['values'] for i in self.files_tree_widget.get_children()]

    def parse_page_select(self, page_select):
        '''
        As this method deals with raw user input, there will have to be a whole lot of error checking
        built into this function at a later time. Really don't look forward to this… at all.
        '''
        for page_range in page_select.replace(' ', '').split(','):
            if '-' in page_range:
                range_list = page_range.split('-')
                yield tuple(sorted((int(range_list[0])-1, int(range_list[1]))))
            else:
                yield tuple(sorted((int(page_range)-1, int(page_range))))

    def add_file(self):
        add_filepaths = self.parent.get_open_files(widget_title='Choose PDFs to Add…')
        if add_filepaths:
            for filepath in list(add_filepaths):
                filename = os.path.basename(filepath)
                with open(filepath, 'rb') as in_pdf:
                    pdf_handler = PdfFileReader(in_pdf)
                    pages = pdf_handler.getNumPages()
                file_data = (filename, '', filepath, pages)
                self.files_tree_widget.insert('', 'end', values=file_data)

    def save_as(self):
        if len(self.get_join_files()) > 0:
            save_filepath = self.parent.get_save_file(widget_title='Save Joined PDF to…')
            if save_filepath:
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
        self.notebook = self.builder.get_object('AppNotebook')
        self.tabs = {
            'join': self.builder.get_object('JoinFrame'),
            'split': self.builder.get_object('SplitFrame'),
            'bg': self.builder.get_object('BgFrame'),
            'rotate': self.builder.get_object('RotateFrame'),
        }
        self.mainwindow.bind_all('<Control-j>', self.select_tab_join)
        self.mainwindow.bind_all('<Control-s>', self.select_tab_split)
        self.mainwindow.bind_all('<Control-b>', self.select_tab_bg)
        self.mainwindow.bind_all('<Control-r>', self.select_tab_rotate)
        self.mainmenu = self.builder.get_object('MainMenu')
        self.mainwindow.config(menu=self.mainmenu)

        self.builder.connect_callbacks(self)

        # Todo get pickled data: last directory visited by user
        self.__current_dir = USER_DIR

        self.jointab = JoinTabManager(self)
        self.splittab = SplitTabManager(self)
        self.rotatetab = RotateTabManager(self)

    # boy oh boy if there's anyway to do these callsbacks more elegantly, please let me gain that knowledge!
    def select_tab_join(self, *args, **kwargs):
        self.notebook.select(self.tabs['join'])
    def select_tab_split(self, *args, **kwargs):
        self.notebook.select(self.tabs['split'])
    def select_tab_bg(self, *args, **kwargs):
        self.notebook.select(self.tabs['bg'])
    def select_tab_rotate(self, *args, **kwargs):
        self.notebook.select(self.tabs['rotate'])

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

    def rotatetab_save_as(self):
        self.rotatetab.save_as()

    def get_open_files(self, widget_title='Open Files…'):
        f = filedialog.askopenfilenames(
            initialdir=self.__current_dir,
            title=widget_title,
            filetypes=(("PDF File", "*.pdf"), ("All Files", "*.*"))
        )
        if f:
            self.__current_dir = os.path.dirname(f[-1])
            return f

    def get_open_file(self, widget_title='Open File…'):
        f = filedialog.askopenfilename(
            initialdir=self.__current_dir,
            title=widget_title,
            filetypes=(("PDF File", "*.pdf"), ("All Files", "*.*"))
        )
        if f:
            self.__current_dir = os.path.dirname(f)
            return f

    def get_save_file(self, widget_title='Save File…'):
        f = filedialog.asksaveasfilename(
            initialdir=self.__current_dir,
            title=widget_title,
            filetypes=(("PDF File", "*.pdf"), ("All Files", "*.*"))
        )
        if f:
            self.__current_dir = os.path.dirname(f)
            return f

    def quit(self, event=None):
        self.mainwindow.quit()

    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = PyPDFBuilderApplication()
    app.run()
