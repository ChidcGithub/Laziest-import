"""
3D Graphics Demo using laziest-import

This script demonstrates the symbol search feature by using
laziest-import to automatically discover and import 3D graphics libraries.
"""

# Use laziest-import for all imports
from laziest_import import *

print(help())
print("="*50)


# Enable symbol search with non-interactive mode for demo
enable_symbol_search(interactive=False)

# ===== Matplotlib 3D Demo =====
print("=" * 50)
print("3D Graphics Demo with laziest-import")
print("=" * 50)

# Create figure and 3D axes
fig = plt.figure(figsize=(12, 5))

# --- 3D Surface Plot ---
ax1 = fig.add_subplot(121, projection='3d')

# Create data for surface plot
x = np.linspace(-5, 5, 100)
y = np.linspace(-5, 5, 100)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

# Plot surface
surface = ax1.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
ax1.set_title('3D Surface: sin(sqrt(x² + y²))')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')
fig.colorbar(surface, ax=ax1, shrink=0.5, aspect=10)

# --- 3D Wireframe ---
ax2 = fig.add_subplot(122, projection='3d')

# Create wireframe data
theta = np.linspace(0, 2*np.pi, 30)
phi = np.linspace(0, np.pi, 30)
Theta, Phi = np.meshgrid(theta, phi)

# Sphere coordinates
R = 2
X_sphere = R * np.sin(Phi) * np.cos(Theta)
Y_sphere = R * np.sin(Phi) * np.sin(Theta)
Z_sphere = R * np.cos(Phi)

# Plot wireframe sphere
ax2.plot_wireframe(X_sphere, Y_sphere, Z_sphere, color='cyan', alpha=0.6)
ax2.set_title('3D Wireframe Sphere')
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_zlabel('Z')

# Adjust layout
plt.tight_layout()

print("\n✓ All imports handled by laziest-import:")
print(f"  - np (numpy)")
print(f"  - plt (matplotlib.pyplot)")
print()

# Show statistics
stats = get_import_stats()
print(f"Import Statistics:")
print(f"  - Total imports: {stats['total_imports']}")
print(f"  - Total time: {stats['total_time']*1000:.2f}ms")
print()

# Show loaded modules
loaded = list_loaded()
print(f"Loaded modules: {loaded}")

# Show the plot in a window
plt.show()
print("\n✓ Figure displayed in window")

print("\n✓ Demo completed successfully!")

