import cv2
import numpy as np

# Choose ArUco dictionary
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# Marker ID (you can change this: 0–49 for DICT_4X4_50)
marker_id = 0

# Size in pixels (bigger = easier for drone to detect)
marker_size = 500

# Generate marker image
marker_image = cv2.aruco.generateImageMarker(
    aruco_dict,
    marker_id,
    marker_size
)

# Save image
cv2.imwrite("aruco_marker_0.png", marker_image)

# Show it
cv2.imshow("ArUco Marker", marker_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
