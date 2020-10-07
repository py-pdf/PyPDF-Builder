#!/usr/bin/python

import os
import sys
import appdirs
import json
from pathlib import Path as plPath
from operator import itemgetter
from settings import *

from tkinter import filedialog
from pygubu import Builder as pgBuilder

# if dist fails to start because it's missing these, uncomment these two imports
# import pygubu.builder.ttkstdwidgets
# import pygubu.builder.widgets.dialog

from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter

# check to see if we're running from stand-alone one-file executable:
if hasattr(sys, '_MEIPASS'):
    CURRENT_DIR = sys._MEIPASS
else:
    CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
USER_DIR = str(plPath.home())
CONFIG_DIR = appdirs.user_config_dir(APPNAME)
DATA_DIR = appdirs.user_data_dir(APPNAME)


class SettingsData:
    '''Class for managing current user's application settings'''

    def __init__(self):
        self.__settings_data_path = os.path.join(CONFIG_DIR, 'data.json')
        self.__settings_defaults = {
            'use_poppler_tools': False,
        }
        self.__settings_data = self.__get_settings_data()

    @property
    def use_poppler_tools(self):
        '''If set to True, PyPDF Builder will first try to use Poppler Tools where possible
        to produce the desired PDFs.

        The getter will first try to return the value stored in the
        instance, then try to read it out of the user data file, and if all else fails,
        set it to False and return that value.

        The setter will set the according class instance property and save that property to
        a settings data file. If no such file exists yet, one will be created.
        '''
        return self.__settings_data.get('use_poppler_tools', self.__get_settings_data()['use_poppler_tools'])

    @use_poppler_tools.setter
    def use_poppler_tools(self, val):
        self.__settings_data['use_poppler_tools'] = val
        self.__save_settings_data()

    def __get_settings_data(self):
        '''Method to retrieve current user's settings data

        Return:
            dict: Dictionary of settings data with keys:
                * `use_poppler_tools`: user Poppler PDF tools by default
        '''
        try:
            with (open(self.__settings_data_path, 'r')) as datafile:
                settings_data = json.load(datafile)
            # make sure all values are returned. If a key is non-existant, fill it with default value
            for key, val in self.__settings_defaults.items():
                if key not in settings_data:
                    settings_data[key] = val
        except FileNotFoundError:
            settings_data = self.__settings_defaults
        return settings_data

    def __save_settings_data(self):
        if not os.path.exists(os.path.dirname(self.__settings_data_path)):
            plPath(os.path.dirname(self.__settings_data_path)).mkdir(parents=True, exist_ok=True)
        try:
            with (open(self.__settings_data_path, 'w')) as datafile:
                json.dump(self.__settings_data, datafile)
        except FileNotFoundError:
            print('Something went horribly wrong while trying to save your current user data.')


class UserData:
    '''Class for storing current user's application data'''

    def __init__(self):
        self.__user_data_path = os.path.join(DATA_DIR, 'data.json')
        self.__data_defaults = {
            'filedialog_path': USER_DIR,
            'number_of_processed_files': 0,
        }
        self.__user_data = self.__get_user_data()

    @property
    def filedialog_path(self):
        '''The last directory the user visited while opening or saving a file
        using a Tk File Dialog.

        The getter will first try to return the value stored in the
        instance, then try to read it out of the user data file, and if all else fails,
        set it to the user's home directory and return that value.

        The setter will set the according class instance property and save that property to
        a user data file. If no such file exists yet, one will be created.
        '''
        return self.__user_data.get('filedialog_path', self.__get_user_data()['filedialog_path'])

    @filedialog_path.setter
    def filedialog_path(self, val):
        self.__user_data['filedialog_path'] = val
        self.__save_user_data()

    @property
    def number_of_processed_files(self):
        '''Simple counter of PDF produced with PyPDF Builder

        The getter will first try to return the value stored in the state of the
        instance, then try to read it out of the user data file, and if all else fails,
        set it to 0 and return that value.

        The setter will set the according class instance property and save that property to
        a user data file. If no such file exists yet, one will be created.
        '''
        return self.__user_data.get('number_of_processed_files', self.__get_user_data()['number_of_processed_files'])

    @number_of_processed_files.setter
    def number_of_processed_files(self, val):
        self.__user_data['number_of_processed_files'] = val
        self.__save_user_data()

    def __get_user_data(self):
        '''Method to retrieve current user's data

        Return:
            dict: Dictionary of user data with keys:
                * `filedialog_path`: last accessed file path
                * `number_of_processed_files`: number of processed files
        '''
        try:
            with (open(self.__user_data_path, 'r')) as datafile:
                user_data = json.load(datafile)
            # make sure all values are returned. If a key is non-existant, fill it with default value
            for key, val in self.__data_defaults.items():
                if key not in user_data:
                    user_data[key] = val
        except FileNotFoundError:
            user_data = self.__data_defaults
        return user_data

    def __save_user_data(self):
        if not os.path.exists(os.path.dirname(self.__user_data_path)):
            plPath(os.path.dirname(self.__user_data_path)).mkdir(parents=True, exist_ok=True)
        try:
            with (open(self.__user_data_path, 'w')) as datafile:
                json.dump(self.__user_data, datafile)
        except FileNotFoundError:
            print('Something went horribly wrong while trying to save your current user data.')


class PDFInfo:
    '''File info class for PDF files.

    Instances of this class show information about PDF files that are being edited in
    PyPDF Builder.

    Args:
        filepath (str): Path to PDF File
    '''

    def __init__(self, filepath):
        self.__filepath = filepath

    @property
    def pages(self):
        '''int: Number of pages contained in PDF file'''
        with open(self.__filepath, 'rb') as in_pdf:
            pdf_handler = PdfFileReader(in_pdf)
            return pdf_handler.getNumPages()

    def concat_filename(self, max_length=35):
        '''Concatenate a filename to a certain length.

        Args:
            max_length (int): Maximum length of concatenated string (default: 35)

        Returns:
            str: Filename of PDFInfo-object concatenated to max length of `max_length`

        '''
        basename = os.path.basename(self.__filepath)
        concat_filename = f'{basename[0:max_length]}'
        if len(basename) > max_length:
            concat_filename += '…'
        return concat_filename

    def pdf_info_string(self, concat_length=35):
        '''Fetch a standard info-string about the PDFInfo-object.

        Args:
            concat_length (int): Maximum length of concatenated filename string (default: 35)

        Returns:
            str: Information in the format `Filename (pages)` of PDFInfo-object

        '''
        concat_filename = self.concat_filename(max_length=concat_length)
        return f'{concat_filename} ({self.pages} pages)'


class BgTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.__source_filepath = None
        self.__bg_filepath = None
        self.__source_file_info = None
        self.__bg_file_info = None
        self.__bg_pdf_pages = None
        self.__source_file_info_widget = self.parent.builder.get_variable('source_file_info')
        self.__bg_file_info_widget = self.parent.builder.get_variable('bg_file_info')
        self.__bg_command = self.parent.builder.get_variable('bg_command')
        self.__bg_only_first_page = self.parent.builder.get_variable('bg_only_first_page')
        self.__bg_button_label = self.parent.builder.get_variable('bg_options_bg_button')
        self.__only_first_button_label = self.parent.builder.get_variable('bg_options_only_first_button')
        self.__bg_command.set('BG')

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def choose_source_file(self):
        choose_source_file = self.parent.get_file_dialog(
            func=filedialog.askopenfilename, widget_title='Choose Source PDF …')
        if choose_source_file:
            self.__source_filepath = choose_source_file
            self.__source_file_info = PDFInfo(self.__source_filepath)
            self.__show_source_file_info()

    def choose_bg_file(self):
        choose_bg_file = self.parent.get_file_dialog(
            func=filedialog.askopenfilename, widget_title='Choose Background PDF …')
        if choose_bg_file:
            self.__bg_filepath = choose_bg_file
            self.__bg_file_info = PDFInfo(self.__bg_filepath)
            self.__show_bg_file_info()

    def __show_source_file_info(self):
        self.__source_file_info_widget.set(self.__source_file_info.pdf_info_string(concat_length=80))

    def __show_bg_file_info(self):
        self.__bg_file_info_widget.set(self.__bg_file_info.pdf_info_string(concat_length=80))

    def choose_stamp_option(self):
        self.__only_first_button_label.set('Apply stamp to only the first page')
        self.__bg_button_label.set('Choose Stamp …')

    def choose_bg_option(self):
        self.__only_first_button_label.set('Apply background to only the first page')
        self.__bg_button_label.set('Choose Background …')

    def save_as(self):
        save_filepath = self.parent.get_file_dialog(func=filedialog.asksaveasfilename, widget_title='Save New PDF to …')
        if self.__source_filepath and self.__bg_filepath:
            out_pdf = PdfFileWriter()
            command = self.__bg_command.get()
            with open(self.__source_filepath, "rb") as source_pdf_stream, \
                    open(self.__bg_filepath, "rb") as bg_pdf_stream:
                for p in range(self.__source_file_info.pages):
                    # new PdfFileReader instances needed for every page merged. See here:
                    # https://github.com/mstamy2/PyPDF2/issues/100#issuecomment-43145634
                    source_pdf = PdfFileReader(source_pdf_stream)
                    bg_pdf = PdfFileReader(bg_pdf_stream)
                    if not self.__bg_only_first_page.get() or (self.__bg_only_first_page.get() and p < 1):
                        if command == 'STAMP':
                            top_page = bg_pdf.getPage(0)
                            bottom_page = source_pdf.getPage(p)
                        elif command == 'BG':
                            top_page = source_pdf.getPage(p)
                            bottom_page = bg_pdf.getPage(0)
                        bottom_page.mergePage(top_page)
                    else:
                        bottom_page = source_pdf.getPage(p)
                    out_pdf.addPage(bottom_page)
                with open(save_filepath, "wb") as out_pdf_stream:
                    out_pdf.write(out_pdf_stream)
            self.parent.save_success(status_text=BG_FILE_SUCCESS.format(os.path.basename(save_filepath)))


class SplitTabManager:
    '''Manager class for the Split Tab

    An instance of this class manages all aspects of the Split Tab in the calling `PyPDFBuilderApplication` instance

    Args:
        parent (PyPDFBuilderApplication): Application that created the instance and that contains the Split Tab.
    '''

    def __init__(self, parent=None):
        self.parent = parent
        self.__split_filepath = None
        self.__split_file_info = None
        self.__split_file_info_widget = self.parent.builder.get_variable('split_file_info')

    @property
    def parent(self):
        '''PyPDFBuilderApplication: Application that created the instance and that contains the Split Tab.'''
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def open_file(self):
        choose_split_file = self.parent.get_file_dialog(
            func=filedialog.askopenfilename, widget_title='Choose PDF to Split…')
        if choose_split_file:
            self.__split_filepath = choose_split_file
            self.__split_file_info = PDFInfo(self.__split_filepath)
            self.__show_file_info()

    def __show_file_info(self):
        self.__split_file_info_widget.set(self.__split_file_info.pdf_info_string())

    def save_as(self):
        if self.__split_filepath:
            basepath = os.path.splitext(self.__split_filepath)[0]
            # in spite of discussion here https://stackoverflow.com/a/2189814
            # we'll just go the lazy way to count the number of needed digits:
            num_length = len(str(abs(self.__split_file_info.pages)))
            in_pdf = PdfFileReader(open(self.__split_filepath, "rb"))
            for p in range(self.__split_file_info.pages):
                output_path = f"{basepath}_{str(p+1).rjust(num_length, '0')}.pdf"
                out_pdf = PdfFileWriter()
                out_pdf.addPage(in_pdf.getPage(p))
                with open(output_path, "wb") as out_pdf_stream:
                    out_pdf.write(out_pdf_stream)
            self.parent.save_success(status_text=SPLIT_FILE_SUCCESS.format(os.path.dirname(self.__split_filepath)))


class RotateTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.__rotate_filepath = None
        self.__rotate_file_info = None
        self.__rotate_file_info_widget = self.parent.builder.get_variable('rotate_file_info')
        self.__rotate_from_page_widget = self.parent.builder.get_variable('rotate_from_page')
        self.__rotate_to_page_widget = self.parent.builder.get_variable('rotate_to_page')
        self.__rotate_amount_widget = self.parent.builder.get_variable('rotate_amount')
        self.__do_page_extract_widget = self.parent.builder.get_variable('do_extract_pages')
        # Set default values. No idea how to avoid this using only the UI file, so I'm
        # breaking the MVC principle here.
        self.__rotate_amount_widget.set('NO_ROTATE')
        self.__rotate_from_page_widget.set('')
        self.__rotate_to_page_widget.set('')
        self.__do_page_extract_widget.set(True)

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def open_file(self):
        chose_rotate_file = self.parent.get_file_dialog(
            func=filedialog.askopenfilename, widget_title='Choose PDF to Rotate…')
        if chose_rotate_file:
            self.__rotate_filepath = chose_rotate_file
            self.__rotate_file_info = PDFInfo(self.__rotate_filepath)
            self.__show_file_info()
            self.__show_rotate_pages()

    def __show_rotate_pages(self):
        self.__rotate_from_page_widget.set(1)
        self.__rotate_to_page_widget.set(self.__rotate_file_info.pages)

    def __show_file_info(self):
        self.__rotate_file_info_widget.set(self.__rotate_file_info.pdf_info_string())

    def save_as(self):
        page_range = (self.__rotate_from_page_widget.get()-1, self.__rotate_to_page_widget.get())
        save_filepath = self.parent.get_file_dialog(func=filedialog.asksaveasfilename, widget_title='Save New PDF to…')
        if self.__rotate_filepath:
            in_pdf = PdfFileReader(open(self.__rotate_filepath, "rb"))
            out_pdf = PdfFileWriter()
            for p in range(self.__rotate_file_info.pages):
                if p in range(*page_range):
                    if ROTATE_DEGREES[self.__rotate_amount_widget.get()] != 0:            
                        out_pdf.addPage(in_pdf.getPage(p).rotateClockwise(
                            ROTATE_DEGREES[self.__rotate_amount_widget.get()]))
                    else:
                        out_pdf.addPage(in_pdf.getPage(p))
                elif not self.__do_page_extract_widget.get():
                    out_pdf.addPage(in_pdf.getPage(p))
            with open(save_filepath, "wb") as out_pdf_stream:
                out_pdf.write(out_pdf_stream)
            self.parent.save_success(status_text=ROTATE_FILE_SUCCESS.format(os.path.basename(save_filepath)))


class JoinTabManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.__current_file_info = None
        self.__files_tree_widget = self.parent.builder.get_object('JoinFilesList')
        self.__files_tree_widget['displaycolumns'] = ('FileNameColumn', 'PageSelectColumn')
        self.__current_file_info_widget = self.parent.builder.get_variable('current_file_info')
        self.__page_select_input_widget = self.parent.builder.get_variable('page_select_input')
        self.__selected_files = []

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, val):
        self.__parent = val

    def on_file_select(self, event):
        self.__selected_files = self.__files_tree_widget.selection()
        self.__current_file_info = PDFInfo(
            self.__files_tree_widget.item(self.__selected_files[0], 'values')[PDF_FILEPATH])
        self.__show_file_info()
        self.__show_selected_pages()

    def enter_page_selection(self, event):
        '''
        This medthod is called when the page selection input field loses focus
        i.e. when input is completed
        '''
        for f in self.__selected_files:
            file_data = self.__files_tree_widget.item(f, 'values')
            page_select = self.__page_select_input_widget.get()
            new_tuple = (file_data[PDF_FILENAME], page_select, file_data[PDF_FILEPATH], file_data[PDF_PAGES])
            self.__files_tree_widget.item(f, values=new_tuple)

    def __show_file_info(self):
        self.__current_file_info_widget.set(self.__current_file_info.pdf_info_string(concat_length=25))

    def __show_selected_pages(self):
        file_data = self.__files_tree_widget.item(self.__selected_files[0], 'values')
        self.__page_select_input_widget.set(file_data[PDF_PAGESELECT])

    def __get_join_files(self):
        return [self.__files_tree_widget.item(i)['values'] for i in self.__files_tree_widget.get_children()]

    def __parse_page_select(self, page_select):
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
        add_filepaths = self.parent.get_file_dialog(
            func=filedialog.askopenfilenames,
            widget_title='Choose PDFs to Add…'
        )
        if add_filepaths:
            for filepath in list(add_filepaths):
                filename = os.path.basename(filepath)
                file_info = PDFInfo(filepath)
                file_data = (filename, '', filepath, file_info.pages)
                self.__files_tree_widget.insert('', 'end', values=file_data)

    def save_as(self):
        if len(self.__get_join_files()) > 0:
            save_filepath = self.parent.get_file_dialog(
                func=filedialog.asksaveasfilename, widget_title='Save Joined PDF to…')
            if save_filepath:
                merger = PdfFileMerger()
                for f in self.__get_join_files():
                    if not f[PDF_PAGESELECT]:
                        merger.append(fileobj=open(f[PDF_FILEPATH], 'rb'))
                    else:
                        for page_range in self.__parse_page_select(str(f[PDF_PAGESELECT])):
                            merger.append(fileobj=open(f[PDF_FILEPATH], 'rb'), pages=page_range)
                with open(save_filepath, 'wb') as out_pdf:
                    merger.write(out_pdf)
                self.parent.save_success(status_text=JOIN_FILE_SUCCESS.format(os.path.basename(save_filepath)))

    def move_up(self):
        selected_files = self.__selected_files
        first_idx = self.__files_tree_widget.index(selected_files[0])
        parent = self.__files_tree_widget.parent(selected_files[0])
        if first_idx > 0:
            for f in selected_files:
                swap_item = self.__files_tree_widget.prev(f)
                new_idx = self.__files_tree_widget.index(swap_item)
                self.__files_tree_widget.move(f, parent, new_idx)

    def move_down(self):
        selected_files = list(reversed(self.__selected_files))
        last_idx = self.__files_tree_widget.index(selected_files[0])
        parent = self.__files_tree_widget.parent(selected_files[0])
        last_idx_in_widget = self.__files_tree_widget.index(self.__files_tree_widget.get_children()[-1])
        if last_idx < last_idx_in_widget:
            for f in selected_files:
                swap_item = self.__files_tree_widget.next(f)
                own_idx = self.__files_tree_widget.index(f)
                new_idx = self.__files_tree_widget.index(swap_item)
                self.__files_tree_widget.move(f, parent, new_idx)

    def remove_file(self):
        for f in self.__selected_files:
            self.__files_tree_widget.detach(f)


class PyPDFBuilderApplication:
    '''Main application class. Handles setup and running of all application parts.'''

    def __init__(self):
        self.builder = pgBuilder()
        self.builder.add_from_file(os.path.join(CURRENT_DIR, 'mainwindow.ui'))

        self.__mainwindow = self.builder.get_object('MainWindow')
        self.__settings_dialog = self.builder.get_object('SettingsDialog', self.__mainwindow)
        self.__notebook = self.builder.get_object('AppNotebook')
        self.__tabs = {
            'join': self.builder.get_object('JoinFrame'),
            'split': self.builder.get_object('SplitFrame'),
            'bg': self.builder.get_object('BgFrame'),
            'rotate': self.builder.get_object('RotateFrame'),
        }
        self.__mainmenu = self.builder.get_object('MainMenu')
        self.__mainwindow.config(menu=self.__mainmenu)
        self.__status_text_variable = self.builder.get_variable('application_status_text')
        self.__settings_use_poppler_variable = self.builder.get_variable('settings_use_poppler')
        self.status_text = None
        self.builder.connect_callbacks(self)

        self.user_data = UserData()
        self.settings_data = SettingsData()

        self.__jointab = JoinTabManager(self)
        self.__splittab = SplitTabManager(self)
        self.__bgtab = BgTabManager(self)
        self.__rotatetab = RotateTabManager(self)

        self.status_text = DEFAULT_STATUS

    @property
    def status_text(self):
        return self.__status_text_variable.get()

    @status_text.setter
    def status_text(self, val):
        self.__status_text_variable.set(val)

    # boy oh boy if there's anyway to do these callsbacks more elegantly, please let me gain that knowledge!
    def select_tab_join(self, *args, **kwargs):
        '''Gets called when menu item "View > Join Files" is selected.
        Pops appropriate tab into view.'''
        self.__notebook.select(self.__tabs['join'])

    def select_tab_split(self, *args, **kwargs):
        '''Gets called when menu item "View > Split File" is selected.
        Pops appropriate tab into view.'''
        self.__notebook.select(self.__tabs['split'])

    def select_tab_bg(self, *args, **kwargs):
        '''Gets called when menu item "View > Background/Stamp/Number" is selected.
        Pops appropriate tab into view.'''
        self.__notebook.select(self.__tabs['bg'])

    def select_tab_rotate(self, *args, **kwargs):
        '''Gets called when menu item "View > Rotate Pages" is selected.
        Pops appropriate tab into view.'''
        self.__notebook.select(self.__tabs['rotate'])

    def jointab_add_file(self):
        self.__jointab.add_file()

    def jointab_on_file_select(self, event):
        self.__jointab.on_file_select(event)

    def jointab_enter_page_selection(self, event):
        self.__jointab.enter_page_selection(event)

    def jointab_save_as(self):
        self.__jointab.save_as()

    def jointab_move_up(self):
        self.__jointab.move_up()

    def jointab_move_down(self):
        self.__jointab.move_down()

    def jointab_remove(self):
        self.__jointab.remove_file()

    def splittab_open_file(self):
        self.__splittab.open_file()

    def splittab_save_as(self):
        self.__splittab.save_as()

    def bgtab_choose_bg_option(self):
        self.__bgtab.choose_bg_option()

    def bgtab_choose_stamp_option(self):
        self.__bgtab.choose_stamp_option()

    def bgtab_choose_number_option(self):
        '''
        Numbering pages is currently not supported by PyPDF2 so this option will remain
        disabled for now
        '''
        pass

    def bgtab_choose_source_file(self):
        self.__bgtab.choose_source_file()

    def bgtab_choose_bg_file(self):
        self.__bgtab.choose_bg_file()

    def bgtab_save_as(self):
        self.__bgtab.save_as()

    def rotatetab_open_file(self):
        self.__rotatetab.open_file()

    def rotatetab_save_as(self):
        self.__rotatetab.save_as()

    def save_success(self, status_text=DEFAULT_STATUS):
        '''Gets called when a PDF file was processed successfully. Currently only
        increases the `number_of_processed_files`-counter by 1
        '''
        self.user_data.number_of_processed_files += 1
        self.status_text = status_text

    def show_settings(self, *args, **kwargs):
        '''Shows the settings dialog. The close event is handled by `self.close_settings()`
        and all the settings management is handled there. Args and kwargs are included in
        method definition in case it is triggered by the keyboard shortcut, in which
        case `event` gets passed into the call.'''
        self.__settings_dialog.run()
        self.__settings_use_poppler_variable.set(self.settings_data.use_poppler_tools)

    def close_settings(self, *args, **kwargs):
        self.settings_data.use_poppler_tools = self.__settings_use_poppler_variable.get()
        self.__settings_dialog.close()

    def cancel_settings(self, *args, **kwargs):
        pass

    def get_file_dialog(self, func, widget_title='Choose File(s) …'):
        f = func(
            initialdir=self.user_data.filedialog_path,
            title=widget_title,
            filetypes=(("PDF File", "*.pdf"), ("All Files", "*.*"))
        )
        if f:
            if type(f) == list or type(f) == tuple:
                self.user_data.filedialog_path = os.path.dirname(f[-1])
            elif type(f) == str:
                self.user_data.filedialog_path = os.path.dirname(f)
            return f

    def quit(self, event=None):
        self.__mainwindow.quit()

    def run(self):
        self.__mainwindow.mainloop()


if __name__ == '__main__':
    app = PyPDFBuilderApplication()
    app.run()
