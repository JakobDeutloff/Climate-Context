import xarray as xr
import cartopy as crs
import matplotlib.pyplot as plt

# %% Load Data
path = r'C:\Users\jakob\3D Objects\E_obs'
file1 = r'\tn_ens_mean_0.1deg_reg_v27.0e.nc'
file2 = r'\tx_ens_mean_0.1deg_reg_v27.0e.nc'
file3 = r'\tg_ens_mean_0.1deg_reg_v27.0e.nc'

T_min = xr.open_dataarray(path + file1)
T_max = xr.open_dataarray(path + file2)
T_mean = xr.open_dataarray(path + file3)

T = {'max': T_max, 'mean': T_mean, 'min': T_min}

# %% Specify request

# Augsburg koordinates
lat = 48.3705
lon = 10.8978
day = '2023-05-10'
temp = 14

# Variable
variable = 'max'

# Select Data
T_sel = T[variable].sel(latitude=lat, longitude=lon,
                        time=(T_mean.time.dt.month == int(day[5:7])) & (T_mean.time.dt.day == int(day[8:10])),
                        method='nearest')


#  Plot timeseries
fig, ax = plt.subplots()
ax.plot(T_sel.time.dt.year, T_sel.values)
ax.axhline(T_sel.mean('time'), color='k', linestyle='--')
ax.plot(int(day[0:4]), temp, marker='o', linestyle='', color='r')
ax.set_title(variable + ' LocationData')
ax.set_ylabel('LocationData [°C]')
plt.show()

# %% Plot of the Field
T_mean.isel(time=1).plot()
plt.show()
