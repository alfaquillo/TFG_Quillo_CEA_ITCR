import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as mpatches
grid = np.loadtxt("full_map_classes.csv", delimiter=",")



colors = [
    "#bfbfbf",  # 0 navegable
    "#ffff00",  # 1 crater
    "#ff0000",  # 2 roca
    "#00C8FF",  # 3 montaña
    "#00ff00",  # 4 cielo
    "#ff00ff",  # 254 trayectoria
    "#404040"   # 255 desconocido
]

cmap = ListedColormap(colors)
bounds = [0,1,2,3,4,5,255,256]
norm = BoundaryNorm(bounds, cmap.N)

plt.figure(figsize=(8,8))
plt.imshow(grid, cmap=cmap, norm=norm, interpolation="nearest")
legend_items = [
    mpatches.Patch(color="#bfbfbf", label="Navegable"),
    mpatches.Patch(color="#ffff00", label="Cráter"),
    mpatches.Patch(color="#ff0000", label="Roca"),
    mpatches.Patch(color="#00C8FF", label="Montaña"),
    mpatches.Patch(color="#00ff00", label="Cielo"),
    mpatches.Patch(color="#ff00ff", label="Trayectoria"),
    mpatches.Patch(color="#404040", label="Desconocido")
]

plt.legend(handles=legend_items,
           loc="center left",
           bbox_to_anchor=(1.02, 0.5),
           fontsize=13,
           markerscale=2.5,
           frameon=True)
plt.title("Mapa SLAM por clases")
#plt.colorbar()
plt.tight_layout()
plt.savefig("slam_debug_map.png", dpi=200, bbox_inches="tight")
plt.show()