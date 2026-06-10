import cv2
import cv2.aruco as aruco

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Switch to 4x4_50 — fewer markers = larger Hamming distance = far fewer false positives
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)

    parameters = aruco.DetectorParameters()

    # More thorough thresholding sweep
    parameters.adaptiveThreshWinSizeMin = 3
    parameters.adaptiveThreshWinSizeMax = 23
    parameters.adaptiveThreshWinSizeStep = 4        # was 10 — check more window sizes

    # Marker geometry
    parameters.minMarkerPerimeterRate = 0.05
    parameters.maxMarkerPerimeterRate = 4.0
    parameters.polygonalApproxAccuracyRate = 0.05   # was 0.03 — more forgiving on corners

    # --- THE KEY FIXES ---
    parameters.errorCorrectionRate = 0.3            # was 0.6 — much stricter, reject ambiguous reads
    parameters.minCornerDistanceRate = 0.05
    parameters.minDistanceToBorder = 3

    # Glare/specular robustness
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX  # sub-pixel corner accuracy
    parameters.adaptiveThreshConstant = 7           # bias threshold darker to cut glare

    # Require a consistent read across the bit matrix
    parameters.minOtsuStdDev = 5.0                  # ignore near-uniform (washed out) regions

    print("Press 'q' to quit.")

    # Track last N detections for a simple majority-vote stabilizer
    from collections import deque, Counter
    history = deque(maxlen=5)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # For glare
        gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

        # Optional: mild CLAHE to normalize glare/shadow
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if ids is not None:
            history.append(int(ids.flatten()[0]))
        else:
            history.append(None)

        # Only report an ID if it appears in 3 of the last 5 frames
        stable_id = None
        if len(history) == 5:
            most_common, count = Counter(history).most_common(1)[0]
            if count >= 3 and most_common is not None:
                stable_id = most_common

        if stable_id is not None:
            aruco.drawDetectedMarkers(frame, corners, ids)
            cv2.putText(frame, f"Stable ID: {stable_id}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)
            print(f"Stable marker ID: {stable_id}")
        else:
            cv2.putText(frame, "No stable marker", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("ArUco Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
