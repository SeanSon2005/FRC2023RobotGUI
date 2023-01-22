import numpy as np
import dearpygui.dearpygui as dpg
import time 
from PIL import Image
import pyautogui
import ctypes
import trajectoryHandler

#intialize user32 to read monitor size
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

#for framerate calculations
prev_frame_time = 0
new_frame_time = 0

#Constants
ENABLEVSYNC = True
SCREENWIDTH = user32.GetSystemMetrics(0)
SCREENHEIGHT = user32.GetSystemMetrics(1)
FIELDWIDTH = 660
FIELDHEIGHT = 1305

#Global Tags
mouseCoordTag = 0

#dynamically updating global variables
trajectoryCoords = np.zeros((500, 500))
latestX = 0
latestY = 0
gameScale = 1

waypoints = []

#draw coordinate global variables
tDraw = [] #trajectories
bDraw = [0] * 2 #background
rDraw = [0] * 2 #robot
intersectCoord = (0, 0)

#update FPS
def updateFps():
    global new_frame_time
    global prev_frame_time
    new_frame_time = time.time()
    fps = 1 / (new_frame_time-prev_frame_time + 0.000001)
    prev_frame_time = new_frame_time
    return "FPS " + str(int(fps))

#flatten image to be used as Texture
def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image

#redraw all elements
def update_graphics():
    global trajectoryCoords

    dpg.set_item_height("drawlist", FIELDHEIGHT)
    dpg.set_item_width("drawlist", FIELDWIDTH)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)
    dpg.draw_image("game field", (0,0), (FIELDWIDTH, FIELDHEIGHT), uv_min=(0, 0), uv_max=(1,1), parent="drawlist")

    for i in range(len(waypoints)):
        if i == 0:
            dpg.draw_circle((waypoints[i][0], waypoints[i][1]), 5, fill=(0, 0, 255, 255), parent="drawlist") # Initial point
        else:
            dpg.draw_circle((waypoints[i][0], waypoints[i][1]), 5, fill=(255, 0, 0, 255), parent="drawlist") # All other waypoints
    
    tDraw = np.zeros(np.shape(trajectoryCoords))
    for i in range(np.shape(trajectoryCoords)[1]):
        tDraw[0][i], tDraw[1][i] = trajectoryCoords[0][i], trajectoryCoords[1][i]
    for i in range(np.shape(trajectoryCoords)[1] - 1):
        dpg.draw_line((tDraw[0][i], tDraw[1][i]), (tDraw[0][i + 1], tDraw[1][i + 1]), color=(255, 0, 0, 255), thickness=3, parent="drawlist")

#create trajectory
def addTargetPoint():
    global latestX
    global latestY
    global waypoints

    latestX = max(pyautogui.position()[0] - 10, 0)
    latestY = max(pyautogui.position()[1] - 25, 0)

    if latestX > FIELDWIDTH or latestY > FIELDHEIGHT:
        return

    dpg.set_value(mouseCoordTag, "CLICK: X " + str(latestX) + " Y " + str(latestY))

    waypoints.append((latestX, latestY))
    update_graphics()

#main APP CONTROL
def main():
    global waypoints

    #always create context first
    dpg.create_context()
    
    #get image and convert to 1D array to turn into a static texture
    img = Image.open('gamefield.png')
    img_rotated = img.rotate(-90, expand=True)
    dpg_image = flat_img(img_rotated)

    #load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=FIELDWIDTH, height=FIELDHEIGHT, default_value=dpg_image, tag="game field")

    #create viewport
    dpg.create_viewport(title='Team 3952', width=SCREENWIDTH, height=SCREENHEIGHT)
    dpg.set_viewport_vsync(ENABLEVSYNC)
    dpg.setup_dearpygui()
    dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    #basically an event handler
    with dpg.handler_registry():
        dpg.add_mouse_click_handler(callback=addTargetPoint)
    
    #create window for drawings and images
    with dpg.window(tag="Window1"):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=SCREENWIDTH / 3, height=FIELDHEIGHT, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (FIELDWIDTH, FIELDHEIGHT), uv_min=(0, 0), uv_max=(1, 1))

    #create window for text 
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450, 250), pos=(SCREENWIDTH / 3 + 20, 10)):
        global mouseCoordTag
        fpsTag = dpg.add_text("FPS 0")
        mouseCoordTag = dpg.add_text("CLICKED: X 0 Y 0")

    def popWaypoint():
        waypoints.pop()
        update_graphics()

    def generateTrajectory():
        global trajectoryCoords
        trajectoryCoords = trajectoryHandler.listOfPointsToTrajectory(waypoints, 0)
        update_graphics()
    
    def saveTrajectory():
        trajectoryHandler.uploadStates(trajectoryCoords, False)
    
    def loadTrajectory():
        print("Loading Trajectory")
    
    def clearTrajectory():
        global trajectoryCoords
        waypoints.clear()
        trajectoryCoords = np.zeros((0, 0))
        update_graphics()

    with dpg.window(tag="trajGenWindow", label="Trajectory Generation", no_close=True, min_size=(450, 350), pos=(SCREENWIDTH / 3 + 20, 300)):
        dpg.add_button(label="Remove last point", callback=popWaypoint)
        dpg.add_button(label="Generate Trajectory", callback=generateTrajectory)
        dpg.add_button(label="Save Trajectory", callback=saveTrajectory)
        dpg.add_button(label="Load Trajectory", callback=loadTrajectory)
        dpg.add_button(label="Clear Trajectory", callback=clearTrajectory)

    #show viewport
    dpg.show_viewport()

    #run program
    while dpg.is_dearpygui_running():
        dpg.set_value(fpsTag, updateFps())    
        dpg.render_dearpygui_frame()                      

    dpg.destroy_context()

if __name__ == "__main__":
    main()