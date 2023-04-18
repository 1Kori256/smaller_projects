import math, tkinter, random, time
from tkinter import *
from math import *
from random import *
from time import *

# Canvas

main = Tk()
main.title('Turbulent Flow')
main.bind("<F1>", exit)

bgcolor = "#%02x%02x%02x" % (  0,  0,  0)
white   = "#%02x%02x%02x" % (255,255,255)

#Global vars

N      = 45
SCALE  = 640/N
iterat = 4

width  = N * SCALE
height = width

cnv = tkinter.Canvas(main, width=width, height=height+100)
cnv.configure(background=bgcolor)
cnv.pack()

cnv.create_line(0,height,width,height,fill=white)    

#HSV
def to8bit(raw_value):
    return int(round(raw_value * 256))

def hsv2rgb(H, S, V):
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
      
    return (red, green, blue)

#Slider

red = hsv2rgb(  0,0.9,0.9)
red = "#%02x%02x%02x" % (red[0], red[1], red[2])

for i in range(50,int(width-50)):
    col = ((i - 50)/(width-100))
    col = hsv2rgb(col,0.9,0.9)
    col1 = "#%02x%02x%02x" % (col[0], col[1], col[2])
    cnv.create_rectangle(i,height+50,i,height+50,fill=col1,width=0)

cnv.create_rectangle(50,height+30,50,height+70,fill=red,width=0)
cnv.create_rectangle(width-50,height+30,width-50,height+70,fill=red,width=0)

cnv.update()

maincol = 0.55

def slider(event):
    global maincol
    mx, my = event.x, event.y
    if (50 < mx < width-50) and (height < my):
        cnv.delete("slider")
        hue = (mx-50)/(width-100)
        maincol = hue
        color = hsv2rgb(hue,0.9,0.9)
        color = "#%02x%02x%02x" % (color[0], color[1], color[2])
        cnv.create_oval(mx-10,height+40,mx+10,height+60,fill=color,tags="slider")

default = hsv2rgb(maincol,0.9,0.9)
default = "#%02x%02x%02x" % (default[0], default[1], default[2])
cnv.create_oval((maincol)*(width-100)+50-10,height+40,(11/20)*(width-100)+50+10,height+60,fill=default,tags="slider")

main.bind("<B1-Motion>", slider)

#Data struct
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def IX(x,y):
    global N
    #constrain(x,0,N-1)
    #constrain(y,0,N-1)
    return (x+(y*N))

#Turbulet flow

class FluidCube():
    def __init__(cube,dt,diffusion,viscosity):
        global N
        cube.size = N
        cube.dt = dt
        cube.diff = diffusion
        cube.visc = viscosity

        cube.s = [0]*(N*N)
        cube.density = [0]*(N*N)

        cube.Vx = [0]*(N*N)
        cube.Vy = [0]*(N*N)

        cube.Vx0 = [0]*(N*N)
        cube.Vy0 = [0]*(N*N)

    def AddDensity(cube, x, y, amount):
        cube.density[IX(x,y)] += amount

    def AddVelocity(cube, x, y, amountX, amountY):
        index = IX(x,y)
        cube.Vx[index] += amountX
        cube.Vy[index] += amountY

    def step(cube):
        diffuse(1, cube.Vx0, cube.Vx, cube.visc, cube.dt)
        diffuse(2, cube.Vy0, cube.Vy, cube.visc, cube.dt)

        project(cube.Vx0, cube.Vy0, cube.Vx, cube.Vy)

        advect(1, cube.Vx, cube.Vx0, cube.Vx0, cube.Vy0, cube.dt)
        advect(2, cube.Vy, cube.Vy0, cube.Vx0, cube.Vy0, cube.dt)

        project(cube.Vx, cube.Vy, cube.Vx0, cube.Vy0)

        diffuse(0, cube.s, cube.density, cube.diff, cube.dt)
        advect(0, cube.density, cube.s, cube.Vx, cube.Vy, cube.dt)

def set_bnd(b, x):
    global N

    for i in range(1,N - 1):
        if b == 2:
            x[IX(i, 0  )] = -x[IX(i, 1  )]
            x[IX(i, N-1)] = -x[IX(i, N-2)]
        else:
            x[IX(i, 0  )] = x[IX(i, 1  )]
            x[IX(i, N-1)] = x[IX(i, N-2)]

    for j in range(1,N - 1):
        if b == 1:
            x[IX(0  , j)] = -x[IX(1  , j)]
            x[IX(N-1, j)] = -x[IX(N-2, j)]
        else:
            x[IX(0  , j)] = x[IX(1  , j)]
            x[IX(N-1, j)] = x[IX(N-2, j)]
    
    x[IX(0, 0)] = 0.5 * (x[IX(1, 0)] + x[IX(0, 1)])
                            
    x[IX(0, N-1)] = 0.5 * (x[IX(1, N-1)] + x[IX(0, N-2)])
                                  
    x[IX(N-1, 0)] = 0.5 * (x[IX(N-2, 0)] + x[IX(N-1, 1)])
                                  
    x[IX(N-1, N-1)] = 0.5 * (x[IX(N-2, N-1)] + x[IX(N-1, N-2)])

def lin_solve(b, x, x0, a, c):
    global N, iterat
    cR = 1/c
    for k in range(0,iterat):
        for j in range(1, N-1):
            for i in range(1, N-1):
                x[IX(i,j)] =       ( x0[IX(i,j)] +
                               a * (  x[IX(i+1,j)]
                                     +x[IX(i-1,j)]
                                     +x[IX(i,j+1)]
                                     +x[IX(i,j-1)]
                                   )) * cR
        set_bnd(b, x)

def diffuse(b, x, x0, diff, dt):
    global N
    a = dt * diff * (N - 2) * (N - 2)
    lin_solve(b, x, x0, a, 1 + 6*a)

def project(velocX, velocY, p, div):
    global N
    for j in range(1, N-1):
        for i in range(1, N-1): 
            div[IX(i, j)] = -0.5*(
                     velocX[IX(i+1, j  )]
                    -velocX[IX(i-1, j  )]
                    +velocY[IX(i  , j+1)]
                    -velocY[IX(i  , j-1)]
                )/N
            p[IX(i, j)] = 0
    
    set_bnd(0, div)
    set_bnd(0, p)
    lin_solve(0, p, div, 1, 6)

    for j in range(1, N-1): 
        for i in range(1, N-1): 
            velocX[IX(i, j)] -= 0.5 * (  p[IX(i+1, j)]
                                         -p[IX(i-1, j)]) * N
            velocY[IX(i, j)] -= 0.5 * (  p[IX(i, j+1)]
                                         -p[IX(i, j-1)]) * N
    set_bnd(1, velocX)
    set_bnd(2, velocY)

def advect(b, d, d0, velocX, velocY, dt):
    global N
    
    dtx = dt * (N - 2)
    dty = dt * (N - 2)
    
    Nfloat = N;
    
    for j in range(1, N-1):
        jfloat = j
        for i in range(1, N-1):
            ifloat = i
                
            tmp1 = dtx * velocX[IX(i, j)]
            tmp2 = dty * velocY[IX(i, j)]

            x    = ifloat - tmp1
            y    = jfloat - tmp2
                
            if(x < 0.5):
                x = 0.5
            if(x > Nfloat + 0.5):
                x = Nfloat + 0.5
            i0 = floor(x)
            i1 = i0 + 1.0
            if(y < 0.5):
                y = 0.5
            if(y > Nfloat + 0.5):
                y = Nfloat + 0.5 
            j0 = floor(y)
            j1 = j0 + 1.0
                
            s1 = x - i0
            s0 = 1.0 - s1
            t1 = y - j0
            t0 = 1.0 - t1
                
            i0i = int(i0)
            i1i = int(i1)
            j0i = int(j0)
            j1i = int(j1)
                
            d[IX(i, j)] = (           
                s0 * ( t0 * d0[IX(i0i, j0i)] + t1 * d0[IX(i0i, j1i)])             
               +s1 * ( t0 * d0[IX(i1i, j0i)] + t1 * d0[IX(i1i, j1i)]))
    set_bnd(b, d)

fluid = FluidCube(0.1,0,0.0000001)

def renderD():
    global maincol
    cnv.delete("fluid")
    for i in range(0, N):
        for j in range(0, N):
            x = i*SCALE
            y = j*SCALE
            d = fluid.density[(IX(i,j))]
            if d >= 900:
                d = 900
            m = hsv2rgb(maincol,0.9,((d)/1000) % 1)
            c = "#%02x%02x%02x" % (m[0], m[1], m[2])
            cnv.create_rectangle(x,y,x+SCALE,y+SCALE,fill=c,width=0,tags="fluid")
            if d > 1:
                fluid.density[(IX(i,j))] -= 1
    cnv.update()

col22 = hsv2rgb(maincol,0.9,0.9)
col2 = "#%02x%02x%02x" % (col22[0], col22[1], col22[2])

def renderV():
    cnv.delete("vector")
    for i in range(0, N):
        for j in range(0, N):
            u = IX(i, j)
            x = i*SCALE
            y = j*SCALE
            vx = fluid.Vx[u]
            vy = fluid.Vy[u]
            if (abs(vx) > 0.05 and abs(vy) > 0.05):
                cnv.create_line(x,y,x+vx*SCALE,y+vy*SCALE,fill=col2,tags="vector",width=2)
    cnv.update()

def renderB():
    global maincol
    cnv.delete("fluid","vector")
    for i in range(0, N):
        for j in range(0, N):
            u = IX(i, j)
            x = i*SCALE
            y = j*SCALE
            d = fluid.density[u]
            if d >= 900:
                d = 900
            m = hsv2rgb(maincol,0.9,((d)/1000) % 1)
            c = "#%02x%02x%02x" % (m[0], m[1], m[2])
            vx = fluid.Vx[u]
            vy = fluid.Vy[u]
            cnv.create_rectangle(x,y,x+SCALE,y+SCALE,fill=c,width=0,tags="fluid")
            if (abs(vx) > 0.05 and abs(vy) > 0.05):
                cnv.create_line(x,y,x+vx*SCALE,y+vy*SCALE,fill=white,tags="vector",width=2)
            if d > 1:
                fluid.density[(IX(i,j))] -= 1
    cnv.update()

px = 0
py = 0

def motion(event):
    global px, py
    xx, yy = event.x, event.y
    fluid.AddDensity(int(xx/SCALE), int(yy/SCALE), 500)
    amtX = (xx - px)/20
    amtY = (yy - py)/20
    if amtX > 10:
        amtX = 10
    if amtY > 2:
        amtY = 2
    if amtY < -10:
        amtX = -10
    if amtY < -2:
        amtY = -2
    px, py = event.x, event.y
    fluid.AddVelocity(int(xx/SCALE), int(yy/SCALE), amtX*2, amtY*2)

#main.bind('<Motion>', motion)

cx = int((  width / SCALE ) /2 )
cy = int(( height / SCALE ) /2 )

posx = 3
posy = cy

velx1 = N/5
vely1 = N/8

globalden = 2500

def click(event):
    global velx1, vely1
    mx, my = event.x, event.y
    if my < height:
        velx1 = (((mx/SCALE)-posx)/4)
        vely1 = (((my/SCALE)-posy)/4)

def left(event):
    global posx
    posx -= 1
    if posx < 2:
        posx = 2

def right(event):
    global posx
    posx += 1
    if posx > N-2:
        posx = N-2

def up(event):
    global posy
    posy -= 1
    if posy < 2:
        posy = 2

def down(event):
    global posy
    posy += 1
    if posy > N-2:
        posy = N-2

def sleft(event):
    global posx
    posx -= 10
    if posx < 2:
        posx = 2

def sright(event):
    global posx
    posx += 10
    if posx > N-2:
        posx = N-2

def sup(event):
    global posy
    posy -= 10
    if posy < 2:
        posy = 2

def sdown(event):
    global posy
    posy += 10
    if posy > N-2:
        posy = N-2

stopvar = 0
def stop(event):
    global vely1, velx1, globalden, stopvar
    if stopvar == 0:
        velx1 = 0
        vely1 = 0
        globalden = 0
        stopvar = 1
    else:
        globalden = 2500
        velx1 = 8
        vely1 = 5
        stopvar = 0
        
main.bind("<1>"          , click )
main.bind('<Left>'       , left  )
main.bind('<Right>'      , right )
main.bind('<Up>'         , up    )
main.bind('<Down>'       , down  )
main.bind('<Shift-Left>' , sleft )
main.bind('<Shift-Right>', sright)
main.bind('<Shift-Up>'   , sup   )
main.bind('<Shift-Down>' , sdown )
main.bind("<s>"          , stop  )

a = 0
n = 1
o = 0
u = 0

def move():
    global a, n, velx1, vely1
    a += n
    velx1 = cos(radians(a))*(N/8)
    vely1 = sin(radians(a))*(N/8)
    if a == 90:
        n = -1
    elif a == -90:
        n = 1

def randommove():
    global a, n, velx1, vely1, o ,u
    if o >= u:
        n = uniform(-5,5)
        u = uniform(0,90)
        o = abs(n)
    a += n
    o += o
    if a >= 90:
        n *= -1
    elif a <= -90:
        n *= -1
    velx1 = cos(radians(a))*(N/8)
    vely1 = sin(radians(a))*(N/8)

def changecolor():
    global maincol
    maincol = (maincol + 0.001) % 1

while True:
    fluid.AddDensity(posx,posy,globalden)
    fluid.AddVelocity(posx,posy,velx1,vely1)

    randommove()
    #changecolor()
    renderD()
    fluid.step()

    

