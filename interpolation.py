import pyvista as pv
from pyvista import examples

# Download sample data
surface = examples.download_saddle_surface()
points = examples.download_sparse_points()

print(points.points)

p = pv.Plotter()
p.add_mesh(points, scalars="val", point_size=30.0, render_points_as_spheres=True)
p.add_mesh(surface)
p.show()


interpolated = surface.interpolate(points, radius=12.0)
p = pv.Plotter()
p.add_mesh(points, scalars="val", point_size=30.0, render_points_as_spheres=True)
p.add_mesh(interpolated, scalars="val")
p.show()