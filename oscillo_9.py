import paramiko
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import io
import numpy as np
from collections import deque

# Configuration SSH
host = "172.20.61.148"
#host = "192.168.0.47"
port = 22
username = "orangepi"
password = "MadeByBoris15AndJay3"
# file_path = "/media/actimetre/Project03/Actim0014-1A_2026-03-25_145446.csv"
file_path = "/media/actimetre/Project07/Actim0018-1A_2026-03-30_092446.csv"
num_lines = 150  # Nombre de lignes a recuperer a chaque fois

# Configuration graphique
interval_seconds = 0.100  # en secondes
fenetre_temps = 1  # Fenetre de temps affichee (en secondes)
max_points = 1000    # Nombre max de points stockes
t_start = 0.0

# Buffer pour stocker les donnees
buffer_x = deque(maxlen=max_points)
buffer_y1 = deque(maxlen=max_points)
buffer_y2 = deque(maxlen=max_points)


# Intervalle de temps entre chaque recuperation (en secondes)
interval_seconds = 0.1


def get_last_lines(ssh_client, file_path, num_lines):
    """Recupere les dernieres lignes d'un fichier via SSH."""
    stdin, stdout, stderr = ssh_client.exec_command(f'tail -n {num_lines} {file_path}')
    data = stdout.read().decode('utf-8')
    return io.StringIO(data)

def init():
    line1.set_data([], [])
    line2.set_data([], [])
    
    return line1, line2


def update(frame):
    data = get_last_lines(ssh_client, file_path, num_lines)
    if data is None:
        print('no data during update')
        return line1, line2
    # df = pd.read_csv(data, header=None,names=['date','time','Ax','Ay','Az','Gx','Gy','Gz'])
    df = pd.read_csv(data, header=None)
    # do not read the last line in case it was not fully written when transfered
    times = pd.to_timedelta(df.iloc[:-1,1]).dt.total_seconds()

    if len(times)>0:
        x = times - t_start[0]
        y1 = df.iloc[:-1,2]
        y2 = df.iloc[:-1,3]

        if len(x)>0:
            last_time = x.iloc[-1]
        else:
            last_time = 0.0

        # mise a jour des buffer
        buffer_x.append(x)
        buffer_y1.append(y1)
        buffer_y2.append(y2)

        mask = [xi >= last_time for xi in buffer_x]

        x_show = np.array(buffer_x)- last_time + fenetre_temps
        y1_show = np.array(buffer_y1)
        y2_show = np.array(buffer_y2)
        line1.set_data(x_show, y1_show)
        line2.set_data(x_show, y2_show)
        # On ne garde que les points dans la fenetre
        # ax.set_xlim(x_show[-1]-fenetre_temps, x_show[-1])

        # Attente avant la prochaine recuperation
        # time.sleep(interval_seconds/5)

    return line1, line2

# Initialisation du graphique
fig, ax = plt.subplots()
line1, = ax.plot([], [], 'b-', lw=1)
line2, = ax.plot([], [], 'r-', lw=1)
ax.set_xlim(0, fenetre_temps)
ax.set_ylim(-0.15, 0.15)
ax.set_xlabel("Temps (s)")
ax.set_ylabel("Accelerations (m.s-2)")
ax.set_title(f"Oscilloscope en temps reel (fenetre glissante de {fenetre_temps}s)")
ax.grid(True)
    
# Creation du client SSH
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(host, port=port, username=username, password=password)
print(f"Connecte a {host}")
# Get two lignes to extract t_start
data = get_last_lines(ssh_client, file_path, num_lines)
if data is None:
    print('No data')
df = pd.read_csv(data, header=None)
t_start = pd.to_timedelta(df.iloc[0:1,1]).dt.total_seconds()
    
try:
    # Update the plot (fetch data, redraw lines...)
    ani = FuncAnimation(fig, update, init_func=init, interval=interval_seconds, blit=True, cache_frame_data=False)
    plt.show()
        
except Exception as e:
    print(f"Erreur : {e}")

finally:
    # Fermeture de la connexion
    ssh_client.close()
    print("Connexion fermee.")
