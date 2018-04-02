from tkinter import *
from tkinter import ttk

class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        tab_control = ttk.Notebook(self.master)
        tab1 = ttk.Frame(tab_control)
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab1, text='First')
        tab_control.add(tab2, text='Second')
        lbl1 = Label(tab1, text= 'label1')
        lbl1.grid(column=0, row=0)
        lbl2 = Label(tab2, text= 'label2')
        lbl2.grid(column=0, row=0)
        tab_control.pack(expand=1, fill='both')

def main():
    root = Tk()
    root.title("Check out these sweet tabs!")
    app = Application(master=root)
    app.mainloop()

if __name__ == '__main__':
    main()