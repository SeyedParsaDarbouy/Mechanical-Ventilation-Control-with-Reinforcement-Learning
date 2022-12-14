# -*- coding: utf-8 -*-
"""Copy of ML Course Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1cVAq_ylcXyJq1SsmDUsTkliROPvm0LrK
"""

# Commented out IPython magic to ensure Python compatibility.
#mount drive and go to working directory so that you can import custom libraries
from google.colab import drive
drive.mount('/content/drive')

# %cd /content/drive/My Drive/

#import dependencies
import numpy as np
import matplotlib.pyplot as plt
import tiles3

# read the data
data =np.genfromtxt('out.txt', dtype=np.float128)

#select subset of data
dataset_size = 16000
test_size = 4000
dataset = data[0:dataset_size, 2:7]
true_value =data[0:dataset_size, 7]

test_dataset = data[dataset_size :dataset_size + test_size, 2:7]
test_true_value =data[dataset_size :dataset_size + test_size, 7]

print(f"train dataset size: {dataset.shape}")
print(f"test dataset size:  {test_dataset.shape}")

class TileCoder:
    def __init__(self, s_max,s_min,iht_size=1028, num_tilings=8, num_tiles=8):
        self.iht = tiles3.IHT(iht_size)
        self.num_tilings = num_tilings
        self.num_tiles = num_tiles
        self.iht_size = iht_size
        self.s_max = s_max
        self.s_min = s_min
    def get_tiles(self, s):
        s_scaled = self.num_tiles * abs((s - self.s_min) / (self.s_max - self.s_min))
        tiles = tiles3.tiles(self.iht, self.num_tilings, [s_scaled])
        return tiles

# apply the tile coder
R_max = 50
R_min = 5
C_max = 50
C_min = 10
time_step_max = 2.94
time_step_min = 0
u_in_max = 100
u_in_min = 0
u_out_max = 1
u_out_min = 0
tc1 = TileCoder(s_max = R_max, s_min = R_min, iht_size=1028, num_tilings=8, num_tiles=8)
tc2 = TileCoder(s_max = C_max, s_min = R_min)
tc3 = TileCoder(s_max = time_step_max, s_min = time_step_min)
tc4 = TileCoder(s_max = u_in_max, s_min = u_in_min)
tc5 = TileCoder(s_max = u_out_max, s_min = u_out_min)

formatted_dataset = np.zeros((dataset.shape[0], 5*tc1.num_tilings)).astype(int)
formatted_test_dataset = np.zeros((test_dataset.shape[0], 5*tc1.num_tilings)).astype(int)

for i, s in enumerate(dataset):
    #print(tc1.get_tiles(s[0]))
    s_tiled = []
    s_tiled+=tc1.get_tiles(s[0])
    s_tiled +=[x + 1028 for x in tc2.get_tiles(s[0])]
    s_tiled+=[x + 2*1028 for x in tc3.get_tiles(s[0])]
    s_tiled +=[x + 3*1028 for x in tc4.get_tiles(s[0])]
    s_tiled+=[x + 4*1028 for x in tc5.get_tiles(s[0])]
    print(s_tiled)
    s_tiled = np.array(s_tiled).astype(int)
    #print(s_tiled)
    #print(s_tiled.shape)
    formatted_dataset[i] = s_tiled


print(formatted_dataset[0:100, ])

def calculated_value(active_tiles, w):
    value = 0
    for i in active_tiles:
        value += w[i]
    return value

def calc_MAE(x, w, true_value):
    pred_value = np.zeros(true_value.reshape(-1, 1).shape)
    for i in range(true_value.shape[0]):
        pred_value[i] = calculated_value(x[i], w)
    return np.sum(np.abs(pred_value - true_value.reshape(-1, 1))) / true_value.shape[0]


def plot_curve(lst,ylabel="mean absolute error"):
    x_axis = [i + 1 for i in range(len(lst))]
    plt.plot(x_axis, lst)
    plt.xlabel("time step")
    plt.ylabel(ylabel)
    plt.show()

def output_of_algorithm(learned_w,x):
  estimated_value = []
  for i in range(x.shape[0]):
    estimated_value.append(calculated_value(x[i],learned_w))
  return estimated_value

def compare_curves(true_value, estimated_value):
  x_axis = [i + 1 for i in range(len(true_value))]
  plt.plot(x_axis, estimated_value, label = "estimated value", color="orange")
  plt.plot(x_axis, true_value, label="true value",color= "blue")
  plt.xlabel("time step")
  plt.ylabel("pressure(cmH2O)")
  plt.legend(loc='upper left')
  plt.show()

def normalize(data):
  return (data +1.9)/(64.8 + 1.9)

def scale_inverse(data):
  return np.multiply(data,(64.8 + 1.9)) -1.9

# define important variables
gamma = 1
step_size = 1 / tc1.num_tilings #should be divided

# tile coding
x = np.copy(formatted_dataset)
num_features = len(dataset[0])

from re import S
# TD(0)

w = np.zeros((tc1.iht_size*5, 1))
error_list = []
min_error = np.inf
min_error_weight_index = 0


for s in range(dataset_size -1):

    #update weights
    predicted_value = calculated_value(x[s], w)
    next_state_predicted_value = calculated_value(x[s + 1], w)
    r = normalize(true_value[s]) #normalized#TODO: is multiply by 3 better???
    delta = r + gamma * next_state_predicted_value - predicted_value
    w[x[s]] = w[x[s]] + step_size * delta

    #decaying step size, and save progress
    if s +1 % 80 ==0:
      step_size = step_size * 0.9

    #save error
    error_list.append(calc_MAE(x, w, true_value))
    print(f"state {s}: error {error_list[-1]}")

    #save min weight
    if error_list[-1] < min_error:
      min_error = error_list[-1] 
      min_error_weight_index = s



final_weight_index = s
np.savetxt(f'min_weight_{min_error_weight_index}.csv', w, delimiter=',')
np.savetxt(f'final_weight_{s}.csv', w, delimiter=',')
print("predicted:", calculated_value(x[80], w), " the true value:", true_value[80])

#visualize the results
print(min_error_weight_index)
plot_curve(error_list)
w = np.genfromtxt(f'min_weight_{min_error_weight_index}.csv')

print(f"least error: {calc_MAE(x,w, true_value)}")

estimated_value = output_of_algorithm(learned_w =w,x=formatted_dataset)
scaled_true_value = normalize(true_value)
rescaled_estimated_value = scale_inverse(estimated_value) #why should i do this?
n_estimated_value =[i*2 for i in estimated_value]

#plot_curve(error_list)
plot_curve(estimated_value[0:800] ,ylabel ="estimated value")
plot_curve(scaled_true_value[0:800],ylabel = "true value")
compare_curves(true_value[0:800], n_estimated_value[0:800])

#test phase

w = np.genfromtxt(f'min_weight_{min_error_weight_index}.csv')

print(f"TEST error: {calc_MAE(formatted_test_dataset, w, test_true_value) }  ")

test_estimated_value = output_of_algorithm(learned_w =w,x=formatted_test_dataset)
scaled_test_true_value = normalize(test_true_value)
rescaled_test_estimated_value = scale_inverse(test_estimated_value)
n_test_estimated_value = [i*2 for i in test_estimated_value]

plot_curve(test_estimated_value[0:800] ,ylabel ="estimated value")
plot_curve(test_true_value[0:800] ,ylabel = "true value")
compare_curves(test_true_value[0:800] , n_test_estimated_value[0:800])

#permutaion test, t-test??
#TD lambda
#more hyperparameter tuning