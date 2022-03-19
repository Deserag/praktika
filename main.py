from tkinter import *
from random import *
left = 20
ai_map = [False for _ in range(left)]
def s1():
  global left
  u = 1
  left = left - int(u)
  if left <= 0:
    sticks.config(text = "Компьютер победил")
    sticks.place(x=475, y=70)
  else:
    sticks.config(text = left*"| ")


def s2():
  global left
  u = 2
  left = left - int(u)
  if left <= 0:
    sticks.config(text = "Компьютер победил")
    sticks.place(x=475, y=70)
  else:
    sticks.config(text = left*"| ")
def s3():
  global left
  u = 3
  left = left - int(u)
  if left <= 0:
    sticks.config(text="Компьютер победил")
    sticks.place(x=475, y=70)
  else:
    sticks.config(text=left * "| ")

def pc():
  global left
  start_cell = 20 - left - 1
  for cell_index in range(20):
    cell = 20 - cell_index - 1
    if 0 < cell_index % (1 + 3) <= 1:
      ai_map[cell] = True
  for x in range(start_cell, 20):
    if ai_map[x] and 1 <= x - start_cell <= 3:
      a =  x - start_cell
    elif x - start_cell > 3:
      a = randint(1, 3)
    else:
      a =randint(1, 3)
  left = left - int(a)
  if left <= 0:
    sticks.config(text="Игрок победил")
    sticks.place(x=140, y=70)
  else:
    sticks.config(text=left * "| ")
root = Tk()
root.geometry("1350x700")
text1 = Label(root, text="Сколько палочек будем брать?")
text1.pack()
wbutt1 = Button(root, text="1", command = s1)
wbutt1.place(x=510, y=230)
wbutt2 = Button(root, text="2", command = s2)
wbutt2.place(x=665, y=230)
wbutt3 = Button(root, text="3", command = s3)
wbutt3.place(x=820, y=230)
sticks = Label(root, text = left*"| ")
sticks.config(font = ("Arial", 35, 'bold'),fg='red')
sticks.place(x=425, y=370)
pc_butt = Button(root, text = "Ход компьютера", command = pc)
pc_butt.place(x=615, y=550)
root.resizable(0,0)
root.title("Палочки")
root.mainloop()