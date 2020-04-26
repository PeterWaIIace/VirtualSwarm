# example 
import random
from virtual_swarm import SwarmMother, Swarm
import numpy as np 
import imageio
from matplotlib import pyplot as plt
from  matplotlib import animation

amplitude = 15000
cols = 50
rows = 35
data_set = np.ones((rows,cols))*amplitude # only one dimensional

def decrement(index):
    col = index%rows
    row = int(index/rows)
    while data_set[col,row] != 0:
        data_set[col,row] -= 1
    return None 

if __name__ == "__main__":

    indexes = np.arange(0,cols*rows,1)
    random.shuffle(indexes) # just shuffle to see better result
    number_of_threads = 4
    swarm = Swarm(number_of_threads)
    Queen = SwarmMother(swarm=swarm,list_of_callbacks=[decrement],initial_problem=indexes)

    ims = []
    summed = np.sum(data_set)
    fig = plt.figure()

    Queen.start(in_background=True)

    while summed != 0:
        im = plt.imshow(data_set,vmin=0, vmax=amplitude)
        ims.append([im]) # every image in ArtistAnimation must be artist series (just images in list - even one)
        
        summed = np.sum(data_set)

    Queen.kill()
    print("saving!")
    ani = animation.ArtistAnimation(fig, ims, interval=50, blit=True,repeat_delay=500)

    print("writer")
    writer = animation.PillowWriter(fps=20)
    print("writer saving")
    ani.save("./demo.gif", writer=writer)
    print("here")
    plt.show()

    