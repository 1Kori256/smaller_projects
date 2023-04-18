import tkinter, math, random, time
from tkinter import *
from time import *
from math import *
from random import *

# Canvas

main = Tk()
main.title('3D Sphere')
main.bind("<F1>", exit)
main.attributes('-fullscreen', True)

w = main.winfo_screenwidth()
h = main.winfo_screenheight()


width  = w
height = h

bgcolor = "#%02x%02x%02x" % (  0,  0,  0)
white   = "#%02x%02x%02x" % (255,255,255)

cnv = tkinter.Canvas(main, width=w, height=h)
cnv.configure(background=bgcolor)
cnv.pack()

# Cols
def to8bit(raw_value):
    return int(round(raw_value * 256))

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

# Matrix Multiplication

def MatMultVec(a,b):
    colsA = len(a[0])
    rowsA = len(a)
    colsB = 1
    rowsB = len(b)

    if (colsA != rowsB):
        print("colsA =/= rowsB")
        return None

    m = rowsA
    result = [0]*m
    for i in range(0,rowsA):
        s = 0
        for k in range(0,colsA):
            s += (a[i][k] * b[k])
        result[i] = s
    return result

def VecMultMat(a,b):
    colsA = 1
    rowsA = len(a)
    colsB = len(b)
    rowsB = 1


    n = colsB
    m = rowsA
    result = []
    for i in range(0,n):
        result.append([0]*m)
    for i in range(0,rowsA):
        for j in range(0,colsB):
            s = 0
            s += (a[i] * b[j])
            result[i][j] = s
    return result

def matrixMult(a,b):

    try:
        colsA = len(a[0])
    except TypeError:
        return VecMultMat(a,b)
        
    rowsA = len(a)

    try:
        colsB = len(b[0])
    except TypeError:
        return MatMultVec(a,b)
        

    rowsB = len(b)

    if (colsA != rowsB):
        print("colsA =/= rowsB")
        return None

    n = colsB
    m = rowsA
    result = []
    for i in range(0,n):
        result.append([0]*m)
    for i in range(0,rowsA):
        for j in range(0,colsB):
            s = 0
            for k in range(0,colsA):
                s += (a[i][k] * b[k][j])
            result[i][j] = s
    return result

cx = width/2
cy = height/2
r = 2

anglez = 0
angley = 0
anglex = 0

projection    = [0]*2
projection[0] = (1,0,0)
projection[1] = (0,1,0)

size = 300

def fibonacci_sphere(samples):
    global points

    points = []
    offset = 2./samples
    increment = math.pi * (3. - math.sqrt(5.));

    for i in range(samples):
        y = ((i * offset) - 1) + (offset / 2);
        r = math.sqrt(1 - pow(y,2))

        phi = ((i) % samples) * increment

        x = math.cos(phi) * r
        z = math.sin(phi) * r

        points.append([x,y,z])

    return points

n = 100
fibonacci_sphere(n)

pmx, pmy = 0, 0
def move(event):
    global pmx, pmy, anglex, angley, anglez
    mx, my = event.x, event.y
    dx = mx - pmx
    dy = my - pmy

    if dx < 100 and dy < 100:
        angley += dx/100
        anglex += dy/100
    pmx, pmy = mx, my

def mouse_wheel(event):
    global size
    if event.delta == -120:
        size -= 5
        r = size/150
    elif event.delta == 120:
        size += 5
        r = size/150

auto = 0        
def auto(event):
    global auto
    if auto == 0:
        auto = 1
    else:
        auto = 0

main.bind("<B1-Motion>", move)
main.bind("<MouseWheel>", mouse_wheel)
main.bind("<Control_L>", auto)

while True:
    rotationZ = [( math.cos(anglez), -math.sin(anglez), 0),
                 ( math.sin(anglez),  math.cos(anglez), 0),
                 (                0,                 0, 1)]

    rotationX = [( 1,                0,                 0),
                 ( 0, math.cos(anglex), -math.sin(anglex)),
                 ( 0, math.sin(anglex),  math.cos(anglex))]

    rotationY = [(  math.cos(angley), 0, math.sin(angley)),
                 (                 0, 1,                0),
                 ( -math.sin(angley), 0, math.cos(angley))]

    ax = []
    ay = []
        
    for x in range(0,len(points)):
        projected2d = matrixMult(rotationX  ,points[x])        
        projected2d = matrixMult(rotationY  ,projected2d)
        projected2d = matrixMult(rotationZ  ,projected2d)
        projected2d = matrixMult(projection ,projected2d)

        col2 = hsv2hex(x/n,0.9,0.9)    
        cnv.create_oval(projected2d[0]*size-r+cx,projected2d[1]*size-r+cy,
                        projected2d[0]*size+r+cx,projected2d[1]*size+r+cy,
                        fill=col2,width=0,tags="p")

        ax.append(projected2d[0]*size+cx)
        ay.append(projected2d[1]*size+cy)

    for i in range(0,int(n)):
        for j in range(0,int(n)):
            xdiff = points[i][0]-points[j][0]
            ydiff = points[i][1]-points[j][1]
            zdiff = points[i][2]-points[j][2]
            if (sqrt(xdiff**2+ydiff**2+zdiff**2) < 0.5):
                col = hsv2hex((i*j)/(n*n),0.9,0.9)
                cnv.create_line(ax[i],ay[i],ax[j],ay[j],fill=col,tags="l")

    if auto == 1:
        angley += 0.01
            
    cnv.update()
    cnv.delete("p","l")
