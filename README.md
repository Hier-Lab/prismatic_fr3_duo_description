# Create the URDF model

Source the ROS environment and workspace has franka_description, then run:

```bash
python3 ./scripts/compile_urdf.py
```

After building and sourcing the workspace, the installed command is also available:

```bash
ros2 run prismatic_fr3_duo_description compile_urdf.py
```

The model parameters are in `config/prismatic_fr3_duo.yaml`. An alternate input,
output, or parameter file can be selected with command-line arguments:

```bash
./scripts/compile_urdf.py \
  --input urdf/prismatic_fr3_duo.urdf.xacro \
  --output /tmp/prismatic_fr3_duo.urdf \
  --config config/prismatic_fr3_duo.yaml
```

Run `./scripts/compile_urdf.py --help` for all options.

By default, compilation reduces every link to at most one cylinder and one
sphere collision. Links that use other geometry retain their first collision.
Use `--keep-all-collisions` when the complete upstream collision model is needed.

## Visualize the model

Build and source the workspace, then launch RViz with the joint-state slider GUI:

```bash
ros2 launch prismatic_fr3_duo_description visualize.launch.py
```

Use a different model parameter file with `config_file:=/path/to/config.yaml`.
