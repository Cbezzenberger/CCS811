from tkinter import *

window = Tk()
#Error is caused by this: https://unix.stackexchange.com/questions/17255/is-there-a-command-to-list-all-open-displays-on-a-machine

window.title('Plotting in Tkinter')

window.geometry("500x500")

plot_button = Button(
    master = window,
    height = 2,
    width = 10,
    text = "Plot"
)

plot_button.pack()

window.mainloop()