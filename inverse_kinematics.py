import tkinter, math, random, time
from tkinter import *
from time import *
from math import *
from random import *

#############################################################################################################################################################################################

# Canvas

main = Tk()
main.title('Inverse Kinematics')
main.bind("<F1>", exit)
main.attributes('-fullscreen', True)

w = main.winfo_screenwidth()
h = main.winfo_screenheight()

width  = w - 500
height = h

bgcolor = "#%02x%02x%02x" % (  0,  0,  0)
white   = "#%02x%02x%02x" % (255,255,255)

cnv = tkinter.Canvas(main, width=w, height=h)
cnv.configure(background=bgcolor)
cnv.pack()

#############################################################################################################################################################################################

basecolor = white

def draw():
    cnv.delete("base")
    cnv.create_line(width,0,width,height,fill=basecolor,tags="base")
    cnv.create_line(width,100,width+500,100,fill=basecolor,tags="base")
    cnv.create_text(width+250,50,fill=basecolor,font=("Times","20", "italic", "bold"), text = "FOLLOW", tags="base")

draw()

sliderlist = []
slidercolor = []
sliderx = []
slidertop = []
sliderbottom = []
slideroutput = []
value = []

def slider(name, scolor, startpos, endpos, output, pos):
    
    cnv.create_line(startpos[0], startpos[1],
                    endpos[0]  , endpos[1]  ,
                    fill=scolor, width=2, tags=(str(name),"menu"))

    cnv.create_line(startpos[0] - 20, startpos[1],
                    startpos[0] + 20, startpos[1],
                    fill=scolor, width=2, tags=(str(name),"menu"))

    cnv.create_line(endpos[0] - 20, endpos[1],
                    endpos[0] + 20, endpos[1],
                    fill=scolor, width=2, tags=(str(name),"menu"))

    cnv.create_oval(pos[0] - 10, pos[1] - 10,
                    pos[0] + 10, pos[1] + 10,
                    fill=scolor, width=0, tags=(str(name),"menu",str(name)+"a"))

    sliderlist.append(str(name))
    slidercolor.append(scolor)
    sliderx.append(startpos[0])
    slidertop.append(startpos[1])
    sliderbottom.append(endpos[1])
    slideroutput.append(output)

    value.append(int(recalc(pos[1], slidertop[name], sliderbottom[name], slideroutput[name][0], slideroutput[name][1])))

def recalc(x, a, b, c, d):

    val = (x-a)/((b-a)/(d-c))+c
    
    return val


def restart():
    global k, value, t, base
    k = int(value[0])    
    t = [0]*k

    for i in range(0,k):
        a = (i/k)*2*pi
        x = 600*cos(a)+cx
        y = 600*sin(a)+cy
        base = [x, y]
        t[i] = TT(base)

    cnv.delete("vals")

    cnv.create_text(width+100,height-100,fill=basecolor,font=("Times","20", "italic", "bold"), text = str(value[0]), tags="vals")
    cnv.create_text(width+250,height-100,fill=basecolor,font=("Times","20", "italic", "bold"), text = str(value[1]), tags="vals")
    cnv.create_text(width+400,height-100,fill=basecolor,font=("Times","20", "italic", "bold"), text = str(value[2]), tags="vals")

def slidertest():
    global sx, sy
    d = 0
    for i in sliderlist:

        if sliderx[d] - 50 < sx < sliderx[d] + 50:
            if sy < slidertop[d]:
                sy = slidertop[d]

            elif sy > sliderbottom[d]:
                sy = sliderbottom[d]
            
            
            cnv.delete(str(i)+"a")

            cnv.create_oval(sliderx[d] - 10, sy - 10,
                            sliderx[d] + 10, sy + 10,
                            fill=slidercolor[d], width=0, tags=(str(i),"menu",str(i)+"a"))

            value[d] = int(recalc(sy, slidertop[d], sliderbottom[d], slideroutput[d][0], slideroutput[d][1]))          

            restart()
                
        d += 1
        
slider(0, basecolor, [width+100, 150], [width+100, height-200], [1, 50], [width+100, 150])
slider(1, basecolor, [width+250, 150], [width+250, height-200], [1, 100], [width+250, 150])
slider(2, basecolor, [width+400, 150], [width+400, height-200], [1, 100], [width+400, 150])

#############################################################################################################################################################################################

# Colors

def to8bit(raw_value):
    return int(round(raw_value * 255))

def hsv2hex(H, S, V):
    if H == S == V == 0.0:
        return (0,0,0)
      
    H *= 6
    I = floor(H)
    F = H - I
    M = V * (1 - S)
    N = V * (1 - S * F)
    K = V * (1 - S * (1 - F))
      
    R = G = B = 0.0
    if I == 0:
        R = V
        G = K
        B = M
    elif I == 1:
        R = N
        G = V
        B = M
    elif I == 2:
        R = M
        G = V
        B = K
    elif I == 3:
        R = M
        G = N
        B = V
    elif I == 4:
        R = K
        G = M
        B = V
    else:
        R = V
        G = M
        B = N

    red = to8bit(R)
    green = to8bit(G)
    blue = to8bit(B)

    col = "#%02x%02x%02x" % (red, green, blue)
      
    return col

cx = width/2
cy = height/2

#############################################################################################################################################################################################

# Inverse Kinematics

class Segment():
    global value

    def __init__(seg, x, y, lenght, angle, index):
        seg.x = x
        seg.y = y
        seg.lenght = lenght
        seg.angle = angle
        seg.a = [x, y]
        seg.color = hsv2hex(index/value[1],0.9,0.9)
        seg.n = 5
        seg.width = 5 #(len(sg)-index)/len(sg)*seg.n

    def calculateB(seg):
        seg.dx = seg.lenght * cos(seg.angle)
        seg.dy = seg.lenght * sin(seg.angle)
        seg.b = [seg.a[0] + seg.dx, seg.a[1] + seg.dy]

    def setA(seg, pos):
        seg.a = pos
        seg.calculateB()

    def follow(seg, tx, ty):
        seg.target = [tx, ty]
        seg.direction = [seg.target[0] - seg.a[0], seg.target[1] - seg.a[1]]
        seg.angle = atan2(seg.direction[1],seg.direction[0])

        seg.k = seg.lenght/(sqrt(seg.direction[0]**2+seg.direction[1]**2))
        seg.direction = [-seg.direction[0]*seg.k, -seg.direction[1]*seg.k]
        seg.a = [seg.target[0]+seg.direction[0], seg.target[1]+seg.direction[1]]

    def head(seg):
        cnv.create_oval(seg.b[0]-seg.n,seg.b[1]-seg.n,seg.b[0]+seg.n,seg.b[1]+seg.n,fill=seg.color,width=seg.width,tags="segment")

    def update(seg):
        seg.calculateB()

    def show(seg):
        cnv.create_line(seg.a[0],seg.a[1],seg.b[0],seg.b[1],fill=seg.color,width=seg.width,tags="segment")


def move(event):
    global mx, my
    if event.x < width:
        mx, my = event.x, event.y
    elif event.x > width:
        global sx, sy
        sx, sy = event.x, event.y
        slidertest()

def button1(event):
    global follow1

    if event.y < 100 and event.x > width:
        if follow1 == True:
            follow1 = False
        else:
            follow1 = True

main.bind("<B1-Motion>", move)
main.bind("<Button-1>", button1)

#############################################################################################################################################################################################

xspeed = 5
yspeed = 5
r = 30
gravity = 0.1

mx, my = r, r

def ballmove():
    global xspeed, yspeed, mx, my, r
    
    mx += xspeed
    my += yspeed
    yspeed += gravity

    if mx + r > width or mx - r < 0:
        xspeed *= -1

    if my + r > height:
        my = height - r
        yspeed *= -1
        yspeed *= 0.95
        xspeed *= 0.95

    cnv.create_oval(mx-r,my-r,mx+r,my+r,fill=white,tags="ball")
    
#############################################################################################################################################################################################

follow1 = True

class TT():
    global value, follow1

    def __init__(tt,base):
        tt.sg = [0]*value[1]
        tt.sg[0] = Segment(cx, cy, value[2], 0, 0)
        tt.sg[0].calculateB()
        for i in range(1,len(tt.sg)):
            tt.sg[i] = Segment(tt.sg[i-1].a[0], tt.sg[i-1].a[1], value[2], 0, i)
            tt.sg[i].calculateB()
        tt.base = base
        
    def update(tt):
        tt.sg[0].follow(mx, my)
        tt.sg[0].update()
            
        for i in range(1,len(tt.sg)):
            tt.sg[i].follow(tt.sg[i-1].a[0], tt.sg[i-1].a[1])
            tt.sg[i].update()

        if follow1 == True:
            tt.sg[len(tt.sg)-1].setA(tt.base)

            for i in range(0,len(tt.sg)-1):
                i = len(tt.sg)-2-i
                tt.sg[i].setA(tt.sg[i+1].b)

    def show(tt):
        for i in range(0,len(tt.sg)):
            tt.sg[i].show()

#############################################################################################################################################################################################

restart()

while True:
    for i in range(0,len(t)):
        t[i].update()
        t[i].show()

    ballmove()
    cnv.update()
    cnv.delete("segment","ball")
    sleep(0.03)
