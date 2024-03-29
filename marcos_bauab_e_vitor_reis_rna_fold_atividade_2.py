# -*- coding: utf-8 -*-
"""Marcos_Bauab_e_Vitor_Reis_RNA_FOLD_ATividade 2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1obupJVx6PgMkUjCp4g74Nr_121bEYO59
"""

import torch
import numpy as np
from torch import nn
import pandas as pd
import zipfile
import folium

from google.colab import drive
drive.mount('/content/drive')

zf = zipfile.ZipFile('/content/drive/MyDrive/IA/House_Sale.zip')  #aloca o arquivo zip

data = pd.read_csv(zf.open('kc_house_data.csv')) # abre o arquivo CSV 'train.csv' presente dentro do ZIP
data.dropna(inplace=True)
data_mapa=data.sample(frac=1).reset_index(drop=True)
data_shuffle=data_mapa.drop(['id', 'date', 'lat', 'long','zipcode' ], axis=1)


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Converte o DataFrame Pandas em um tensor do PyTorch
data_tensor = torch.tensor(data_shuffle.values).float().to(device)

#data = data.drop([10, 17])

# np.where(data['sqft_above'].isnull().values==True)

# data.isnull().sum()

# print(data.values[10])
# print(data.values[17])

data_shuffle.head()

coluna_lat = data_mapa['lat'].values
print(coluna_lat.shape)

coluna_long = data_mapa['long'].values
print(coluna_lat.shape)

# data_shuffle = data_shuffle.drop(['id', 'date', 'lat', 'long','zipcode' ], axis=1) # remove a coluna de IDs
data_shuffle.head()

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import mean_absolute_percentage_error

# Define the neural network architecture
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(15, 30)
        self.fc2 = nn.Linear(30, 60)
        self.fc3 = nn.Linear(60, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x)) # relu(Wi * X + b)
        x = torch.relu(self.fc2(x)) # relu(Wi+1 * relu(W * X + b))
        x = self.fc3(x)             # relu( Wi+2 * relu( Wi+1 * relu(W * X + b) ) )
        return x

from sklearn.model_selection import KFold

X = data_shuffle.values[:, 1:]
y = data_shuffle.values[:, 0]

kf = KFold()
kf.get_n_splits(X)
best_loss = float('inf')

best_model = {'name':'johndoe', 'mape':0}
for i, (train_index, test_index) in enumerate(kf.split(X)):
  print(f"\033[32mFold {i}:\033[0m")
  print(f"  Train: index={len(train_index)}")
  print(f"  Test:  index={len(test_index)}")

  train_inputs = torch.from_numpy(X[train_index]).to(device)
  train_inputs = train_inputs.float()

  train_labels = torch.from_numpy(y[train_index]).unsqueeze(1).to(device)
  train_labels = train_labels.to(device).float()  # mover para o mesmo dispositivo e converter para float

  test_inputs = torch.from_numpy(X[test_index]).to(device)
  test_inputs = test_inputs.float()

  test_labels = torch.from_numpy(y[test_index]).to(device)
  test_labels = test_labels.to(device).float()  # mover para o mesmo dispositivo e converter para float

  model = Net()
  model.to(device)
  criterion = nn.L1Loss().to(device)
  optimizer = optim.Adam(model.parameters(), lr=0.0567)
  list_loss_scores = []

  model.train()
  for epoch in range(1000):
    optimizer.zero_grad()
    outputs = model(train_inputs)
    outputs = outputs.to(device)
    loss = criterion(outputs, train_labels)
    list_loss_scores.append(loss.cpu().detach().numpy())
    loss.backward()
    optimizer.step()
    print('Epoch %d, Loss: %.4f' % (epoch+1, loss.item()))

    model.eval()
    with torch.no_grad():
      outputs = model(test_inputs)
      outputs = outputs.to(device)
      mape = mean_absolute_percentage_error(test_labels.cpu(), outputs.cpu())
      if (mape < best_loss):
        best_loss = mape
        model_name = f"Marcos_Bauab_e_Vitor_Reis_RNA_FOLD_{i+1}.pth"
        torch.save(model.state_dict(), model_name)
        best_model['name'] = model_name
        best_model['mape'] = mape

print(best_model)

model = Net()
model.load_state_dict(torch.load(best_model['name']))
model.to(device)

X = data_shuffle.values[:, 1:]
y = data_shuffle.values[:, 0]

test_inputs = torch.from_numpy(X).to(device)
test_inputs = test_inputs.float()

test_labels = torch.from_numpy(y).to(device)
test_labels = test_labels.to(device).float()  # mover para o mesmo dispositivo e converter para float

outputs = model(test_inputs)
outputs = outputs.cpu().detach().numpy()
mape = mean_absolute_percentage_error(test_labels.cpu(), outputs)

data_mapa['NEW_PRICE'] = outputs # adicionando a coluna New_price
print(mape)

data_mapa.head()

from matplotlib import pyplot as plt

#print(list_loss_scores)
list_loss_scores = np.array(list_loss_scores)
#print(list_loss_scores)

x_axis = np.arange(1,list_loss_scores.shape[0]+1)
plt.title("Curva de Aprendizagem da MLP")
plt.xlabel("Epochs")
plt.ylabel("Loss scores")
plt.plot(x_axis,list_loss_scores)
plt.xlim([1, list_loss_scores.shape[0]+1])
plt.show()

map = folium.Map(location=[47.5112	,-122.257], zoom_start=10)

import webbrowser

for x in range(2000):
    folium.CircleMarker(location=[coluna_lat[x],coluna_long[x]],
                  parse_html=True,fill_opacity=1,weight=1,color='blue',radius=4,fill=True,
                  popup="<div style='width: 200px'>"
                        f"<b>Price:</b> {data_mapa.loc[x]['price']}<br>"
                        f"<p style='color: red'><b>Predicted Price:</b> {round(data_mapa.loc[x]['NEW_PRICE'], 1):.1f}<br></p>"
                        f"<b>ID:</b> {data_mapa.loc[x]['id']}<br>"
                        f"<b>Date:</b>{data_mapa.loc[x]['date']}<br>"
                        f"<b>Bedrooms:</b> {data_mapa.loc[x]['bedrooms']}<br>"
                        f"<b>Bathrooms:</b> {data_mapa.loc[x]['bathrooms']}<br>"
                        f"<b>sqft_living:</b> {data_mapa.loc[x]['sqft_living']}<br>"
                        f"<b>sqft_lot:</b> {data_mapa.loc[x]['sqft_lot']}<br>"
                        f"<b>Floors:</b> {data_mapa.loc[x]['floors']}<br>"
                        f"<b>Waterfront:</b> {data_mapa.loc[x]['waterfront']}<br>"
                        f"<b>view:</b> {data_mapa.loc[x]['view']}<br>"
                        f"<b>condition:</b> {data_mapa.loc[x]['condition']}<br>"
                        f"<b>grade:</b> {data_mapa.loc[x]['grade']}<br>"
                        f"<b>sqft_above:</b> {data_mapa.loc[x]['sqft_above']}<br>"
                        f"<b>sqft_basement:</b> {data_mapa.loc[x]['sqft_basement']}<br>"
                        f"<b>yr_built:</b> {data_mapa.loc[x]['yr_built']}<br>"
                        f"<b>yr_renovated:</b> {data_mapa.loc[x]['yr_renovated']}<br>"
                        f"<b>zipcode:</b> {data_mapa.loc[x]['zipcode']}<br>"
                        f"<b>sqft_living15:</b> {data_mapa.loc[x]['sqft_living15']}<br>"
                        f"<b>sqft_lot15:</b> {data_mapa.loc[x]['sqft_lot15']}<br>"
                        "</div>",
                        tooltip='Clique aqui!',).add_to(map)


map.save("output.html")
webbrowser.open("output.html")
map

data_mapa.loc[0]['price']