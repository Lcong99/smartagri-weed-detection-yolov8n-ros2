#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------
# run_demo.sh
#   1) source ROS2
#   2) convert GLB → DAE (if needed)
#   3) copy data & maps into package
#   4) build package
#   5) launch RViz + 3 publishers
# ------------------------------------------------

# 1) ROS2 env
echo "[1] Sourcing ROS 2..."
source /opt/ros/humble/setup.bash

# 2) Paths
WS=~/ros2_ws
PKG=$WS/src/field_visualizer
DATA_SRC=/mnt/data
DATA_DST=$PKG/data
MAPS_DST=$PKG/maps
RVIZ_CONFIG=$PKG/launch/field_view.rviz

# 3) Ensure directories
echo "[2] Preparing folders..."
mkdir -p $DATA_DST $MAPS_DST

# 4) Copy CSVs
echo "[3] Copying CSV logs..."
cp $DATA_SRC/odom.csv        $DATA_DST/
cp $DATA_SRC/imu.csv         $DATA_DST/
cp $DATA_SRC/field_test_log.csv $DATA_DST/

# 5) Copy & convert GLB → DAE
if [ ! -f $MAPS_DST/field_map.dae ]; then
  echo "[4] Converting GLB → DAE..."
  cp $DATA_SRC/17_7_2025.glb $MAPS_DST/
  assimp export $MAPS_DST/17_7_2025.glb $MAPS_DST/field_map.dae
else
  echo "[4] DAE already exists, skipping conversion."
fi

# 6) Build
echo "[5] Building field_visualizer..."
cd $WS
colcon build --packages-select field_visualizer
source install/setup.bash

# 7) Launch
echo "[6] Starting RViz + publishers..."
# a) RViz
rviz2 -d $RVIZ_CONFIG &

# b) Publishers
for script in odom_publisher detection_marker_publisher heatmap_publisher; do
  python3 $PKG/field_visualizer/${script}.py &
done

echo "All set!  →  Check RViz for /odom, /weed_markers & /weed_heatmap."

